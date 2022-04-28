import collections
import datetime
import logging
import os
import re
import sqlite3
import sys
import textwrap
import time

import pandas
from packaging import version

if version.parse(pandas.__version__) < version.parse('1.3.0'):
    raise AssertionError('Pandas >= 1.3.0 required')

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Hoping that using a bunch of regular expressions will help with basic string
# processing speed.
INVEST_REGEX = re.compile('InVEST')
assert INVEST_REGEX.search('InVEST')
assert not INVEST_REGEX.search('iNvest')
assert not INVEST_REGEX.search('foo')

USERGUIDE_REGEX = re.compile('userguide')
assert USERGUIDE_REGEX.search('/userguide/index.html')
assert not USERGUIDE_REGEX.search('InVEST_Setup.exe')

EXTENSION_REGEX = re.compile('(exe)|(dmg)|(zip)|(whl)|(tar.gz)$')
assert EXTENSION_REGEX.search('InVEST_Setup.exe')
assert not EXTENSION_REGEX.search('index.html')

SAMPLEDATA_REGEX = re.compile('(_sample_data\.zip)|(/data/)')
assert SAMPLEDATA_REGEX.search('invest/3.10.2/InVEST_3.10.2_sample_data.zip$')
assert SAMPLEDATA_REGEX.search('invest/3.10.2/data/Base_Data.zip$')

EXT_MAP = {
    'whl': 'python',
    '.gz': 'python',
    'dmg': 'mac',
    'zip': 'mac',  # We distributed several InVEST mac builds as .zip
    'exe': 'windows',
}


def timestamp_to_date(microseconds_from_unix_epoch):
    # Date given in microseconds since the unix epoch
    # frometimestamp() takes seconds as a parameter, so we need to convert
    # microseconds to seconds.
    return datetime.datetime.fromtimestamp(
        int(microseconds_from_unix_epoch) / 1000000)


def count_from_one_file(source_filepath, target_filtered_csv_path):
    # See https://cloud.google.com/storage/docs/access-logs#format
    # for the CSV format
    start_time = time.time()
    table = pandas.read_csv(
        source_filepath,
        sep=',',
        engine='c',
        on_bad_lines='warn'  # some lines in CSV may be obviously malformed
    )
    LOGGER.info(
        f'{source_filepath} read in {round(time.time() - start_time)}s')

    valid_rows = []
    monthly_counts = collections.defaultdict(
        lambda: collections.defaultdict(int))

    n_files_unrecognized = 0
    start_time = time.time()
    for row_index, row in enumerate(table.itertuples()):
        elapsed_time = time.time() - start_time
        if elapsed_time >= 5.0:
            percent_complete = round(row_index / len(table.index), 2) * 100
            LOGGER.info(
                f'Locating downloads; {percent_complete}% complete')
            start_time = time.time()

        downloaded_file = row.cs_object
        if not isinstance(downloaded_file, str):
            # sometimes is nan
            # Based on the docs, this is probably when a listdir API call is
            # made
            continue

        if not INVEST_REGEX.search(downloaded_file):
            continue

        if not EXTENSION_REGEX.search(downloaded_file):
            continue

        if USERGUIDE_REGEX.search(downloaded_file):
            continue

        if SAMPLEDATA_REGEX.search(downloaded_file):
            continue

        # Logging records all requests, regardless of their HTTP status.
        # Reject any records with a 400 status code and anything with a 500
        # status code is an internal server error and should be skipped too.
        if 400 <= int(row.sc_status) < 600:
            continue

        date = timestamp_to_date(row.time_micros)
        month = date.strftime('%Y-%m')
        try:
            system = EXT_MAP[downloaded_file[-3:]]
        except KeyError:
            LOGGER.warning(
                f'Extension not recognized on {downloaded_file}, ignoring')
            n_files_unrecognized += 1
            continue

        monthly_counts[month][system] += 1
        row_dict = row._asdict()
        row_dict['ISO-8601-datetime'] = date.isoformat(sep=' ')
        valid_rows.append(row_dict)

    if n_files_unrecognized:
        n_rows = len(table.index)
        percent = round(n_files_unrecognized / n_rows, 6) * 100
        LOGGER.warning(
            f'{n_files_unrecognized} ({percent}%) files were unrecognized')
    LOGGER.info(f'Completed iteration over {source_filepath}')
    columns = ['ISO-8601-datetime'] + list(table.columns)

    # Dump the filtered results to CSV
    invest_downloads_df = pandas.DataFrame(data=valid_rows, columns=columns)
    invest_downloads_df.to_csv(target_filtered_csv_path, index=None)

    # Don't do this extra work for the workbench yet.
    if 'workbench' in target_filtered_csv_path:
        return monthly_counts

    # also dump the table to sqlite
    sqlite_path = os.path.splitext(target_filtered_csv_path)[0] + '.sqlite'
    conn = sqlite3.connect(sqlite_path)
    invest_downloads_df.to_sql(
        'invest', conn, if_exists='replace', index=False)
    conn.close()

    identify_uniqueish_downloads(
        sqlite_path, 'aggregated-invest-monthly-counts.csv')

    return monthly_counts


def write_dict_to_csv(monthly_counts_dict, target_filepath):
    monthly_counts = monthly_counts_dict

    dataframe = pandas.DataFrame.from_dict(
        monthly_counts,
        orient='index')
    dataframe["total"] = dataframe.sum(axis=1)
    dataframe = dataframe.sort_index()  # Fix a sorting issue in months
    dataframe.to_csv(target_filepath)


def identify_uniqueish_downloads(sqlite_path, target_csv):
    conn = sqlite3.connect(sqlite_path)

    # Assume that a unique download is one (useragent, referrer, object, ip
    # address, day, hour).  This will unfortunately aggregate a few extra
    # downloads, but should be pretty close.
    # TODO: figure out a better way to group clusters of HTTP:206 requests into
    # a single download.
    df = pandas.read_sql(
        textwrap.dedent(
            """\
            select month, count(*) from (
                select "ISO-8601-datetime",
                        substr("ISO-8601-datetime", 0, 8) as month,
                        substr("ISO-8601-datetime", 0, 11) as day,
                        substr("ISO-8601-datetime", 12, 2) as hour,
                        c_ip,
                        cs_object,
                        cs_user_agent,
                        sum(sc_bytes) as size from invest
                where cs_method == "GET"
                group by cs_user_agent, cs_referer, cs_object, c_ip, day, hour
                order by "ISO-8601-datetime" DESC
            )
            group by month
            order by month asc;
            """), conn)
    conn.close()

    df.to_csv(target_csv, index=False)


if __name__ == '__main__':
    source_csv_path = sys.argv[1]  # expected: usage-invest-workbench.csv
    dest_csv_path = source_csv_path.replace('usage-', 'monthly-')
    monthly_counts_dataframe = count_from_one_file(
        source_csv_path, source_csv_path.replace('usage-', 'filtered-'))
    write_dict_to_csv(monthly_counts_dataframe, dest_csv_path)

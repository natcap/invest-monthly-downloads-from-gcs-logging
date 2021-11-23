import collections
import datetime
import re
import sys
import time
import logging

import pandas

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Hoping that using a bunch of regular expressions will help with basic string
# processing speed.
INVEST_REGEX = re.compile('InVEST')
assert INVEST_REGEX.search('InVEST')
assert not INVEST_REGEX.search('foo')

USERGUIDE_REGEX = re.compile('userguide')
assert USERGUIDE_REGEX.search('/userguide/index.html')
assert not USERGUIDE_REGEX.search('InVEST_Setup.exe')

EXTENSION_REGEX = re.compile('(exe)|(dmg)|(zip)|(whl)|(tar.gz)$')
assert EXTENSION_REGEX.search('InVEST_Setup.exe')
assert not EXTENSION_REGEX.search('index.html')

EXT_MAP = {
    'whl': 'python',
    '.gz': 'python',
    'dmg': 'mac',
    'zip': 'mac',  # We distributed several InVEST mac builds as .zip
    'exe': 'windows',
}


def count_from_one_file(filepath):
    # See https://cloud.google.com/storage/docs/access-logs#format
    # for the CSV format
    start_time = time.time()
    table = pandas.read_csv(filepath, sep=',', engine='c')
    LOGGER.info(f'{filepath} read in {round(time.time() - start_time)}')

    monthly_counts = collections.defaultdict(
        lambda: collections.defaultdict(int))

    start_time = time.time()
    for row_index, row in enumerate(table.itertuples()):
        elapsed_time = time.time() - start_time
        if elapsed_time >= 5.0:
            percent_complete = round(row_index / len(table.index), 2)
            LOGGER.info(
                f'Locating downloads; {percent_complete}% complete')
            start_time = time.time()

        downloaded_file = row['cs_object']
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

        # Logging records all requests, regardless of their HTTP status.
        # Reject any records with a 400 status code and anything with a 500
        # status code is an internal server error and should be skipped too.
        if 400 <= int(row['sc_status']) < 600:
            continue

        # Date given in microseconds since the unix epoch
        # frometimestamp() takes seconds as a parameter, so we need to convert
        # microseconds to seconds.
        date = datetime.datetime.fromtimestamp(
            int(row['time_micros']) / 1000000)
        month = date.strftime('%Y-%m')
        system = EXT_MAP[downloaded_file[-3:]]
        monthly_counts[month][system] += 1

    LOGGER.info(f'Completed iteration over {filepath}')
    return monthly_counts


def write_dict_to_csv(monthly_counts_dict, target_filepath):
    monthly_counts = monthly_counts_dict

    dataframe = pandas.DataFrame.from_dict(
        monthly_counts,
        orient='index')
    dataframe["total"] = dataframe["windows"] + dataframe["mac"]
    dataframe = dataframe.sort_index()  # Fix a sorting issue in months
    dataframe.to_csv(target_filepath)


if __name__ == '__main__':
    source_csv_path = sys.argv[1]  # expected: usage-invest-workbench.csv
    dest_csv_path = source_csv_path.replace('usage-', 'monthly-')
    write_dict_to_csv(
        count_from_one_file(source_csv_path),
        dest_csv_path)

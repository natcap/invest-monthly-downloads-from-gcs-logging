import collections
import datetime
import glob
import pprint
import re
import time

import pandas

# Hoping that using a bunch of regular expressions will help with basic string
# processing speed.
INVEST_REGEX = re.compile('InVEST')
assert INVEST_REGEX.search('InVEST')
assert not INVEST_REGEX.search('foo')

USERGUIDE_REGEX = re.compile('userguide')
assert USERGUIDE_REGEX.search('/userguide/index.html')
assert not USERGUIDE_REGEX.search('InVEST_Setup.exe')

EXTENSION_REGEX = re.compile('(exe)|(dmg)|(zip)$')
assert EXTENSION_REGEX.search('InVEST_Setup.exe')
assert not EXTENSION_REGEX.search('index.html')


def count():
    monthly_counts = collections.defaultdict(int)
    last_time = time.time()
    n_files_touched = 0
    n_files_touched_last_time = 0

    summary_file = open('summary.txt', 'w')
    start_time = time.time()

    file_list = glob.glob(
        'logging/releases.naturalcapitalproject.org/_usage*')

    n_files = len(file_list)

    for usage_file in file_list:
        n_files_touched += 1
        if time.time() - last_time > 5.0:
            elapsed = round(time.time() - start_time, 2)
            files_per_second = round(
                n_files_touched_last_time / elapsed, 2)

            print(
                f'{n_files_touched} so far; {elapsed}s elapsed '
                f'{files_per_second} files/second '
                f'{n_files - n_files_touched} remaining')
            last_time = time.time()
            n_files_touched_last_time = n_files_touched

        table = pandas.read_csv(usage_file, sep=',', engine='c')

        year_month_day = re.findall('[0-9]{4}_[0-9]+_[0-9]+', usage_file)[0]
        date = datetime.date(*[int(s) for s in year_month_day.split('_')])

        for index, row in table.iterrows():
            downloaded_file = row['cs_object']
            if not isinstance(downloaded_file, str):
                # sometimes is nan
                continue

            if not INVEST_REGEX.search(downloaded_file):
                continue

            if not EXTENSION_REGEX.search(downloaded_file):
                continue

            if not USERGUIDE_REGEX.search(downloaded_file):
                continue

            monthly_counts[f'{date.year}-{date.month}'] += 1
            summary_file.write(
                f'{date.year}-{date.month}-{date.day},{downloaded_file}\n')

    summary_file.close()
    pprint.pprint(dict(monthly_counts))


if __name__ == '__main__':
    count()

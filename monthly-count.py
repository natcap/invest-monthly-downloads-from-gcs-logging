import collections
import datetime
import glob
import pprint
import re
import time

import pandas


def count():
    monthly_counts = collections.defaultdict(int)
    last_time = time.time()
    n_files_touched = 0

    summary_file = open('summary.txt', 'w')
    for usage_file in glob.glob(
            'logging/releases.naturalcapitalproject.org/_usage*'):
        n_files_touched += 1
        if time.time() - last_time > 5.0:
            print(f'{n_files_touched} so far')
            last_time = time.time()

        table = pandas.read_csv(usage_file, sep=None, engine='python')

        year_month_day = re.findall('[0-9]{4}_[0-9]+_[0-9]+', usage_file)[0]
        date = datetime.date(*[int(s) for s in year_month_day.split('_')])

        for index, row in table.iterrows():
            downloaded_file = row['cs_object']
            if not isinstance(downloaded_file, str):
                # sometimes is nan
                continue

            if ('InVEST' in downloaded_file and
                    downloaded_file.endswith(('.exe', '.dmg', '.zip')) and
                    'userguide' not in downloaded_file):
                monthly_counts[f'{date.year}-{date.month}'] += 1
                summary_file.write(
                    f'{date.year}-{date.month}-{date.day},{downloaded_file}\n')

    summary_file.close()
    pprint.pprint(dict(monthly_counts))


if __name__ == '__main__':
    count()

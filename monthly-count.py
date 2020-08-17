import collections
import datetime
import glob
import pprint
import re

import pandas


def count():
    monthly_counts = collections.defaultdict(int)
    for usage_file in glob.glob(
            'logging/releases.naturalcapitalproject.org/_usage*'):
        table = pandas.read_csv(usage_file)

        year_month_day = re.findall('[0-9]{4}_[0-9]+_[0-9]+', usage_file)
        date = datetime.date(*year_month_day.split('_'))

        for row in table.iterrows():
            downloaded_file = row['cs_object']
            if ('InVEST' in downloaded_file and
                    downloaded_file.endswith(('.exe', '.dmg', '.zip'))):
                print(downloaded_file)
                monthly_counts[f'{date.year}-{date.month}'] += 1

    pprint.pprint(monthly_counts)

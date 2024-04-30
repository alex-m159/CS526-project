import csv
import sys

def main():
    with open(sys.argv[1], 'r') as fr:
        fieldnames = [
            'measure_id',
            'measure_name',
            'location_id',
            'location_name',
            'fips',
            'race_id',
            'race_name',
            'sex_id',
            'sex_name',
            'age_group_id',
            'age_name',
            'year',
            'metric_id',
            'metric_name',
            'val',
            'upper',
            'lower',
        ]
        reader = csv.DictReader(fr)

        with open(f'{sys.argv[1]}.processed', 'w') as fw:
            writer = csv.DictWriter(fw, ['ROWNUM', 'STATE_FIPS', 'STATE_COUNTY_FIPS', 'LIFE_EXPECTANCY', 'YEAR'])
            rows = []
            for (i, rrow) in enumerate(reader):
                if rrow['location_name'] == 'United States of America':
                    continue
                if rrow['race_name'] != 'Total':
                    continue
                if rrow['sex_name'] != 'Both':
                    continue
                if rrow['age_name'] != '<1 year':
                    continue

                rows.append({
                    'ROWNUM': i,
                    'STATE_FIPS': int(rrow['fips'])//1000 if int(rrow['fips']) > 1000 else int(rrow['fips']),
                    'STATE_COUNTY_FIPS': None if int(rrow['fips']) < 1000 else int(rrow['fips']),
                    'LIFE_EXPECTANCY': rrow['val'],
                    'YEAR': int(rrow['year'])
                })

            writer.writerows(rows)
            


if __name__ == "__main__":

    main()
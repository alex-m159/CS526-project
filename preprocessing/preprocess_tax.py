import csv

def main():
    with open('../data/15incyallagi.csv', 'r') as fr:
        with open('../data/taxes-paid-by-county-2015.csv', 'w') as fw:
            reader = csv.DictReader(fr)
            newrows = []
            skipped = 0
            for (i, row) in enumerate(reader):
                if int(float(row['N1'])) == 0:
                    skipped += 1
                    # A county with "zero" returns is possible in this dataset since
                    # the data is processed to group tax returns from counties with < 20 returns into a neighboring county
                    # to preserve privacy, so just skip them since it should only be an issue for a small proportion of counties.
                    # Only happens to 253 counties so < 1% of counties
                    continue
                newrows.append([
                    i,                                                                  # ROWNUM                    UInt32 PRIMARY KEY,
                    2015,                                                               # TAX_YEAR                  UInt16,
                    row['STATEFIPS'],                                                   # STATEFIPS                 UInt32,
                    row['STATE'],                                                       # STATE_ABBREV              String,
                    ''.join([row['STATEFIPS'], row['COUNTYFIPS']]),                     # COUNTYFIP                 UInt32,
                    row['COUNTYNAME'],                                                  # COUNTY_NAME               String,
                    row['agi_stub'],                                                    # AGI_STUB                  UInt8,
                    int(float(row['N1'])),                                              # NUM_RETURNS               UInt32,       -- N1
                    1000 * int(float(row['A00100'])),                                   # ADJUSTED_GROSS_INCOME     UInt64,       -- A00100
                    1000 * int(float(row['A18300'])),                                   # TAXES_PAID_AMOUNT         UInt64,       -- A18300
                    1000 * int(float(row['A10600'])),                                   # TOTAL_TAX_PAYMENTS_AMOUNT UInt64        -- A10600
                    int((1000 * int(float(row['A00100']))) / int(float(row['N1']))),         # AVG_AGI_PER_FILER         Int32        -- A00100 / N1 
                    int((1000 * int(float(row['A18300']))) / int(float(row['N1']))),           # AVG_TAXES_PER_FILER       Int32        -- A18300 / N1                          
                ])
        
            writer = csv.writer(fw)
            writer.writerows(newrows)
            print(f'skipped: {skipped}')
if __name__ == "__main__":
    main()
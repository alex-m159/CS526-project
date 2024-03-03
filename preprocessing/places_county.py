import csv
import re


def main():
    with open('../data/PLACES_County_2023.csv', 'r') as fr:
        with open('../data/PLACES_County_2023_Preprocessed.csv', 'w') as fw:
            reader = csv.DictReader(fr)
            newrows = []
            writer = csv.writer(fw, quoting=csv.QUOTE_NONE, delimiter='\t', lineterminator='')
            footnote_symbolA = 0
            footnote_symbolB = 0.0
            row_fsA = None
            row_fsB = None
            high_confA = 0
            high_confB = 0.0
            row_hcA = None
            row_hcB = None
            low_confA = 0
            low_confB = 0.0
            row_lcA = None
            row_lcB = None

            for (i, row) in enumerate(reader):
                fs = row['Data_Value']
                hc = row['High_Confidence_Limit']
                lc = row['Low_Confidence_Limit']
                geo = row['Geolocation']
                match = re.match('POINT \((-?[0-9]+\.[0-9]+) (-?[0-9]+\.[0-9]+)\)', geo)
                # import pdb;pdb.set_trace()
                
                # if not match:
                #     import pdb;pdb.set_trace()
                
                row = [
                    str(i),                                                                           # ROWNUM                      UInt32 PRIMARY KEY
                    str(row['Year']),                                                                 # YEAR                        UInt16
                    str(row['StateAbbr']),                                                            # STATE_ABBREV                String
                    str(row['StateDesc']),                                                            # STATE_NAME                  String
                    str(row['LocationName']),                                                         # COUNTY_NAME                 String
                    str(row['DataSource']),                                                           # DATASOURCE                  String
                    str(row['Category']),                                                             # CATEGORY                    String
                    str(row['Measure']),                                                              # MEASURE                     String
                    str(row['Data_Value_Unit']),                                                      # DATA_VALUE_UNIT             String
                    str(row['Data_Value_Type']),                                                      # DATA_VALUE_TYPE             String
                    str(row['Data_Value']),                                                           # DATA_VALUE                  Decimal(3, 1)
                    str(row['Data_Value_Footnote_Symbol']),                                           # DATA_VALUE_FOOTNOTE_SYMBOL  Nullable(String)
                    str(row['Data_Value_Footnote']),                                                  # DATA_VALUE_FOOTNOTE         Nullable(String)
                    str(row['Low_Confidence_Limit']),                                                 # LOW_CONFIDENCE_LIMIT        Decimal(3, 1)
                    str(row['High_Confidence_Limit']),                                                # HIGH_CONFIDENCE_LIMIT       Decimal(3, 1)
                    str(row['TotalPopulation']),                                                      # TOTAL_POPULATION            UInt32
                    str(int(row['LocationID'])),                                                           # COUNTY_FIPS                 UInt32
                    str(row['CategoryID']),                                                           # CATEGORY_ID                 String
                    str(row['MeasureId']),                                                            # MEASURE_ID                  String
                    str(row['DataValueTypeID']),                                                      # DATA_VALUE_TYPE_ID          String
                    str(row['Short_Question_Text']),                                                  # SHORT_QUESTION_TEXT         String
                               # GEOLOCATION                 Point
                ]
                writer.writerow(row)
                fw.write(f"\t({match.group(1)}, {match.group(2)})\n" if match else f'\t(0, 0)\n')
                
                

if __name__ == "__main__":
    main()
"""
Author: Alex Markley
This is a quick script to preprocess data that was extracted from IPUMS.

When exported via R to a CSV, the data will keep the IPUMS numeric encodings 
for the columns. However, having the human-readable string values obviously makes
data exploration much easier, so this file will merge the string values into a new
column with the prefix "_NAME" for all the columns that are encoded values.
"""
import csv


def main():

    WO_NAMES = "../data/cps_00004_header.csv"
    W_NAMES = "../data/cps_00004_named.csv"
    MERGED = "../data/cps_00004_merged.csv"
    headers = [
        'ROWNUM',
        'YEAR',
        'SERIAL',
        'MONTH',
        'CPSID',
        'ASECFLAG',
        'HFLAG',
        'ASECWTH',
        'STATEFIP',
        'STATECENSUS',
        'COUNTY',
        'METFIPS',
        'METAREA',
        'METRO',
        'INDIVIDCC',
        'PERNUM',
        'CPSIDV',
        'CPSIDP',
        'ASECWT',
        'EDUC',
        'HIGRADE',
        'FTOTVAL',
        'INCTOT',
        'ADJGINC',
        'FEDTAX',
        'FEDTAXAC',
        'MARGTAX',
        'STATETAX',
        'STATAXAC',
        'TAXINC'
    ]
    named_headers = [
        'ROWNUM',
        'YEAR',
        'SERIAL',
        'MONTH',
        'MONTH_NAME',
        'CPSID',
        'ASECFLAG',
        'HFLAG',
        'ASECWTH',
        'STATEFIP',
        'STATEFIP_NAME',
        'STATECENSUS',
        'COUNTY',
        'METFIPS',
        'METAREA',
        'METAREA_NAME',
        'METRO',
        'METRO_NAME',
        'INDIVIDCC',
        'PERNUM',
        'CPSIDV',
        'CPSIDP',
        'ASECWT',
        'EDUC',
        'EDUC_NAME',
        'HIGRADE',
        'HIGRADE_NAME',
        'FTOTVAL',
        'INCTOT',
        'ADJGINC',
        'FEDTAX',
        'FEDTAXAC',
        'MARGTAX',
        'STATETAX',
        'STATAXAC',
        'TAXINC'
    ]
    with open(WO_NAMES, 'r', 2**25) as wof:
        with open(W_NAMES, 'r', 2**25) as wf:
            with open(MERGED, 'w', 2**25) as mf:
                wo_reader = csv.DictReader(wof)
                w_reader = csv.DictReader(wf)
                m_writer = csv.DictWriter(mf, fieldnames=named_headers)
                for (wo_row, w_row) in zip(wo_reader, w_reader):
                    # import pdb;pdb.set_trace()
                    m_row = {
                        'ROWNUM': wo_row[''],
                        'YEAR': wo_row['YEAR'],
                        'SERIAL': wo_row['SERIAL'],
                        'MONTH': wo_row['MONTH'],
                        'MONTH_NAME': w_row['month'],
                        'CPSID': wo_row['CPSID'],
                        'ASECFLAG': wo_row['ASECFLAG'],
                        'HFLAG': wo_row['HFLAG'],
                        'ASECWTH': wo_row['ASECWTH'],
                        'STATEFIP': wo_row['STATEFIP'],
                        'STATEFIP_NAME': wo_row['STATEFIP'],
                        'STATECENSUS': wo_row['STATECENSUS'],
                        'COUNTY': wo_row['COUNTY'],
                        'METFIPS': wo_row['METFIPS'],
                        'METAREA': wo_row['METAREA'],
                        'METAREA_NAME': w_row['metarea'],
                        'METRO': wo_row['METRO'],
                        'METRO_NAME': w_row['metro'],
                        'INDIVIDCC': wo_row['INDIVIDCC'],
                        'PERNUM': wo_row['PERNUM'],
                        'CPSIDV': wo_row['CPSIDV'],
                        'CPSIDP': wo_row['CPSIDP'],
                        'ASECWT': wo_row['ASECWT'],
                        'EDUC': wo_row['EDUC'],
                        'EDUC_NAME': w_row['educ'],
                        'HIGRADE': wo_row['HIGRADE'],
                        'HIGRADE_NAME': w_row['higrade'],
                        'FTOTVAL': wo_row['FTOTVAL'],
                        'INCTOT': wo_row['INCTOT'],
                        'ADJGINC': wo_row['ADJGINC'],
                        'FEDTAX': wo_row['FEDTAX'],
                        'FEDTAXAC': wo_row['FEDTAXAC'],
                        'MARGTAX': wo_row['MARGTAX'],
                        'STATETAX': wo_row['STATETAX'],
                        'STATAXAC': wo_row['STATAXAC'],
                        'TAXINC': wo_row['TAXINC'],
                    }  

                    m_writer.writerow(m_row)
    print("done.")



if __name__ == "__main__":
    main()
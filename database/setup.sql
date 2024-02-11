CREATE DATABASE cps_00004;

USE cps_00004;

CREATE TABLE cps_00004 (
        ROWNUM              UInt32 PRIMARY KEY,
        YEAR                UInt16,
        SERIAL              UInt64,
        MONTH               Nullable(UInt8),
        MONTH_NAME          Nullable(String),
        CPSID               Nullable(UInt64),
        ASECFLAG            Nullable(UInt8),
        HFLAG               Nullable(UInt8),
        ASECWTH             Nullable(Decimal(10, 4)),
        STATEFIP            UInt8,
        STATEFIP_NAME       String,
        STATECENSUS         Nullable(UInt8),
        COUNTY              Nullable(UInt32),
        METFIPS             UInt32,
        METAREA             UInt16,
        METAREA_NAME        String,
        METRO               UInt8,
        METRO_NAME          String,
        INDIVIDCC           Nullable(UInt8),
        PERNUM              UInt8,
        CPSIDV              Nullable(UInt64),
        CPSIDP              Nullable(UInt64),
        ASECWT              Nullable(Decimal(10, 4)),
        EDUC                UInt16,
        EDUC_NAME           String,
        HIGRADE             UInt16,
        HIGRADE_NAME        String,
        FTOTVAL             Nullable(Int64),
        INCTOT              Int64,
        ADJGINC             Nullable(Int64),
        FEDTAX              Nullable(Int64),
        FEDTAXAC            Nullable(Int64),
        MARGTAX             Nullable(UInt8),
        STATETAX            Nullable(Int64),
        STATAXAC            Nullable(Int64),
        TAXINC              Nullable(Int32)
    ) ENGINE = MergeTree();


-- Clickhouse doesn't support SQL script files with multiple statements
-- so to run this code and load in the CSV file, it's recommended to 
-- run:
--  $ clickhouse client --query="<copy below SQL statement>" < cps_00004.csv
--
-- You'll also have to ensure that you have proper permissions in Clickhouse for
-- the above command to work.
INSERT INTO cps_00004.cps_00004 (ROWNUM, YEAR, SERIAL, MONTH, MONTH_NAME, CPSID, ASECFLAG, HFLAG, ASECWTH, STATEFIP, STATEFIP_NAME, STATECENSUS, COUNTY, METFIPS, METAREA, METAREA_NAME, METRO, METRO_NAME, INDIVIDCC, PERNUM, CPSIDV, CPSIDP, ASECWT, EDUC, EDUC_NAME, HIGRADE, HIGRADE_NAME, FTOTVAL, INCTOT, ADJGINC, FEDTAX, FEDTAXAC, MARGTAX, STATETAX, STATAXAC, TAXINC ) FORMAT CSV 


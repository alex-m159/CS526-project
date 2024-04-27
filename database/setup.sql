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


CREATE TABLE rural_urban_codes (
    FIPS                    UInt64 PRIMARY KEY,
    STATE_ABBREV            String,
    COUNTY_NAME             String,
    POP                     UInt32,
    RUCC                    UInt8,
    DESCR                   String
) ENGINE = MergeTree();


CREATE TABLE life_expectancy (
    ROWNUM                    UInt32 PRIMARY KEY,
    STATE_FIPS                UInt32,
    STATE_COUNTY_FIPS         Nullable(UInt32),
    LIFE_EXPECTANCY           Decimal(3, 1),
    YEAR                      UInt32
) ENGINE = MergeTree();


CREATE TABLE income_tax (
    ROWNUM                    UInt32 PRIMARY KEY,
    TAX_YEAR                  UInt16,
    STATEFIPS                 UInt32,
    STATE_ABBREV              String,
    COUNTYFIP                 UInt32,
    COUNTY_NAME               String,
    AGI_STUB                  UInt8,
    NUM_RETURNS               UInt64,       -- N1
    ADJUSTED_GROSS_INCOME     Int64,        -- A00100
    TAXES_PAID_AMOUNT         Int64,        -- A18300
    TOTAL_TAX_PAYMENTS_AMOUNT Int64,        -- A10600
    AVG_AGI_PER_FILER         Int64,        -- A00100 / N1
    AVG_TAXES_PER_FILER       Int64         -- A18300 / N1
) ENGINE = MergeTree();

-- Year,StateAbbr,StateDesc,LocationName,DataSource,Category,Measure,Data_Value_Unit,Data_Value_Type,Data_Value,Data_Value_Footnote_Symbol,Data_Value_Footnote,Low_Confidence_Limit,High_Confidence_Limit,TotalPopulation,LocationID,CategoryID,MeasureId,DataValueTypeID,Short_Question_Text,Geolocation
-- 2021,GA,Georgia,Ware,BRFSS,Health Outcomes,Stroke among adults aged >=18 years,%,Crude prevalence,4.6,,,4.0,5.1,36033,13299,HLTHOUT,STROKE,CrdPrv,Stroke,POINT (-82.4215072 31.050881)

CREATE TABLE places_county (
    ROWNUM                      UInt32 PRIMARY KEY,
    YEAR                        UInt16,
    STATE_ABBREV                String,
    STATE_NAME                  String,
    COUNTY_NAME                 String,
    DATASOURCE                  String,
    CATEGORY                    String,
    MEASURE                     String,
    DATA_VALUE_UNIT             String,
    DATA_VALUE_TYPE             String,
    DATA_VALUE                  DOUBLE,
    DATA_VALUE_FOOTNOTE_SYMBOL  Nullable(String),
    DATA_VALUE_FOOTNOTE         Nullable(String),
    LOW_CONFIDENCE_LIMIT        Decimal(3, 1),
    HIGH_CONFIDENCE_LIMIT       Decimal(3, 1),
    TOTAL_POPULATION            UInt32,
    COUNTY_FIPS                 UInt32,
    CATEGORY_ID                 String,
    MEASURE_ID                  String,
    DATA_VALUE_TYPE_ID          String,
    SHORT_QUESTION_TEXT         String,
    GEOLOCATION                 Point
) ENGINE = MergeTree();

CREATE TABLE premature_deaths (
    ROWNUM                      UInt32 PRIMARY KEY,
    STATE_FIPS                  UInt32,
    STATE_NAME                  String,
    YEAR_COLLECTED              UInt16,
    YEARS_LOST_PER_100K         UInt32,
)

CREATE TABLE public_health_spending (
    ROWNUM                      UInt32 PRIMARY KEY,
    STATE_FIPS                  UInt32,
    STATE_NAME                  String,
    YEAR_COLLECTED              UInt16,
    DOLLARS_PER_CAPITA          UInt32,
)

CREATE TABLE preventable_hospitalizations (
    ROWNUM                      UInt32 PRIMARY KEY,
    STATE_FIPS                  UInt32,
    STATE_NAME                  String,
    YEAR_COLLECTED              UInt16,
    HOSPITALIZATIONS_PER_100K   UInt32,
)

CREATE TABLE state_regions (
    STATE_FIPS UInt32 PRIMARY KEY,
    STATE_NAME String,
    STATE_ABBREV String,
    DIVISION String,
    REGION String
) ENGINE = MergeTree();

CREATE TABLE state_fips (
    STATE_FIPS UInt32 PRIMARY KEY,
    STATE_NAME String
) ENGINE = MergeTree();

CREATE TABLE county_fips (
    STATE_COUNTY_FIPS UInt64 PRIMARY KEY,
    COUNTY_FIPS UInt32,
    COUNTY_NAME String,
    STATE_FIPS  UInt32,
    STATE_NAME  String,
    GEO         String
) ENGINE = MergeTree();

CREATE TABLE county_gini (
    STATE_COUNTY_FIPS UInt64 PRIMARY KEY,
    GINI DOUBLE
) ENGINE = MergeTree();

CREATE TABLE neighboring_counties (
    ROWNUM Int64 PRIMARY KEY,
    STATE_COUNTY_FIPS_left UInt64,
    GINI_left DOUBLE,
    AVG_AGI_left Decimal(10, 3),
    STATE_COUNTY_FIPS_right UInt64,
    GINI_right DOUBLE,
    AVG_AGI_right Decimal(10, 3)
) ENGINE = MergeTree();


CREATE TABLE pop_weighted_rucc (
    STATE_FIPS UInt32 PRIMARY KEY,
    WEIGHTED_RUCC DOUBLE
) ENGINE = MergeTree();

-- Clickhouse doesn't support SQL script files with multiple statements
-- so to run this code and load in the CSV file, it's recommended to 
-- run:
--  $ clickhouse client --query="<copy below SQL statement>" < cps_00004_merged.csv
--
-- You'll also have to ensure that you have proper permissions in Clickhouse for
-- the above command to work.
INSERT INTO cps_00004.cps_00004 (ROWNUM, YEAR, SERIAL, MONTH, MONTH_NAME, CPSID, ASECFLAG, HFLAG, ASECWTH, STATEFIP, STATEFIP_NAME, STATECENSUS, COUNTY, METFIPS, METAREA, METAREA_NAME, METRO, METRO_NAME, INDIVIDCC, PERNUM, CPSIDV, CPSIDP, ASECWT, EDUC, EDUC_NAME, HIGRADE, HIGRADE_NAME, FTOTVAL, INCTOT, ADJGINC, FEDTAX, FEDTAXAC, MARGTAX, STATETAX, STATAXAC, TAXINC ) FORMAT CSV 

INSERT INTO cps_00004.rural_urban_codes (FIPS, STATE_ABBREV, COUNTY_NAME, POP, RUCC, DESCR) FORMAT CSV

INSERT INTO cps_00004.life_expectancy ( ROWNUM, STATE_NAME, COUNTY, CENSUS_TRACT_NUMBER, LIFE_EXPECTANCY, LIFE_EXPECTANCY_RANGE, LIFE_EXPECTANCY_STD_ERR ) FORMAT CSV 

INSERT INTO cps_00004.state_regions (STATE_FIPS, STATE_NAME, STATE_ABBREV, DIVISION, REGION ) FORMAT CSV 






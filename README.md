# [CS 526] Data Visualization Project
This project is focused on creating interactive visualizations using public health, education, and income datasets.

## Datasources
IPUMS Datasets:
https://cps.ipums.org/cps/index.shtml
https://usa.ipums.org/usa/

Suicide:
https://catalog.data.gov/dataset/death-rates-for-suicide-by-sex-race-hispanic-origin-and-age-united-states-020c1

Alzhiemer's and Aging:
https://catalog.data.gov/dataset/alzheimers-disease-and-healthy-aging-data

Leading Causes of Death:
https://catalog.data.gov/dataset/nchs-leading-causes-of-death-united-states

Life Expectency:
https://catalog.data.gov/dataset/nchs-death-rates-and-life-expectancy-at-birth

Human Well-Being Index:
https://catalog.data.gov/dataset/human-well-being-index-hwbi-for-u-s-counties-2000-20101

Behavioral Cardiovascular Risk Factor:
https://catalog.data.gov/dataset/behavioral-risk-factor-surveillance-system-brfss-national-cardiovascular-disease-surveilla

Hospital Provider Cost Report:
https://catalog.data.gov/dataset/hospital-provider-cost-report

Epidemiology Survey:
https://catalog.data.gov/dataset/500-cities-city-level-data-gis-friendly-format-2019-release

Rural-Urban Area Codes (Rural Areas based on Census Tract):
https://catalog.data.gov/dataset/rural-urban-commuting-area-codes

Rural-Urban Continuum Codes:
https://catalog.data.gov/dataset/rural-urban-continuum-codes

Income Tax:
https://www.irs.gov/statistics/soi-tax-stats-county-data



## Limitations
The NHIS source dataset does NOT offer publicly available data that have geographic information at granularity smaller than region of the US (Northeast, Midwest, etc.), so evaluations that relate a specific city/county with health outcomes are impossible with that dataset.

## Questions to Answer
1. We know that income and health/life expectancy are correlated. Where does that correlation plateau? Are there diminishing returns?
  Data required (per row):
  ```
  individual income
  income percentile within location
  income percentile nationally
  location (county/census tract)
  life expectancy
  health outcomes
  ```

  Combine IPUMS USA income data at county level with census tract/county data on life expectancy.
  

2. Is it better to be poor in a rich area or rich in a poor area? What are the limits of this effect?

  Big geographic map showing the health disparities between the bottom x% and the top y%

  Data required (per row):
  ```
  individual income
  income percentile within location
  income percentile nationally
  location (county/census tract)
  life expectancy
  health outcomes
  ```
  * join on location
  * group by income percentile
  * average life expectancy and health outcomes

3. Controlling for income, does being close to a densely populated area improve/decrease life expectancy or health?

  Data required (per row):
  ```
  individual income
  income percentile within location (metroarea)
  metroarea
  life expectancy
  health outcomes
  ```
  * join on metroarea


4. Are taxation rates related to health outcomes? Is high tax revenue correlated with increased health expenditures? Are increased health expenditures correlated with increased health outcomes?
  geographic map with range selection for taxation rate/tax per capita and a selection for health quality metrics (rate of cancer/disease/life expectancy)
  Possibly double map for comparison or some kind.

  Data required (per row):
  ```
  tax revenue collected
  population
  effective tax rate
  income/earnings
  location (county/census tract)
  ```
  * join on location

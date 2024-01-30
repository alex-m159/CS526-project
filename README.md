# [CS 526] Data Visualization Project
This project is focused on creating interactive visualizations using public health, education, and income datasets.

## Datasources
IPUMS Datasets:
https://cps.ipums.org/cps/index.shtml
https://usa.ipums.org/usa/

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

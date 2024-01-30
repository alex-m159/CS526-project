* 
* 
* This STATA command do-file will 
* load in the given datafile and then export 
* it as a CSV, and then will export a partial
* as well for easy viewing in Excel. 
* 
* 

* Change this to match the actual path
cd "C:\Users\adm146\Downloads"

* You need to download this from the IPUMS site,
* the same page you download the data from
do "C:\Users\adm146\Downloads\cps_00004.do"

* Not necessary, but this installs a utility that helps
* with printing/debugging if needed
ssc install listfirst
export delimited using cps_00004.csv

* Filter out records without federal tax and taxable income
frame put if !missing(fedtax) & !missing(taxinc), into(partial)
frame change partial
export delimited using cps_00004_partial.csv

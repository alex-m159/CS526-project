# [CS 526] Data Visualization Project
Group 3: 

Amari Urquhart, Jennifer Xin, Alex Markley

This project is focused on creating interactive visualizations using public health and income datasets.
Live Link: http://45.79.137.151:5175/

## Datasources
IPUMS Datasets (Tax, Income, Location):
https://cps.ipums.org/cps/index.shtml
https://usa.ipums.org/usa/

Life Expectency:
https://catalog.data.gov/dataset/nchs-death-rates-and-life-expectancy-at-birth

Rural-Urban Area Codes (Rural Areas based on Census Tract):
https://catalog.data.gov/dataset/rural-urban-commuting-area-codes

Rural-Urban Continuum Codes:
https://catalog.data.gov/dataset/rural-urban-continuum-codes

Income Tax:
https://www.irs.gov/statistics/soi-tax-stats-county-data

## Data Samples
The `data_samples` folder contains a small sample of our datasets. Ten rows from each. The files are named after the corresponding table name, please refer to the `database/schema.sql` file for the original schema they were taken from.

## Installation

### Clickhouse Database
We made use of Clickhouse's provided Docker Image.
The full configuration can be found in `ops/Dockerfile.database` and `ops/docker-compose.yaml`.
Note that in `docker-compose.yaml` the image is pulled from a self-hosted docker registry. 
You can change this to use your own registry or to use DockerHub, and change the volume mounts as needed to match your local directory structure.

Once the Clickhouse container is running you'll need to create the tables and load the data into those tables.
The `database/setup.sql` file contains the table creation statements and there is a helper script `data/load-data.sh` that provides shell commands to load the data into 
Clickhouse, assuming it's in the appropriate format.

### Data Loading

We used several datasources, many of which require preprocessing before loading, and we created pre-computed tables as well.
Datasources are linked above, preprocessing Python scripts are located in `preprocessing/`, and pre-computed tables were generated in Jupyter notebooks and loaded into the database.

To populate the database, you must download all the files from the above linked sources. IPUMS CPS requires an account to access the dataset and you must then select 
the variables that match the variables shown in `cps_00004.cps_00004` table definition in `database/schema.sql`. Data for all available sample years should be downloaded.
After doing this you should load the data in STATA and augment the data with additional columns that contain the string equivalents for any fields that rely on a numerical code for a categorical encoding. You should then export this as a single CSV file. This can be uploaded into Clickhouse.

The other data files come from either the links above or the Jupyter notebooks in `web/src/alex`, `web/src/jen`, `web/src/amari`.
Once the raw data files are gathered, you should run the scripts in `preprocessing/` to ensure that the datasets are prepared for the Clickhouse schema.


Finally you can run the `data/load-data.sh` script from within the Clickhouse database container (or outside the container if you opted to install Clickhouse directly).
If the data is in the correct format and the tables are created, then the script will run to completion, otherwise errors will be reported.

### Python

```bash
cd web/src
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  
```

To run:

```bash
cd web/src/
gunicorn pubhealth.pubhealth:app -k eventlet -w 2 -b localhost:9002 -t 1000
```

Use `-b 0.0.0.0:9002` for public access

### Frontend
Ensure that Node v20.11.0 and NPM 10.2.4 are installed before continuing.

```bash
cd web/src/pubhealth/templates/pubhealth/
npm install 
npm run dev
```

Use `npm run dev -- --host` for public access. Will also require a change to the `Income.vue`, `IncomeInequality.vue`, `Population.vue`, and `Taxation.vue` files, `web/src/pubhealth/templates/pubhealth/src/views/`. You'll have to change the `domain` variable at the top of the file to the public IP address or DNS name of the server, and the `port` variable as well to match the Gunicorn port.

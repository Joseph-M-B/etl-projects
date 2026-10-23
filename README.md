# ETL Projects

Hands-on ETL pipelines built with Python, pandas, SQLAlchemy and PostgreSQL.

## Project 1: Messy CSV cleaning and loading

Takes a deliberately messy equipment-rental CSV (inconsistent column names,
mixed date formats, text inside number columns, duplicates, blanks), cleans it
with pandas, validates it, and loads it into PostgreSQL.

### What the pipeline does
1. Standardizes column names (lowercase, underscores)
2. Standardizes text values (spacing, capitalization, one mapping for "Bull Dozer")
3. Converts text to numbers; impossible values such as negative days become NULL
4. Parses dates written in three formats; unparseable dates become NULL
5. Removes duplicates after cleaning; removed rows are logged to removed_duplicates.csv
6. Runs seven validation checks and stops if any fail
7. Loads into PostgreSQL with typed columns (DATE, INTEGER, NUMERIC) and verifies the row count; safe to re-run

### Results
- 78 raw rows became 70 clean rows (8 duplicates removed)
- Remaining blanks are kept as NULL, not invented: 3 start dates, 6 days, 4 rates

### How to run
Set the environment variables PG_USER, PG_PASSWORD, PG_HOST, PG_PORT and PG_DB,
then run: python project1/p1_clean.py

Requires: pandas, sqlalchemy, psycopg2-binary



## Project 2: Weather API to PostgreSQL (re-runnable ETL)

Pulls daily weather for four equipment sites (Eket Yard, Uyo Road Project,
Calabar Bridge, Port Harcourt Depot) from the Open-Meteo Historical Weather API,
reshapes it with pandas, and loads it into PostgreSQL. Site coordinates are
approximate town locations. Weather data by Open-Meteo.com (non-commercial use).

### What the pipeline does
1. Extract: one API call per site (Jan to Jun 2025), checking the status code and
   surfacing the server's error reason; a one-second pause between calls
2. Transform: turn the API's parallel lists into a table, name columns with units
   (temp_max_c, precip_mm), and check for missing values
3. Load: write to `weather_daily` with a primary key on (site, weather_date) using
   INSERT ... ON CONFLICT DO UPDATE, so re-running never duplicates rows

### Tested
- 4 sites x 181 days = 724 rows; running twice still gives 724 rows
- Damaged the table on purpose (deleted 10 rows, corrupted one value); one re-run
  restored all 724 rows and the correct value

### How to run
Set PG_USER, PG_PASSWORD, PG_HOST, PG_PORT and PG_DB, then run
`python project2/p2_extract_transform.py`. The `exploration` folder holds the
learning scripts used to study the API (status codes, headers, JSON).
`exploration/sample_response.json` is a saved example of the API's reply
(3 days, daily temperature and rainfall), so you can see its shape without
running anything.

Requires: pandas, requests, sqlalchemy, psycopg2-binary
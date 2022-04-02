# Tyler Technologies Odyssey scraper and parser

This is a scraper to collect and process public case records from the Tyler Technologies Odyssey court records system. Tested with Hays, Smith, and Harris counties.

## Install

1. Clone this repo and navigate to it.
   - `git clone https://github.com/open-austin/Odyssey-Court-Records-to-JSON`
   - `cd Odyssey-Court-Records-to-JSON`
     min1. Install [poetry](https://python-poetry.org/docs/#installation) and [pyenv](https://github.com/pyenv/pyenv#installation). Benefits are easier env management and reproducable builds.
1. Install libraries.
   - `poetry install`
1. Alternatively with pip, if you don't want to install poetry.
   - `pip install -r requirements.txt`

## Use

_**--help for parameter details.**_

Output of these commands will go to `./data/COUNTY_NAME`

1. Scrape case HTML data through date range.
   - `poetry run python ./src/scraper -start_date 01/01/1970 -end_date 01/01/1970 -county hays`
   - Use "python3" instead of "poetry run python" if you are not using poetry.
1. Parse the case data into JSON files.
   - `poetry run python ./src/parser.py -county hays`

## Other files

- `resources/texas_county_data.csv` - We are storing portal pages and relevant metadata here. Put the main portal page with a trailing slash.
- `resources/minimum_scraper_examples` - Educational resource to understand the flow for scraping each site.
- `src/tools/combine_parsed.py -county hays` - a script to combine JSON files into one and put it in an s3 bucket.
- `src/tools/print_stats.py -county hays` - Get some stats from the JSON data

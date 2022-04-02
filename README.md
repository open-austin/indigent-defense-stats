# Tyler Technologies Odyssey scraper and parser

This is a scraper to collect and process public case records from the Tyler Technologies Odyssey court records system. Tested with Hays, Smith, and Harris counties.

## Installation

1. Clone this repo.
   - `git clone https://github.com/derac/Odyssey-Court-Records-to-JSON.git`
1. Navigate to it. (use venv if desired)
   - `cd Odyssey-Court-Records-to-JSON`
1. Install [poetry](https://python-poetry.org/docs/#installation).
1. (Optional) Install [pyenv](https://github.com/pyenv/pyenv#installation).
1. Install libraries.
   - `poetry install`

## Usage

_**Use --help for parameter info.**_

1. Output of these commands will go to `./data/COUNTY_NAME`
1. Scrape case HTML data through date range.
   - `poetry run python ./src/scraper -start_date 01/01/1970 -end_date 01/01/1970 -county hays`
1. Parse the case data into JSON files.
   - `poetry run python ./src/parser.py -county hays`

## Info on other files

- The command `poetry run python src/combine_parsed.py` will run a script to combine html files into a .json in an s3 bucket.
- `texas_county_data.csv` - We are storing portal pages and relevant metadata here. Put the main portal page with a trailing slash.
- `/resources/minimum_scraper_examples` - Educational resource to understand the flow for scraping each site.
- `poetry run python ./src/print_stats.py -county hays` - Get some stats from the JSON data

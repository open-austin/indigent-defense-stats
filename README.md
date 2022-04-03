# Tyler Technologies Odyssey scraper and parser

This is a scraper to collect and process public case records from the Tyler Technologies Odyssey court records system. If you are a dev or want to file an Issue, please read [CONTRIBUTING](CONTRIBUTING.md).

## Install

1. Clone this repo and navigate to it.
   - `git clone https://github.com/open-austin/Odyssey-Court-Records-to-JSON`
   - `cd Odyssey-Court-Records-to-JSON`
1. Install [poetry](https://python-poetry.org/docs/#installation) and [pyenv](https://github.com/pyenv/pyenv#installation). Benefits are easier env management and reproducable builds.
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
   - `poetry run python ./src/parser -county hays`

## Other files

- [resources/texas_county_data.csv](resources/texas_county_data.csv) - We are storing portal pages and relevant metadata here. Put the main portal page with a trailing slash.
- [src/tools/combine_parsed.py](src/tools/combine_parsed.py) - a script to combine JSON files into one and put it in an s3 bucket.
- [src/tools/print_stats.py](src/tools/print_stats.py) - Get some stats from the JSON data

# Compatibility info

I did a manual scraping test up to returning search results, most dates have 0 results, so I didn't test scraping case data from the search on any of these. Here is the data:

12/59 do not work, 79.6% do work. 3 are captcha-blocked, 9 are currently impossible (site down or search disabled). 75.8% of the population should be scrapable without captcha solving. 2.9% of population is under captcha.

Parser for post 2017 sites is not complete. Parser for pre-2017 sites works well, but needs a lot more testing.

## Galveston, Cameron, Angelina

captcha on search page, reCaptcha for post-2017 and simple obscured letters image for pre-2017

## Kaufman, Hunt, El Paso, Comal, Chambers

Court Calendar (pre-2017) or Search Hearings (post-2017) disabled

## Matagorda, Gillespie, Bexar, Kerr

503 Service unavailable or 403 Forbidden

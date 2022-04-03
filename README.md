# Tyler Technologies Odyssey scraper and parser

This is a scraper to collect and process public case records from the Tyler Technologies Odyssey court records system.

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

I did a manual test up to returning search results, most dates have 0 results, so I didn't test scraping case data from the search on any of these. Here is the data:

23/59 do not work, 61% do work. 12 of these should be easy to fix, 2 are reCaptcha, 9 are impossible (site down or search disabled).

## Williamson, Donton

```
ERROR:pid: 5408:'Court Calendar link' could not be found in page. Aborting. Writing /data/debug.html with response. May not be HTML.
```

## Angelina

```
ERROR:pid: 19484:Verification text Record Count not in response
```

## Victoria, Tarrant, Howard, Grayson, Fort Bend, Collin, Austin

```
Traceback (most recent call last):
  File "c:\Users\Derek\.pyenv\pyenv-win\versions\3.8.10\lib\runpy.py", line 194, in _run_module_as_main
    return _run_code(code, main_globals, None,
  File "c:\Users\Derek\.pyenv\pyenv-win\versions\3.8.10\lib\runpy.py", line 87, in _run_code
    exec(code, run_globals)
  File "F:\Projects\Odyssey-Court-Records-to-JSON\.\src\scraper\__main__.py", line 94, in <module>
    location_option = main_soup.findAll("option", text=re.compile(args.location))[0]
IndexError: list index out of range
```

## Morris, Burnet

needs public login

## Galveston, Cameron

reCaptcha on search page

## Kaufman, Hunt, El Paso, Comal, Chambers

Court Calendar (pre-2017) or Search Hearings (post-2017) disabled

## Matagorda, Gillespie, Bexar, Kerr

503 Service unavailable or 403 Forbidden

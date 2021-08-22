## Hays County Criminal Records Scraper

This is a simple scraper that uses `requests` and `beautifulsoup` to collect and process case records from the [Hayes County Criminal Records](http://public.co.hays.tx.us/) public database.

### Installation and Usage

1. Clone this repo - `git clone https://github.com/derac/hays-scraper.git`
1. Go to it - `cd hays-scraper`
1. _(optional)_ Make a virtual environment - `python -m venv .`
1. _(optional)_ Activate it - `source bin/activate` (bash) or `./Scripts/activate.ps1` (powershell)
1. Install libraries - `pip install -r requirements.txt`
1. Scrape the calendar data - `python ./src/scrape_calendar_data.py` - this will go to _./data_by_JO/{JO_name}/calendar_html/\*.html_
1. Process the calendar data and scrape the individual cases `python ./src/scrape_case_data` - this will go to _./data_by_JO/{JO_name}/case_html/\*.html_

### Command line parameter usage info:

```bash
python ./src/scrape_calendar_data.py --help
python ./src/scrape_case_data.py --help
```

## TODO

- Write parser for case data and determine schema.
- Implement retry behavior when a request fails by starting a new session once, then quitting instead of quitting immediately.
- Add session persistance across runs, then change the case scraping code which needs to visit the case's calendar page to only do so on failure. Then, try getting a new session, if that doesn't work, quit.
- Potentially scrape the calendar by doing the entire date range, then if the returned results are more than 200, split the search space in half. Do so over and over. This would complicate the cache checking code. Probably not be necessary as the pages for 5 years and 10 JOs can be scraped with 200ms rate limiting in _(5\*365\*10 pages/5/60/60)_ = ~ 1 hour and 18250 requests.

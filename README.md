## Hays County Criminal Records Scraper

This is a scraper to collect and process public case records from the [Hayes County Criminal Records](http://public.co.hays.tx.us/) database. The intention is to gain insight and advocate for defendant's rights.

This should be adaptable to other Tyler Technologies Odyssey based court records sites.

### Installation

1. Clone this repo.
   - `git clone https://github.com/derac/hays-scraper.git`
1. Navigate to it.
   - `cd hays-scraper`
1. _(optional)_ Make a virtual environment.
   - `python -m venv .`
1. _(optional)_ Activate it.
   - _bash_ `source bin/activate`
   - _powershell_ `./Scripts/activate.ps1`
   - _fish_ `source bin/activate.fish`
1. Install libraries.
   - `pip install -r requirements.txt`

### Usage

**Use --help for command line parameter information.**

1. Scrape calendar data by JO and day.
   - `python ./src/scrape_calendar_data.py`
   - _./data_by_JO/_{**JO name**}_/calendar_html/_{**date**}_.html_
1. Scrape individual cases from calendar data.
   - `python ./src/scrape_case_data.py`
   - _./data_by_JO/_{**JO name**}_/case_html/_{**date**} {**odyssey id**}_.html_
1. Process the case data into JSON files.
   - `python ./src/process_case_data.py`
   - _./data_by_JO/_{**JO name**}_/case_data/_{**case code**}_.json_
1. Print some stats from the JSON.
   - `python ./src/print_case_stats.py`

## Implementation Details

- The session must visit the main page in order to access the calendar search page.
- To visit a case page, you must have visited a results page containing it.
- Some form data must be sent with the search request. Data in _./src/libraries/scrape_config.py_.

## TODO

- failure found where a 0kb case file was written, need checking for strings and retrying
- Implement retry behavior when a request fails by starting a new session once, then quitting instead of quitting immediately.
- Add session persistance across runs, then change the case scraping code which needs to visit the case's calendar page to only do so on failure. Then, try getting a new session, if that doesn't work, quit.
- Potentially scrape the calendar by doing the entire date range, then if the returned results are more than 200, split the search space in half. Do so over and over. This would complicate the cache checking code. Probably not be necessary as the pages for 5 years and 10 JOs can be scraped with 200ms rate limiting in _(5\*365\*10 pages/5/60/60)_ = ~ 1 hour and 18250 requests.
- Some Odyssey based sites have a CAPTCHA on the main page. This can't beat that. yet. 😅

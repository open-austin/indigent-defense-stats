## Hays County Criminal Records Scraper

This is a scraper to collect and process public case records from the [Hayes County Criminal Records](http://public.co.hays.tx.us/) database. The intention is to gain insight into this opaque system and advocate for defendant's rights.

This should be adaptable to other Tyler Technologies Odyssey based court records sites.

### Installation and Usage

1. Clone this repo - `git clone https://github.com/derac/hays-scraper.git`
1. Go to it - `cd hays-scraper`
1. _(optional)_ Make a virtual environment - `python -m venv .`
1. _(optional)_ Activate it - `source bin/activate` (bash) or `./Scripts/activate.ps1` (powershell)
1. Install libraries - `pip install -r requirements.txt`
1. Scrape the calendar data - `python ./src/scrape_calendar_data.py` - this will go to _./data_by_JO/{JO_name}/calendar_html/\*.html_
1. Process the calendar data and scrape the individual cases `python ./src/scrape_case_data.py` - this will go to _./data_by_JO/{JO_name}/case_html/\*.html_
1. Process the case data into json files `python ./src/process_case_date.py` - this will go to _./data_by_JO/{JO_name}/case_data/\*.json_

### Command line parameter usage info:

    python ./src/scrape_calendar_data.py --help
    python ./src/scrape_case_data.py --help
    python ./src/process_case_data.py --help

## Implementation Details

The session must visit the main page to access the calendar page. Also, you must visit a calendar results page which contains the case page you are trying to access in order to visit it.

## TODO

- Implement retry behavior when a request fails by starting a new session once, then quitting instead of quitting immediately.
- Add session persistance across runs, then change the case scraping code which needs to visit the case's calendar page to only do so on failure. Then, try getting a new session, if that doesn't work, quit.
- Potentially scrape the calendar by doing the entire date range, then if the returned results are more than 200, split the search space in half. Do so over and over. This would complicate the cache checking code. Probably not be necessary as the pages for 5 years and 10 JOs can be scraped with 200ms rate limiting in _(5\*365\*10 pages/5/60/60)_ = ~ 1 hour and 18250 requests.
- Some Odyssey based sites have a CAPTCHA on the main page. This can't beat that. yet. 😅

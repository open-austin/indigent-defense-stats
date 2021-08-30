## Tyler Technologies Odyssey court records scraper and parser

This is a scraper to collect and process public case records from the Tyler Technologies Odyssey County Records system. The intention is to gain insight and advocate for defendant's rights. A google search for ["Copyright \* Tyler Technologies" "Court Calendar"](https://www.google.com/search?q=%22Copyright+*+Tyler+Technologies%22+%22Court+Calendar%22&oq=%22Copyright+*+Tyler+Technologies%22+%22Court+Calendar%22&aqs=edge..69i57.283j0j1&sourceid=chrome&ie=UTF-8) will show some other possible sites to scrape. You should just need to input parameters for the main page and a list of JOs and scrape any Odyssey page.

Tested with:

- http://public.co.hays.tx.us/ (~4k cases from 2 months from 9 JOs)
- https://txhoododyprod.tylerhost.net/PublicAccess/ (110 cases from 1 JO)
- https://judicial.smith-county.com/PublicAccess/ (125 cases from 1 JO)

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

1. Scrape calendar and case data by JO and day. The data will be cached in the following way.
   - `python ./src/scrape_html.py`
   - _./data_by_JO/_{**JO name**}_/calendar_html/_{**date**}_.html_
   - _./data_by_JO/_{**JO name**}_/case_html/_{**date**} {**odyssey id**}_.html_
1. Parse the case data into JSON files.
   - `python ./src/parse_json.py`
   - _./data_by_JO/_{**JO name**}_/case_json/_{**case code**}_.json_
1. Print some stats from the JSON.
   - `python ./src/print_stats.py`

## Implementation Details

- The session must visit the main page in order to access the calendar search page.
- To visit a case page, you must have visited a results page containing it.
- Some form data must be sent with the search request. Data in _./src/libraries/scrape_config.py_.
- hidden values are grabbed from the calendar page, NodeID and NodeDesc are grabbed from the main page.

## TODO
- Some Odyssey sites have a CAPTCHA on the main page. This can't beat that. yet. 😅
- Some Odysset sites have multiple choices for court calendars and some other options that could be implemented as parameters.

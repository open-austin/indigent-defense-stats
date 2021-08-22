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

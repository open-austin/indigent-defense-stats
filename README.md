## Hays County Criminal Records Scraper

This is (currently) a simple proof-of-concept that uses `requests`, `datetime`
and `beautifulsoup` to collect case records over the past five years.

### Installation

1. Clone this repo - `git clone https://github.com/derac/hays-scraper.git`
1. Go to it - `cd hays-scraper`
1. *(optional)* Make a virtual environment - `python -m venv .`
1. *(optional)* Activate it - `source bin/activate` (bash) or `./Scripts/activate.ps1` (powershell)
1. Install libraries - `pip install -r requirements.txt`
2. Run it - `./src/scrape.py`

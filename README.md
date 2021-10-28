## Tyler Technologies Odyssey court records scraper and parser

This is a scraper to collect and process public case records from the Tyler Technologies Odyssey County Records system. The intention is to gain insight and advocate for defendant's rights. A google search for ["Copyright \* Tyler Technologies" "Court Calendar"](https://www.google.com/search?q=%22Copyright+*+Tyler+Technologies%22+%22Court+Calendar%22&oq=%22Copyright+*+Tyler+Technologies%22+%22Court+Calendar%22&aqs=edge..69i57.283j0j1&sourceid=chrome&ie=UTF-8) will show some other possible sites to scrape. You should just need to input parameters for the main page and a list of JOs and scrape any Odyssey page.

Tested with:

- http://public.co.hays.tx.us/ (~4k cases from 2 months from 9 JOs)
- https://txhoododyprod.tylerhost.net/PublicAccess/ (110 cases from 1 JO)
- https://judicial.smith-county.com/PublicAccess/ (125 cases from 1 JO)

### Installation

1. Clone this repo.
   - `git clone https://github.com/derac/Odyssey-Court-Records-to-JSON.git`
1. Navigate to it. (use venv if desired)
   - `cd Odyssey-Court-Records-to-JSON`
1. Install libraries.
   - `pip install -r requirements.txt`

### Usage

**Use --help for command line parameter information.**

1. Scrape calendar and case data by JO and day.
   - `python ./src/scraper.py`
   - _./data/case_html/_**odyssey id**_.html_
1. Parse the case data into JSON files.
   - `python ./src/parser.py`
   - _./data/case_json/_**odyssey id**_.json_
1. Print some stats from the JSON.
   - `python ./src/print_stats.py`

## Implementation Details

- The session must visit the main page in order to access the calendar search page. To visit a case page, you must have visited a results page containing it.
- hidden values are grabbed from the calendar page, NodeID and NodeDesc are grabbed from the main page location field.

## Writing to s3 bucket
The command `python3.8 src/combine_parsed.py` will run a script to combine html files into a .json in an s3 bucket. 
Currently this is running daily on a shell script, on only 1000 files as an example to see schema for Athena.

## TODO

- Some Odyssey sites have a CAPTCHA on the calendar page. This can't beat that yet. Could implement 2Captcha or get input from user potentially.
- The only bit that seems to break between sites is parsing party information. Need to recode this to work in a different way.

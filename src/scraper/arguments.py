import argparse
from datetime import date, timedelta, datetime

argparser = argparse.ArgumentParser()

argparser.add_argument(
    "-ms_wait",
    "-w",
    type=int,
    default=200,
    help="Number of ms to wait between requests.",
)
argparser.add_argument(
    "-judicial_officers",
    "-j",
    nargs="*",
    type=str,
    default=[],
    help="Judicial Officers to scrape. For example, -j 'mr. something' 'Rob, Albert'. By default, it will scrape all JOs.",
)
argparser.add_argument(
    "-no_overwrite",
    "-o",
    action="store_true",
    help="Switch to don't overwrite cached html files if you want to speed up the process (but may not get the most up to date version).",
)
argparser.add_argument(
    "-log",
    type=str,
    default="INFO",
    help="Set the level to log at.",
)
argparser.add_argument(
    "-court_calendar_link_text",
    "-cclt",
    type=str,
    default="Court Calendar",
    help="This is the link to the Court Calendar search page at default.aspx, usually it will be 'Court Calendar', but some sites have multiple calendars e.g. Williamson",
)
argparser.add_argument(
    "-location",
    "-l",
    type=str,
    help="'Select a location' select box on the main page. Default to the the first entry, which is usually all courts.",
)
argparser.add_argument(
    "-test",
    "-t",
    action="store_true",
    help="If this parameter is present, the script will stop after the first case is scraped.",
)
argparser.add_argument(
    "-case_number",
    "-cnum",
    type=str,
    help="If a case number is entered, only that single case is scraped. ex. 12-2521CR",
)
argparser.description = "Scrape data for list of judicial officers in date range."
args = argparser.parse_args()

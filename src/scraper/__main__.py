import logging, os, csv
from arguments import args

import requests

import pre2017, post2017

from helpers import *
from arguments import args  # argument settings here

session = requests.Session()
# allow bad ssl and turn off warnings
session.verify = False
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

logger = logging.getLogger(name=str(os.getpid()))
logging.basicConfig()
logging.root.setLevel(level=args.log)

# make cache directories if not present
case_html_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", args.county, "case_html"
)
os.makedirs(case_html_path, exist_ok=True)

# get county portal and version year information from csv file
base_url = odyssey_version = notes = None
with open(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "resources", "texas_county_data.csv"
    ),
    mode="r",
) as file_handle:
    csv_file = csv.DictReader(file_handle)
    for row in csv_file:
        if row["county"].lower() == args.county.lower():
            base_url = row["portal"]
            # add trailing slash if not present, otherwise urljoin breaks
            if base_url[-1] != "/":
                base_url += "/"
            logger.info(f"{base_url} - scraping this url")
            odyssey_version = int(row["version"].split(".")[0])
            notes = row["notes"]
            break
if not base_url or not odyssey_version:
    raise Exception(
        "The required data to scrape this county is not in ./resources/texas_county_data.csv"
    )

if odyssey_version < 2017:
    case_data = pre2017.scrape(session, base_url, notes, logger, args, case_html_path)
else:
    case_data = post2017.scrape(session, base_url, notes, logger, args, case_html_path)

import os, argparse, csv, json, traceback, xxhash
from time import time

from bs4 import BeautifulSoup

import pre2017, post2017

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-overwrite",
    "-o",
    action="store_true",
    help="Switch to overwrite already parsed data.",
)
argparser.add_argument(
    "-county",
    "-c",
    type=str,
    default="hays",
    help="The name of the county.",
)
argparser.description = "Parse data for the specified county."
args = argparser.parse_args()

# get directories and make json dir if not present
case_html_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", args.county, "case_html"
)
case_json_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", args.county, "case_json"
)
if not os.path.exists(case_json_path):
    os.makedirs(case_json_path, exist_ok=True)

# get county version year information to determine which scraper to use
base_url = odyssey_version = None
with open(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "resources", "texas_county_data.csv"
    ),
    mode="r",
) as file_handle:
    csv_file = csv.DictReader(file_handle)
    for row in csv_file:
        if row["county"].lower() == args.county.lower():
            odyssey_version = int(row["version"].split(".")[0])
            break
if not odyssey_version:
    raise Exception(
        "The required data to scrape this county is not in ./resources/texas_county_data.csv"
    )

START_TIME = time()

cached_case_json_list = [
    file_name.split(".")[0] for file_name in os.listdir(case_json_path)
]

for case_html_file_name in os.listdir(case_html_path):
    try:
        case_id = case_html_file_name.split(".")[0]
        if case_id in cached_case_json_list and not args.overwrite:
            continue
        case_html_file_path = os.path.join(case_html_path, case_html_file_name)
        print(f"{case_id} - parsing")
        with open(case_html_file_path, "r") as file_handle:
            case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")

        if odyssey_version < 2017:
            case_data = pre2017.parse(case_soup, case_id)
        else:
            case_data = post2017.parse(case_soup, case_id)

        #Adds a hash to the JSON file of the underlying HTML
        body = case_soup.find("body")
        #This section removes the "balance due" table, which changes frequently with payment even if the case data itself isn't updated, so it makes the hashes look unique even when things haven't changed. 
        balance_table = body.find_all("table")[-1]
        if "Balance Due" in balance_table.text:
            balance_table.decompose()
        case_data["html_hash"] = xxhash.xxh64(str(body)).hexdigest()
        
        # Write JSON data
        with open(os.path.join(case_json_path, case_id + ".json"), "w") as file_handle:
            file_handle.write(json.dumps(case_data))
    except Exception:
        print(traceback.format_exc())
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "data",
                args.county,
                "cases_with_parsing_error.txt",
            ),
            "w",
        ) as file_handle:
            file_handle.write(case_id + "\n")
RUN_TIME = time() - START_TIME
print(f"Parsing took {RUN_TIME} seconds")

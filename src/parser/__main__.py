import os, argparse, csv, json, traceback, xxhash
from time import time

from bs4 import BeautifulSoup

from .pre2017  import pre2017_parser
from .post2017  import post2017_parser

class parser:

    def __init__(self, county):
        self.county = county.lower()

    def parse(self):

        # get directories and make json dir if not present
        case_html_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", self.county, "case_html"
        )
        case_json_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", self.county, "case_json"
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
                if row["county"].lower() == self.county.lower():
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
                if case_id in cached_case_json_list:
                    continue
                case_html_file_path = os.path.join(case_html_path, case_html_file_name)
                print(f"{case_id} - parsing")
                with open(case_html_file_path, "r") as file_handle:
                    case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")

                if odyssey_version < 2017:
                    case_data = pre2017_parser(case_id, self.county).parse_pre2017(case_soup)
                else:
                    case_data = post2017_parser(case_id, self.county).parse_post2017(case_soup)
                #Adds county field to data
                case_data['county'] = self.county
                #Adds a hash to the JSON file of the underlying HTML
                body = case_soup.find("body")
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
                        self.county,
                        "cases_with_parsing_error.txt",
                    ),
                    "w",
                ) as file_handle:
                    file_handle.write(case_id + "\n")

        RUN_TIME = time() - START_TIME
        print(f"Parsing took {RUN_TIME} seconds")

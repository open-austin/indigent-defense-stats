import os
import json
from datetime import datetime

from bs4 import BeautifulSoup

for JO_folder in os.scandir("data_by_JO"):
    case_data_path = os.path.join(JO_folder.path, "case_data")
    if not os.path.exists(case_data_path):
        os.mkdir(case_data_path)
    for case_html_file in os.scandir(os.path.join(JO_folder.path, "case_html")):
        print("Processing", case_html_file.path)
        case_data = {}
        with open(case_html_file.path, "r") as file_handle:
            case_html = file_handle.read()
        case_soup = BeautifulSoup(case_html, "html.parser")
        # Gather initial data for filename and date checking
        case_data["name"] = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
            0
        ].text
        case_data["date"] = case_html_file.name.split()[0]
        case_filename = os.path.join(case_data_path, case_data["name"] + ".json")
        # If file exists, check if the cached version has a newer date, if so continue.
        if os.path.exists(case_filename):
            with open(case_filename, "r") as file_handle:
                cached_data = json.loads(file_handle.read())
            cached_date = datetime.strptime(cached_data["date"], "%m-%d-%Y")
            current_date = datetime.strptime(case_data["date"], "%m-%d-%Y")
            if cached_date > current_date:
                print("Cached data is newer. Continuing.")
                continue
        # Continue to parse and gather data.

        # Quit for now so we don't write a bunch of crap
        quit()
        # Write file as json data
        with open(case_filename, "w") as file_handle:
            file_handle.write(json.dumps(case_data))

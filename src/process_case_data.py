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
        # TODO: there are multiple types of cases, most are the CR-* type, but some are different
        # have a different code naming convention and layout
        # Gather initial data for filename and date checking
        case_data["code"] = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
            0
        ].text
        case_data["osyssey_id"] = case_html_file.name.split()[1].split(".")[0]
        case_data["date"] = case_html_file.name.split()[0]
        case_filename = os.path.join(case_data_path, case_data["code"] + ".json")
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
        # get all the root tables
        root_tables = case_soup.select("body>table")
        for table in root_tables:
            # The State of Texas vs. X, Cast Type, Date Filed, etc.
            if "Case Type:" in table.text and "Date Filed:" in table.text:
                table_values = table.select("b")
                table_labels = table.select("th")
                # the first value doesn't have a label, it's the case name
                case_data["name"] = table_values[0].text
                for i in range(len(table_labels)):
                    value = table_values[i + 1].text
                    # sometimes there is a blank space next to the value
                    # add that value to the last label
                    if table_labels[i].text:
                        label = table_labels[i].text
                        case_data[label[:-1].lower()] = value
                    else:
                        case_data[label[:-1].lower()] += "\n" + value
            if "Related Case Information" in table.text:
                case_data["related_cases"] = [
                    case.text.strip().replace("\xa0", " ")
                    for case in table.select("td")
                ]
            if "Party Information" in table.text:
                # the layout here is very goofy, just dumping raw text as a list for now
                case_data["party_information"] = [
                    tag.strip().replace("\xa0", " ")
                    for tag in table.find_all(text=True)
                    if tag.strip()
                ]
            if "Charge Information" in table.text:
                table_text = [
                    tag.strip().replace("\xa0", " ")
                    for tag in table.find_all(text=True)
                    if tag.strip()
                ]
                case_data["charge_information"] = []
                for i in range(5, len(table_text), 5):
                    case_data["charge_information"].append(
                        {
                            k: v
                            for k, v in zip(
                                ["Charges", "Statute", "Level", "Date"],
                                table_text[i + 1 : i + 5],
                            )
                        }
                    )
            if "Events & Orders of the Court" in table.text:
                ...
                # extremely goofy layout
                ## DISPOSITIONS
                ## OTHER EVENTS AND HEARINGS
            if "Financial Information" in table.text:
                ...

        # Quit for now so we don't write a bunch of crap
        print(case_data)
        quit()
        # Write file as json data
        with open(case_filename, "w") as file_handle:
            file_handle.write(json.dumps(case_data))

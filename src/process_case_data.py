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
        case_data["code"] = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
            0
        ].text
        case_data["osyssey id"] = case_html_file.name.split()[1].split(".")[0]
        case_data["date"] = case_html_file.name.split()[0].replace("-", "/")
        case_filename = os.path.join(case_data_path, case_data["code"] + ".json")
        # If file exists, check if the cached version has a newer date, if so continue.
        if os.path.exists(case_filename):
            with open(case_filename, "r") as file_handle:
                cached_data = json.loads(file_handle.read())
            cached_date = datetime.strptime(cached_data["date"], "%m/%d/%Y")
            current_date = datetime.strptime(case_data["date"], "%m/%d/%Y")
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
            elif "Related Case Information" in table.text:
                case_data["related cases"] = [
                    case.text.strip().replace("\xa0", " ")
                    for case in table.select("td")
                ]
            elif "Party Information" in table.text:
                table_rows = [
                    [
                        tag.strip().replace("\xa0", " ")
                        for tag in tr.find_all(text=True)
                        if tag.strip()
                    ]
                    for tr in table.select("tr")
                ]
                table_rows = [sublist for sublist in table_rows if sublist]
                state_rows = []
                defendant_rows = []
                bondsman_rows = []
                SECTION = "state"
                while table_rows and (row := table_rows.pop()):
                    if SECTION == "state":
                        state_rows.append(row)
                    if SECTION == "defendant":
                        defendant_rows.append(row)
                    if SECTION == "bondsman":
                        bondsman_rows.append(row)
                    if row[0] == "State":
                        SECTION = "defendant"
                    if row[0] == "Defendant":
                        SECTION = "bondsman"
                    if row[0] == "Bondsman":
                        break
                state_rows = state_rows[::-1]
                defendant_rows = defendant_rows[::-1]
                bondsman_rows = bondsman_rows[::-1]
                if bondsman_rows[0][0] != "Bondsman":
                    bondsman_rows = []

                has_height_and_weight = "," in defendant_rows[0][4]
                party_information = {
                    "defendant": defendant_rows[0][1],
                    "sex": defendant_rows[0][2].split()[0],
                    "race": " ".join(defendant_rows[0][2].split()[1:]),
                    "date of birth": defendant_rows[0][3].split()[1],
                    "height": defendant_rows[0][4].split(",")[0]
                    if has_height_and_weight
                    else "",
                    "weight": defendant_rows[0][4].split(",")[1][1:]
                    if has_height_and_weight
                    else "",
                    "defense attorney": defendant_rows[0][
                        5 + (has_height_and_weight - 1)
                    ]
                    if len(defendant_rows[0]) > 5 + (has_height_and_weight - 1)
                    else "",
                    "appointed or retained": defendant_rows[0][
                        6 + (has_height_and_weight - 1)
                    ]
                    if len(defendant_rows[0]) > 6 + (has_height_and_weight - 1)
                    else "",
                    "defense attorney phone number": defendant_rows[0][
                        7 + (has_height_and_weight - 1)
                    ]
                    if len(defendant_rows[0]) > 7 + (has_height_and_weight - 1)
                    else "",
                    "defendant address": ", ".join(defendant_rows[1][:-2]),
                    "SID": defendant_rows[1][-1],
                    "prosecuting attorney": state_rows[0][2]
                    if len(state_rows[0]) > 2
                    else "",
                    "prosecuting attorney phone number": state_rows[0][3]
                    if len(state_rows[0]) > 3
                    else "",
                    "prosecuting attorney address": ", ".join(state_rows[1]),
                    "bondsman": bondsman_rows[0][1] if bondsman_rows else "",
                    "bondsman address": ", ".join(bondsman_rows[1])
                    if len(bondsman_rows) > 1
                    else "",
                }
                case_data["party information"] = party_information
            elif "Charge Information" in table.text:
                table_rows = [
                    tag.strip().replace("\xa0", " ")
                    for tag in table.find_all(text=True)
                    if tag.strip()
                ]
                case_data["charge information"] = []
                for i in range(5, len(table_rows), 5):
                    case_data["charge information"].append(
                        {
                            k: v
                            for k, v in zip(
                                ["charges", "statute", "level", "date"],
                                table_rows[i + 1 : i + 5],
                            )
                        }
                    )
            elif "Events & Orders of the Court" in table.text:
                table_rows = [
                    [
                        tag.strip().replace("\xa0", " ")
                        for tag in tr.find_all(text=True)
                        if tag.strip()
                    ]
                    for tr in table.select("tr")
                    if tr.select("th")
                ]
                table_rows = [
                    [
                        " ".join(word.strip() for word in text.split())
                        for text in sublist
                    ]
                    for sublist in table_rows
                    if sublist
                ]
                other_event_rows = []
                disposition_rows = []
                SECTION = "other_events"
                while table_rows and (row := table_rows.pop()):
                    if row[0] == "OTHER EVENTS AND HEARINGS":
                        SECTION = "dispositions"
                        continue
                    if row[0] == "dispositions":
                        break
                    if SECTION == "other_events":
                        other_event_rows.append(row)
                    if SECTION == "dispositions":
                        disposition_rows.append(row)
                other_event_rows = other_event_rows[::-1]
                disposition_rows = disposition_rows[::-1]
                case_data["other events and hearings"] = other_event_rows
                case_data["dispositions"] = disposition_rows
            elif "Financial Information" in table.text:
                table_rows = [
                    [
                        tag.strip().replace("\xa0", " ")
                        for tag in tr.find_all(text=True)
                        if tag.strip()
                    ]
                    for tr in table.select("tr")
                    if tr.select("th")
                ]
                table_rows = [
                    [
                        " ".join(word.strip() for word in text.split())
                        for text in sublist
                    ]
                    for sublist in table_rows
                    if sublist
                ]
                financial_information = {
                    "total financial assessment": table_rows[1][1],
                    "total payments and credits": table_rows[2][1],
                    "balance due": table_rows[3][1],
                    "transactions": table_rows[4:],
                }
                case_data["financial_information"] = financial_information
            elif "Location : All Courts" not in table.text and table.text:
                ...
                # print to see if there are sections we are missing in any of the table sections
                # print(table)

        print(case_data)

        # Write file as json data
        # with open(case_filename, "w") as file_handle:
        #     file_handle.write(json.dumps(case_data))

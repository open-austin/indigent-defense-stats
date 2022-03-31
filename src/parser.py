import os
import json
import argparse
from time import time
from bs4 import BeautifulSoup

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
    os.path.dirname(__file__), "..", "data", args.county, "case_html"
)
case_json_path = os.path.join(
    os.path.dirname(__file__), "..", "data", args.county, "case_json"
)
if not os.path.exists(case_json_path):
    os.makedirs(case_json_path, exist_ok=True)

# read in files that didn't work
broken_json_path = os.path.join(case_json_path, "broken_files.txt")
if not os.path.exists(broken_json_path):
    broken_files = []
else:
    with open(broken_json_path, "a+") as f:
        broken_files = f.readlines()
        broken_files = list(set(broken_files))
        f.truncate()

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
        print(case_html_file_path)
        case_data = {}
        with open(case_html_file_path, "r") as file_handle:
            case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")
        # Gather initial data for filename and date checking
        case_data["code"] = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
            0
        ].text
        case_data["odyssey id"] = case_id
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
                        tag.strip().replace("\xa0", "").replace("Â", "")
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

                has_height_and_weight = (
                    len(defendant_rows[0]) > 4 and "," in defendant_rows[0][4]
                )
                has_sex = len(defendant_rows[0]) > 2 and "," in defendant_rows[0][2]
                party_information = {
                    "defendant": defendant_rows[0][1],
                    "sex": defendant_rows[0][2].split()[0] if has_sex else "",
                    "race": " ".join(defendant_rows[0][2].split()[1:])
                    if len(defendant_rows[0]) > 3
                    else "",
                    "date of birth": defendant_rows[0][3].split()[1]
                    if len(defendant_rows[0]) > 3
                    else "",
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
                    "defendant address": ", ".join(
                        defendant_rows[1][:-2] if len(defendant_rows) > 1 else []
                    ),
                    "SID": defendant_rows[1][-1] if len(defendant_rows) > 1 else "",
                    "prosecuting attorney": state_rows[0][2]
                    if len(state_rows[0]) > 2
                    else "",
                    "prosecuting attorney phone number": state_rows[0][3]
                    if len(state_rows[0]) > 3
                    else "",
                    "prosecuting attorney address": ", ".join(
                        state_rows[1] if len(state_rows) > 1 else []
                    ),
                    "bondsman": bondsman_rows[0][1] if bondsman_rows else "",
                    "bondsman address": ", ".join(bondsman_rows[1])
                    if len(bondsman_rows) > 1
                    else "",
                }

                # Temporary cleanup options for "appointed or retained"
                # TODO: fix parser for these cases
                allowed_states = ["Appointed", "Retained", "Court Appointed"]
                check_phrases = ["Court Appointed", "Retained", "Appointed", "Pro Se"]
                if party_information["appointed or retained"] not in allowed_states:
                    party_information["appointed or retained"] = ""
                    for phrase in check_phrases:
                        if phrase.lower() in str(defendant_rows).lower():
                            party_information["appointed or retained"] = phrase
                            break

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
                    if row[0] == "DISPOSITIONS":
                        break
                    if SECTION == "other_events":
                        other_event_rows.append(row)
                    if SECTION == "dispositions":
                        disposition_rows.append(row)
                other_event_rows = other_event_rows[::-1]
                disposition_rows = disposition_rows[::-1]
                case_data["other events and hearings"] = other_event_rows
                case_data["dispositions"] = disposition_rows

                # Note that counsel was waived
                if not case_data["party information"]["appointed or retained"]:
                    if "waiver of right to counsel" in str(other_event_rows).lower():
                        case_data["party information"][
                            "appointed or retained"
                        ] = "Waived right to counsel"
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
                case_data["financial information"] = financial_information
            elif "Location : All Courts" not in table.text and table.text:
                ...
                # print to see if there are sections we are missing in any of the table sections
                # print(table)

        # Write file as json data
        json_str = json.dumps(case_data)
        case_filename = os.path.join(case_json_path, case_id + ".json")
        with open(case_filename, "w") as file_handle:
            file_handle.write(json_str)
    except:
        broken_files.append(case_id)
        with open(broken_json_path, "w") as file_handle:
            file_handle.write(case_id + "\n")

# Print some data for debugging and statistics purposes

RUN_TIME = time() - START_TIME

# from print_stats import case_data_list

# print("\nTime to run script:", round(RUN_TIME, 2), "seconds")
# print(
#     "Milliseconds per case:",
#     int(RUN_TIME / len(case_data_list) * 1000),
#     "ms",
# )

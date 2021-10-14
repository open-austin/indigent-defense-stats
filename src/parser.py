import os
import json
import argparse
from time import time

import pandas
from bs4 import BeautifulSoup

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-overwrite",
    "-o",
    action="store_true",
    help="Switch to overwrite already parsed data.",
)
argparser.description = "Parse data from data/case_html into data/case_json."
args = argparser.parse_args()

# get directories and make json dir if not present
case_html_path = os.path.join("data", "case_html")
case_json_path = os.path.join("data", "case_json")
if not os.path.exists(case_json_path):
    os.mkdir(case_json_path)

# initialize some variables
START_TIME = time()
cached_case_json_list = [
    file_name.split(".")[0] for file_name in os.listdir(case_json_path)
]

# start parsing html files
for case_html_file_name in os.listdir(case_html_path):
    case_id = case_html_file_name.split(".")[0]
    if case_id in cached_case_json_list and not args.overwrite:
        continue
    case_html_file_path = os.path.join(case_html_path, case_html_file_name)
    print(case_html_file_path)
    case_data = {}
    with open(case_html_file_path, "r") as file_handle:
        case_html = file_handle.read().replace("\xa0", " ")
    case_data["osyssey id"] = case_id

    # get the case code
    case_soup = BeautifulSoup(case_html, "html.parser")
    case_data["code"] = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
        0
    ].text

    # header information - name, case type, date filed, location
    df = pandas.read_html(case_html, match="Case Type")
    case_data["name"] = df[0].iloc[0, 0]
    case_data["case type"] = df[2].iloc[0, 1]
    case_data["date filed"] = df[2].iloc[1, 1]
    case_data["location"] = df[2].iloc[2, 1]

    # party information
    df = pandas.read_html(case_html, match="Party Information", keep_default_na=False)[
        0
    ]
    case_data["party information"] = {
        "defendant": {
            "name": df.iloc[1, 1],
            "address and SID": df.iloc[2, 1],
            "race dob height weight": df.iloc[2, 3],
            "attorney info": df.iloc[2, 4],
        },
        "state": {
            "name": df.iloc[4, 1],
            "address": df.iloc[5, 1],
            "attorney info": df.iloc[4, 4],
        },
    }

    # related cases
    try:
        df = pandas.read_html(case_html, match="Related Cases")[0]
        case_data["related cases"] = [
            {
                "case": df.iloc[i, 0].replace("\xa0", " "),
                "reason": df.iloc[i + 1, 0].replace("\xa0", " "),
            }
            for i in range(0, len(df), 2)
        ]
    except:
        ...

    # charge information
    df = pandas.read_html(case_html, match="Charge Information", keep_default_na=False)[
        0
    ]
    case_data["charge information"] = [
        {
            "charge": df.iloc[i, 1],
            "statute": df.iloc[i, 3],
            "level": df.iloc[i, 4],
            "date": df.iloc[i, 5],
        }
        for i in range(0, len(df), 2)
    ]

    # Events & Orders of the Court
    df = pandas.read_html(
        case_html, match="Events & Orders of the Court", keep_default_na=False
    )[0]
    # print(df)

    # Financial Information
    df = pandas.read_html(
        case_html, match="Financial Information", keep_default_na=False
    )[0]

    # print(df)

    # Write file as json data
    json_str = json.dumps(case_data)
    case_filename = os.path.join(case_json_path, case_id + ".json")
    with open(case_filename, "w") as file_handle:
        file_handle.write(json_str)

# Print some data for debugging and statistics purposes
RUN_TIME = time() - START_TIME
from print_stats import case_data_list

print("\nTime to run script:", round(RUN_TIME, 2), "seconds")
print(
    "Milliseconds per case:",
    int(RUN_TIME / len(case_data_list) * 1000),
    "ms",
)

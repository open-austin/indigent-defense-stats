import os
import argparse

import requests
from bs4 import BeautifulSoup

# initialization

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-ms_wait",
    "-w",
    type=int,
    default=200,
    help="Number of ms to wait between requests.",
)
argparser.add_argument(
    "-main_page",
    "-m",
    type=str,
    default="http://public.co.hays.tx.us/",
    help="URL for the main page of the Odyssey site.",
)
argparser.add_argument(
    "-days",
    "-d",
    type=int,
    default=5 * 365,
    help="Number of days to scrape (backwards).",
)
argparser.add_argument(
    "-start_offset",
    "-s",
    type=int,
    default=1,
    help="The number of days ago to start scraping. 1 is Yesterday.",
)
argparser.add_argument(
    "-judicial_officers",
    "-j",
    nargs="*",
    type=str,
    default=[
        "VISITING, JUDGE",
        "Boyer, Bruce",
        "Johnson, Chris",
        "Robison, Jack",
        "Tibbe, Sherri K.",
        "Henry, William R",
        "Steel, Gary L.",
        "Updegrove, Robert",
        "Zelhart, Tacie",
    ],
    help="Judicial Officers to scrape. e.g. -j 'mr. something' 'Rob, Albert'",
)
argparser.description = "Scrape data for list of judicial officers in date range."

args = argparser.parse_args()
if "default.aspx" in args.main_page:
    args.main_page = args.main_page.replace("default.aspx", "")

# Initial setup for the session
session = requests.Session()
main_response = session.get(args.main_page)
main_soup = BeautifulSoup(main_response.text, "html.parser")
calendar_response = session.get(args.main_page + "Search.aspx?ID=900")
calendar_soup = BeautifulSoup(calendar_response.text, "html.parser")
if "Court Calendar" not in calendar_soup.text:
    print("ERROR: Couldn't access Court Calendar page. Quitting.")
    quit()
hidden_values = {
    hidden["name"]: hidden["value"]
    for hidden in calendar_soup.select('input[type="hidden"]')
}
judicial_officer_to_ID = {
    option.text: option["value"]
    for option in calendar_soup.select('select[labelname="Judicial Officer:"] > option')
}
node_info = main_soup.select_one('select[id="sbxControlID2"] > option')
hidden_values.update({"NodeDesc": node_info.text, "NodeID": node_info["value"]})

# make directoriesif not present
if not os.path.exists("data_by_JO"):
    os.mkdir("data_by_JO")
for JO_name in args.judicial_officers:
    JO_path = os.path.join("data_by_JO", JO_name)
    JO_case_path = os.path.join(JO_path, "case_html")
    JO_cal_path = os.path.join(JO_path, "calendar_html")
    if not os.path.exists(JO_path):
        os.mkdir(JO_path)
    if not os.path.exists(JO_case_path):
        os.mkdir(JO_case_path)
    if not os.path.exists(JO_cal_path):
        os.mkdir(JO_cal_path)


# helper function to make form data
def make_form_data(date, JO_id, hidden_values):
    form_data = {}
    form_data.update(hidden_values)
    form_data.update(
        {
            "SearchBy": "3",
            "ExactName": "on",
            "CaseSearchMode": "CaseNumber",
            "CaseSearchValue": "",
            "CitationSearchValue": "",
            "CourtCaseSearchValue": "",
            "PartySearchMode": "Name",
            "AttorneySearchMode": "Name",
            "LastName": "",
            "FirstName": "",
            "cboState": "AA",
            "MiddleName": "",
            "DateOfBirth": "",
            "DriverLicNum": "",
            "CaseStatusType": "0",
            "DateFiledOnAfter": "",
            "DateFiledOnBefore": "",
            "cboJudOffc": JO_id,
            "chkCriminal": "on",
            "chkDtRangeCriminal": "on",
            "chkDtRangeFamily": "on",
            "chkDtRangeCivil": "on",
            "chkDtRangeProbate": "on",
            "chkCriminalMagist": "on",
            "chkFamilyMagist": "on",
            "chkCivilMagist": "on",
            "chkProbateMagist": "on",
            "DateSettingOnAfter": date,
            "DateSettingOnBefore": date,
            "SortBy": "fileddate",
            "SearchSubmit": "Search",
            "SearchType": "JUDOFFC",
            "SearchMode": "JUDOFFC",
            "NameTypeKy": "",
            "BaseConnKy": "",
            "StatusType": "true",
            "ShowInactive": "",
            "AllStatusTypes": "true",
            "CaseCategories": "CR",
            "RequireFirstName": "True",
            "CaseTypeIDs": "",
            "HearingTypeIDs": "",
            # NOTE: `SearchParams` doesn't seem required. Perhaps it's just used for logging?
            # "SearchParams": "SearchBy~~Search By: ~~Judicial Officer~~Judicial Officer | |chkExactName~~Exact Name: ~~on~~on | |cboJudOffc~~Judicial Officer: ~~Arrington, Tamara~~Arrington, Tamara | |DateSettingOnAfter~~Date On or After: ~~8/11/2005~~8/11/2005 | |DateSettingOnBefore~~Date On or Before: ~~8/11/2021~~8/11/2021 | |selectSortBy~~Sort By: ~~Filed Date~~Filed Date | |CaseCategories~~Case Categories: ~~CR~~Criminal",
        }
    )
    return form_data


def write_debug_and_quit(html: str, vars: str):
    print(
        'ERROR: "Date Filed" substring not found in case html page. Aborting.\n',
        "Writing ./debug.html with response and ./debug.txt with current variables.\n",
        vars,
    )
    with open("debug.html", "w") as file_handle:
        file_handle.write(html)
    with open("debug.txt", "w") as file_handle:
        file_handle.write(vars)
    quit()


__all__ = [
    "make_form_data",
    "write_debug_and_quit",
    "args",
    "hidden_values",
    "judicial_officer_to_ID",
    "session",
]

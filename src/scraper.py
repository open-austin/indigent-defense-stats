import os
import argparse
import re
from datetime import datetime, timedelta
from time import sleep, time

import requests
from bs4 import BeautifulSoup

# helper logging function
def write_debug_and_quit(substr: str, html: str, vars: str):
    print(
        f"ERROR: '{substr}' substring not found in html page. Aborting.\n",
        "Writing ./debug.html with response and ./debug.txt with current variables.\n",
        vars,
    )
    with open(os.path.join("data", "debug.html"), "w") as file_handle:
        file_handle.write(html)
    with open(os.path.join("data", "debug.txt"), "w") as file_handle:
        file_handle.write(vars)
    quit()


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


# get command line parmeter info
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
    help="URL for the main page of the Odyssey site. Try to get the whole path with slash up to, but excluding 'default.aspx'",
)
argparser.add_argument(
    "-location",
    "-l",
    type=str,
    default="All Courts",
    help="'Select a location' select box on the main page. Usually 'All Courts' will work.",
)
argparser.add_argument(
    "-calendar_link_text",
    "-c",
    type=str,
    default="Court Calendar",
    help="The text on the main page that you click on to get to your desired calendar. Usually 'Court Calendar' will work.",
)
argparser.add_argument(
    "-days",
    "-d",
    type=int,
    default=7,
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
    default=[],
    help="Judicial Officers to scrape. For example, -j 'mr. something' 'Rob, Albert'. By default, it will scrape all JOs.",
)
argparser.add_argument(
    "-overwrite",
    "-o",
    action="store_true",
    help="Switch to overwrite cached case html, use this when updating your data from a small date range to grab new information.",
)
argparser.description = "Scrape data for list of judicial officers in date range."

args = argparser.parse_args()
# remove default.aspx as a hacky way to accept not-well-formed urls
# TODO: do this in a better way with url parser lib
if "default.aspx" in args.main_page:
    args.main_page = args.main_page.replace("default.aspx", "")
if args.main_page[-1] != "/":
    args.main_page += "/"

# start session
session = requests.Session()
# allow bad ssl
session.verify = False
main_response = session.get(args.main_page)
main_soup = BeautifulSoup(main_response.text, "html.parser")
# get path to the calendar page here
search_page_links = main_soup.select('a[class="ssSearchHyperlink"]')
for link in search_page_links:
    if link.text == args.calendar_link_text:
        search_page_id = link["href"].split("?ID=")[1].split("'")[0]
if not search_page_id:
    print("Couldn't find the Court Calendar page ID. Quitting.")
    quit()
calendar_url = args.main_page + "Search.aspx?ID=" + search_page_id
calendar_response = session.get(calendar_url)
calendar_soup = BeautifulSoup(calendar_response.text, "html.parser")
# See if we got a good response
if "Court Calendar" not in calendar_soup.text:
    write_debug_and_quit("Court Calendar", calendar_soup.text, f"{calendar_url = }")
# we need these hidden values to access the search page
hidden_values = {
    hidden["name"]: hidden["value"]
    for hidden in calendar_soup.select('input[type="hidden"]')
}
# get a list of JOs to their IDs from the search page
judicial_officer_to_ID = {
    option.text: option["value"]
    for option in calendar_soup.select('select[labelname="Judicial Officer:"] > option')
}
# if juidicial_officers param is not specified, use all of them
if not args.judicial_officers:
    args.judicial_officers = list(judicial_officer_to_ID.keys())
# get nodedesc and nodeid information from main page location select box
location_option = main_soup.findAll("option", text=re.compile(args.location))[0]
hidden_values.update({"NodeDesc": args.location, "NodeID": location_option["value"]})

# make cache directories if not present
case_html_path = os.path.join("data", "case_html")
if not os.path.exists("data"):
    os.mkdir("data")
if not os.path.exists(case_html_path):
    os.mkdir(case_html_path)

# initialize some variables
TODAY = datetime.today()
START_TIME = time()
cached_case_html_list = [
    file_name.split(".")[0] for file_name in os.listdir(case_html_path)
]

# days in the past starting with yesterday.
for day_offset in range(args.start_offset, args.days):
    date_string = datetime.strftime(TODAY - timedelta(days=day_offset), "%m/%d/%Y")
    for JO_name in args.judicial_officers:
        # error check and initialize variables for this JO
        if JO_name not in judicial_officer_to_ID:
            print(
                f"ERROR: judicial officer {JO_name} not found on calendar page. Continuing."
            )
            continue
        JO_id = judicial_officer_to_ID[JO_name]
        print(f"Searching cases on {date_string} - {day_offset = } for {JO_name}")
        cal_results = session.post(
            calendar_url,
            data=make_form_data(date_string, JO_id, hidden_values),
        )
        # error check based on text in html result.
        if "Record Count" in cal_results.text:
            # rate limiting - convert ms to seconds
            sleep(args.ms_wait / 1000)
        else:
            curr_vars = f"{day_offset = }\n{JO_name = }\n{date_string = }"
            write_debug_and_quit("Record Count", cal_results.text, curr_vars)

        # read the case URLs from the calendar page html
        cal_soup = BeautifulSoup(cal_results.text, "html.parser")
        case_anchors = cal_soup.select('a[href^="CaseDetail"]')
        print(len(case_anchors), "cases found.")
        # if there are any cases found for this JO and date
        if case_anchors:
            # if all cases are cached, continue
            if all(
                case_anchor["href"].split("=")[1] in cached_case_html_list
                for case_anchor in case_anchors
            ):
                print("All cases are cached for this JO and date.")
                continue

            # process each case
            for case_anchor in case_anchors:
                case_url = args.main_page + case_anchor["href"]
                case_id = case_url.split("=")[1]
                # continue if case is already cached, unless using overwrite flag
                if case_id in cached_case_html_list and not args.overwrite:
                    continue
                case_html_file_path = os.path.join(case_html_path, f"{case_id}.html")

                # make request for the case
                print("Visiting:", case_url)
                case_results = session.get(case_url)
                # error check based on text in html result.
                if "Date Filed" in case_results.text:
                    print("Response string length:", len(case_results.text))
                    with open(case_html_file_path, "w") as file_handle:
                        file_handle.write(case_results.text)
                    # add case id to cached list
                    if case_id not in cached_case_html_list:
                        cached_case_html_list.append(case_id)
                    # rate limiting - convert ms to seconds
                    sleep(args.ms_wait / 1000)
                else:
                    curr_vars = f"{day_offset = }\n{date_string = }\n{JO_name = }\n{case_url = }"
                    write_debug_and_quit("Date Filed", case_results.text, curr_vars)

print("\nTime to run script:", round(time() - START_TIME, 2), "seconds")

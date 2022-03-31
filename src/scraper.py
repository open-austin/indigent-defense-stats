import argparse
from datetime import datetime, timedelta
import logging
import os
import re
import csv
from time import sleep, time
from typing import Any, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(name=__name__)
logging.basicConfig()


# helper logging function
def write_debug_and_quit(substr: str, html: str, vars: str) -> None:
    logger.error(
        f"'{substr}' substring not found in html page. Aborting.\n",
        "Writing ./debug.html with response and ./debug.txt with current variables.\n {vars}",
    )
    with open(os.path.join("data", "debug.html"), "w") as file_handle:
        file_handle.write(html)
    with open(os.path.join("data", "debug.txt"), "w") as file_handle:
        file_handle.write(vars)
    quit()


# helper function to make form data
def make_form_data(
    date: str, JO_id: str, hidden_values: Dict[str, str]
) -> Dict[str, str]:
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


def main() -> None:
    def request_page(
        session: requests.Session,
        url: str,
        verification_text: str,
        data: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
    ) -> Tuple[str, bool]:
        response = ""
        for i in range(max_retries):
            failed = False
            try:
                if data is None:
                    response = session.get(url)
                else:
                    response = session.post(url, data=data)
                response.raise_for_status()
                if verification_text not in response.text:
                    failed = True
                    logger.error(
                        f"Verification text {verification_text} not in response"
                    )
            except requests.RequestException as e:
                logger.exception(f"Failed to get url {url}, try {i}")
                failed = True
            if not failed:
                return response.text, failed
            if i != max_retries - 1:
                sleep(args.ms_wait / 1000)
        return response.text, failed

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
        "-county",
        "-c",
        type=str,
        default="hays",
        help="The name of the county, the main page for their Odyssey install will be grabbed from resources/text_county_data.csv",
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
        "-cal",
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
    argparser.add_argument(
        "-log",
        type=str,
        default="INFO",
        help="Set the level to log at.",
    )
    argparser.description = "Scrape data for list of judicial officers in date range."

    args = argparser.parse_args()

    # set log level
    logging.root.setLevel(level=args.log)

    # make cache directories if not present
    case_html_path = os.path.join("data", "case_html")
    os.makedirs(case_html_path, exist_ok=True)

    # remove default.aspx as a hacky way to accept not-well-formed urls
    # TODO: do this in a better way with url parser lib

    with open(
        os.path.join(
            os.path.dirname(__file__), "..", "resources", "texas_county_data.csv"
        ),
        mode="r",
    ) as file_handle:
        csv_file = csv.DictReader(file_handle)
        main_page = ""
        for row in csv_file:
            if row["county"].lower() == args.county.lower():
                main_page = row["portal"]
                break
        if main_page == "":
            raise ValueError("There is no portal page for this county.")

    # start session
    session = requests.Session()
    # allow bad ssl
    session.verify = False
    main_text, failed = request_page(session, main_page, "ssSearchHyperlink")
    if failed:
        write_debug_and_quit("Main Page", main_text, f"{main_page = }")
    main_soup = BeautifulSoup(main_text, "html.parser")
    # get path to the calendar page here
    search_page_links = main_soup.select('a[class="ssSearchHyperlink"]')
    for link in search_page_links:
        if link.text == args.calendar_link_text:
            search_page_id = link["href"].split("?ID=")[1].split("'")[0]
    if not search_page_id:
        write_debug_and_quit(
            "Couldn't find the Court Calendar page ID. Quitting.", main_text, ""
        )

    calendar_url = main_page + "Search.aspx?ID=" + search_page_id
    calendar_text, failed = request_page(session, calendar_url, "Court Calendar")
    if failed:
        write_debug_and_quit("Court Calendar", calendar_text, f"{calendar_url = }")
    calendar_soup = BeautifulSoup(calendar_text, "html.parser")

    # we need these hidden values to access the search page
    hidden_values = {
        hidden["name"]: hidden["value"]
        for hidden in calendar_soup.select('input[type="hidden"]')
    }
    # get a list of JOs to their IDs from the search page
    judicial_officer_to_ID = {
        option.text: option["value"]
        for option in calendar_soup.select(
            'select[labelname="Judicial Officer:"] > option'
        )
    }
    # if juidicial_officers param is not specified, use all of them
    if not args.judicial_officers:
        args.judicial_officers = list(judicial_officer_to_ID.keys())
    # get nodedesc and nodeid information from main page location select box
    location_option = main_soup.findAll("option", text=re.compile(args.location))[0]
    hidden_values.update(
        {"NodeDesc": args.location, "NodeID": location_option["value"]}
    )

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
                logger.error(
                    f"judicial officer {JO_name} not found on calendar page. Continuing."
                )
                continue
            JO_id = judicial_officer_to_ID[JO_name]
            logger.info(
                f"Searching cases on {date_string} - {day_offset = } for {JO_name}"
            )
            cal_text, failed = request_page(
                session,
                calendar_url,
                "Record Count",
                data=make_form_data(date_string, JO_id, hidden_values),
            )

            if failed:
                write_debug_and_quit(
                    "Record Count",
                    cal_text,
                    f"{day_offset = }\n{JO_name = }\n{date_string = }",
                )

            # rate limiting - convert ms to seconds
            sleep(args.ms_wait / 1000)

            # read the case URLs from the calendar page html
            cal_soup = BeautifulSoup(cal_text, "html.parser")
            case_anchors = cal_soup.select('a[href^="CaseDetail"]')
            logger.info(f"{len(case_anchors)} cases found.")
            # if there are any cases found for this JO and date
            if case_anchors:
                # if all cases are cached, continue
                if (
                    all(
                        case_anchor["href"].split("=")[1] in cached_case_html_list
                        for case_anchor in case_anchors
                    )
                    and not args.overwrite
                ):
                    logger.info("All cases are cached for this JO and date.")
                    continue

                # process each case
                for case_anchor in case_anchors:
                    case_url = main_page + case_anchor["href"]
                    case_id = case_url.split("=")[1]
                    # continue if case is already cached, unless using overwrite flag
                    if case_id in cached_case_html_list and not args.overwrite:
                        continue
                    case_html_file_path = os.path.join(
                        case_html_path, f"{case_id}.html"
                    )

                    # make request for the case
                    logger.info("Visiting: " + case_url)
                    case_results, failed = request_page(session, case_url, "Date Filed")
                    # error check based on text in html result.
                    if not failed:
                        logger.info(f"Response string length: {len(case_results)}")
                        with open(case_html_file_path, "w") as file_handle:
                            file_handle.write(case_results)
                        # add case id to cached list
                        if case_id not in cached_case_html_list:
                            cached_case_html_list.append(case_id)
                    else:
                        curr_vars = f"{day_offset = }\n{date_string = }\n{JO_name = }\n{case_url = }"
                        write_debug_and_quit("Date Filed", case_results, curr_vars)
                    # rate limiting - convert ms to seconds
                    sleep(args.ms_wait / 1000)

    logger.info(f"\nTime to run script: {round(time() - START_TIME, 2)} seconds")


if __name__ == "__main__":
    main()

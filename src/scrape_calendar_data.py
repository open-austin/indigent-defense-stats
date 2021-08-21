import os
import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup

MS_WAIT_PER_REQUEST = 100
DAYS_OF_RECORDS = 5 * 365
TODAY = datetime.datetime.today()

main_page_url = "http://public.co.hays.tx.us/"
# TODO: Might be able to chop off part of this url, need to test
calendar_page_url = "http://public.co.hays.tx.us/Search.aspx?ID=900&NodeID=100,101,102,103,200,201,202,203,204,6112,400,401,402,403,404,405,406,407,6111,6114&NodeDesc=All%20Courts"

# TODO: Find out the timespan when each JO presided.
Judicial_Officer_to_ID = {
    "visiting_officer": "37809",
    "Boyer_Bruce": "39607",
    "Johnson_Chris": "48277",
    "Robison_Jack": "6140",
    "Sherri_Tibbe": "55054",
    "Henry_Bill": "25322",
    "Steel_Gary": "6142",
    "Updegrove_Robert": "38628",
    "Zelhart_Tacie": "48274",
}


def make_form_data(startDate, endDate, jo_id, viewstate):
    return {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": "BBBC20B8",
        "__EVENTVALIDATION": "/wEWAgKEib6eCQKYxoa5CABRE1bdUnTyMmdE4n0IKj4cWw4t",
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
        "cboJudOffc": jo_id,
        "chkCriminal": "on",
        "chkDtRangeCriminal": "on",
        "chkDtRangeFamily": "on",
        "chkDtRangeCivil": "on",
        "chkDtRangeProbate": "on",
        "chkCriminalMagist": "on",
        "chkFamilyMagist": "on",
        "chkCivilMagist": "on",
        "chkProbateMagist": "on",
        "DateSettingOnAfter": startDate,
        "DateSettingOnBefore": endDate,
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


if __name__ == "__main__":
    # Initial setup for the session
    session = requests.Session()
    main_page = session.get(main_page_url)
    # May not be necessary, grabbing viewstate for form data
    calendar_page = session.get(calendar_page_url)
    soup = BeautifulSoup(calendar_page.text, "html.parser")
    viewstate_token = soup.find(id="__VIEWSTATE")["value"]

    # Data dir setup - added this to gitignore for now, may want to remove later
    if not os.path.exists("data_by_JO"):
        os.mkdir("data_by_JO")
    for JO_name in Judicial_Officer_to_ID.keys():
        JO_path = os.path.join("data_by_JO", JO_name)
        JO_cal_path = os.path.join(JO_path, "calendar_html")
        if not os.path.exists(JO_path):
            os.mkdir(JO_path)
        if not os.path.exists(JO_cal_path):
            os.mkdir(JO_cal_path)

    # Days in the past starting with yesterday.
    for DAY_OFFSET in range(1, DAYS_OF_RECORDS):
        date_string = datetime.datetime.strftime(
            TODAY - datetime.timedelta(days=DAY_OFFSET), format="%m/%d/%Y"
        )
        file_name = f"{date_string.replace('/','-')}.html"
        for JO_name, JO_id in Judicial_Officer_to_ID.items():
            print(f"Capturing data for JO: {JO_name} on {date_string}")
            cal_html_file_path = os.path.join(
                "data_by_JO", JO_name, "calendar_html", file_name
            )
            # Check if the file is already cached before requesting
            if not os.path.exists(cal_html_file_path):
                cal_results = session.post(
                    calendar_page_url,
                    data=make_form_data(
                        date_string, date_string, JO_id, viewstate_token
                    ),
                )
                # Error check based on text in html result.
                if "Record Count" in cal_results.text:
                    print(f"Writing file: {cal_html_file_path}")
                    with open(cal_html_file_path, "w") as file_handle:
                        file_handle.write(cal_results.text)
                    # Rate limiting - convert ms to seconds
                    sleep(MS_WAIT_PER_REQUEST / 1000)
                else:
                    print(
                        f'ERROR: "Record Count" substring not found in calendar html page. Aborting. Writing ./debug.html'
                    )
                    with open("debug.html", "w") as file_handle:
                        file_handle.write(cal_results.text)
                    quit()
            else:
                print("Data is already cached. Skipping.")

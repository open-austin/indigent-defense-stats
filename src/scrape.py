import os
import datetime as dt
import requests as r

from time import sleep

from bs4 import BeautifulSoup as bs

s = r.Session()

MS_WAIT_PER_REQUEST = 100
DAYS_OF_RECORDS = 5*365

main_page_url = "http://public.co.hays.tx.us/"
calendar_page_url = "http://public.co.hays.tx.us/Search.aspx?ID=900&NodeID=100,101,102,103,200,201,202,203,204,6112,400,401,402,403,404,405,406,407,6111,6114&NodeDesc=All%20Courts"

main_page = s.get(main_page_url)
calendar_page = s.get(calendar_page_url)

soup = bs(calendar_page.text, "html.parser")
viewstate = soup.find(id="__VIEWSTATE")["value"]

# TODO: Find out the timespan when each JO presided.
judicial_officers = {
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

# Data dir setup - added this to gitignore for now, may want to remove later
if not os.path.exists("case_data"):
    os.mkdir("case_data")
for JO_name in judicial_officers.keys():
    data_path = os.path.join("case_data", JO_name)
    if not os.path.exists(data_path):
        os.mkdir(data_path)


def mk_cal_results_form_data(startDate, endDate, jo_id):
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


today = dt.datetime.today()

for daysago in range(1, DAYS_OF_RECORDS):
    date_string = dt.datetime.strftime(
        today - dt.timedelta(days=daysago), format="%m/%d/%Y"
    )
    file_name = f"{date_string.replace('/','-')}.html"
    for JO_name, JO_id in judicial_officers.items():
        data_file_path = os.path.join("case_data", JO_name, file_name)
        # check if the file is already cached before requesting
        print(f"Capturing data for JO: {JO_name} on {date_string}")
        if not os.path.exists(data_file_path):
            form_data = mk_cal_results_form_data(date_string, date_string, JO_id)
            cal_results = s.post(calendar_page_url, data=form_data)
            # TODO: add check on response page content to see if we got an error.
            # for now, just print the length so the user can have some guess if there is an error.
            print(f"String length of html page output: {len(cal_results.text)}")
            with open(data_file_path, "w") as fh:
                fh.write(cal_results.text)
            
            # Rate limiting - convert to seconds
            sleep(MS_WAIT_PER_REQUEST / 1000) 
        else:
            print("Exists.")
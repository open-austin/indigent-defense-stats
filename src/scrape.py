import os
import datetime as dt
import requests as r

from bs4 import BeautifulSoup as bs

s = r.Session()

main_page_url = "http://public.co.hays.tx.us/"
calendar_page_url = "http://public.co.hays.tx.us/Search.aspx?ID=900&NodeID=100,101,102,103,200,201,202,203,204,6112,400,401,402,403,404,405,406,407,6111,6114&NodeDesc=All%20Courts"

main_page = s.get(main_page_url)
calendar_page = s.get(calendar_page_url)

soup = bs(calendar_page.text)
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

for daysago in range(5):
    date_string = dt.datetime.strftime(
        today - dt.timedelta(days=daysago), format="%-m/%-d/%Y")

    print(date_string)

    data = mk_cal_results_form_data("07/21/2021", date_string, "55054")

    cal_results = s.post(
        calendar_page_url, data=data)

    output_root = "data/by_judicial_officer/"

    folder_path = os.path.join("data/by_judicial_officer/", "Tibee_Sherri")

    filename = os.path.join(
        folder_path, f"{date_string.replace('/','-')}.html")

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    # We thought `w+` would write the file even if the path didn't exist, but alas..
    with open(filename, "w") as file:
        file.write(cal_results.text)


# cal_results = s.post(calendar_page_url, data=cal_results_form_data)

# print(req.text)
# print(req.headers)
# print(cal_results.text)
# print(viewstate)

# with open("test2.html", "w") as fh:
#     fh.write(cal_results.text)

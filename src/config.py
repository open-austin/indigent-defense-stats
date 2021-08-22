import os
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "--ms_wait",
    "--w",
    type=int,
    default=200,
    help="Number of ms to wait between requests.",
)
argparser.add_argument(
    "--main_page",
    "--m",
    type=str,
    default="http://public.co.hays.tx.us/",
    help="URL for the main page of the Odyssey site.",
)
argparser.add_argument(
    "--calendar_page",
    "--c",
    type=str,
    default="http://public.co.hays.tx.us/Search.aspx?ID=900&NodeID=100,101,102,103,200,201,202,203,204,6112,400,401,402,403,404,405,406,407,6111,6114&NodeDesc=All%20Courts",
    help="URL for the calendar page of the Odyssey site.",
)

# TODO: Find out the timespan when each JO presided?
judicial_officer_to_ID = {
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


def make_form_data(date, JO_id, viewstate_token):
    return {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate_token,
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


# Make all data folders if they don't exist
if not os.path.exists("data_by_JO"):
    os.mkdir("data_by_JO")
for JO_name in judicial_officer_to_ID.keys():
    JO_path = os.path.join("data_by_JO", JO_name)
    JO_case_path = os.path.join(JO_path, "case_html")
    JO_cal_path = os.path.join(JO_path, "calendar_html")
    if not os.path.exists(JO_path):
        os.mkdir(JO_path)
    if not os.path.exists(JO_case_path):
        os.mkdir(JO_case_path)
    if not os.path.exists(JO_cal_path):
        os.mkdir(JO_cal_path)

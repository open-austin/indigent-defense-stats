import os
import argparse

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


def setup_directories(judicial_officers):
    if not os.path.exists("data_by_JO"):
        os.mkdir("data_by_JO")
    for JO_name in judicial_officers:
        JO_path = os.path.join("data_by_JO", JO_name)
        JO_case_path = os.path.join(JO_path, "case_html")
        JO_cal_path = os.path.join(JO_path, "calendar_html")
        if not os.path.exists(JO_path):
            os.mkdir(JO_path)
        if not os.path.exists(JO_case_path):
            os.mkdir(JO_case_path)
        if not os.path.exists(JO_cal_path):
            os.mkdir(JO_cal_path)

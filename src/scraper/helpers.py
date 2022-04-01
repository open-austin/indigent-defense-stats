import os
import requests
from time import sleep
from logging import Logger
from typing import Any, Dict, Optional, Tuple


def write_debug_and_quit(substr: str, html: str, vars: str, logger: Logger) -> None:
    logger.error(
        f"'{substr}' could not be found in html page. Aborting.\n",
        "Writing ./debug.html with response and ./debug.txt with current variables.\n {vars}",
    )
    with open(os.path.join("data", "debug.html"), "w") as file_handle:
        file_handle.write(html)
    with open(os.path.join("data", "debug.txt"), "w") as file_handle:
        file_handle.write(vars)
    quit()


# helper function to make form data
def create_search_form_data(
    date: str, JO_id: str, hidden_values: Dict[str, str], odyssey_version: int
) -> Dict[str, str]:
    form_data = {}
    form_data.update(hidden_values)
    if odyssey_version < 2017:
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
            }
        )
    else:
        form_data.update(
            {
                "SearchCriteria.SelectedHearingType": "Criminal+Hearing+Types",
                "SearchCriteria.SearchByType": "JudicialOfficer",
                "SearchCriteria.SelectedJudicialOfficer": JO_id,
                "SearchCriteria.DateFrom": date,
                "SearchCriteria.DateTo": date,
            }
        )

    return form_data


def request_page_with_retry(
    session: requests.Session,
    url: str,
    verification_text: str,
    logger: Logger,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, str]] = None,
    max_retries: int = 5,
    ms_wait: str = 200,
) -> Tuple[str, bool]:
    response = ""
    for i in range(max_retries):
        failed = False
        try:
            if not data and not headers:
                response = session.post(url)
            elif not data:
                response = session.post(url, headers=headers)
            elif not headers:
                response = session.post(url, data=data)
            else:
                response = session.post(url, data=data, headers=headers)
            response.raise_for_status()
            if verification_text not in response.text:
                failed = True
                logger.error(f"Verification text {verification_text} not in response")
        except requests.RequestException as e:
            logger.exception(f"Failed to get url {url}, try {i}")
            failed = True
        if not failed:
            return response.text, failed
        if i != max_retries - 1:
            sleep(ms_wait / 1000)
    return response.text, failed


def create_header_data():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Origin": "https://jpodysseyportal.harriscountytx.gov",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        # TODO: figure out which headers are needed
        # "Referer": "https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Home/Dashboard/26",  # ?
        # "Cookie": "", # ?
    }

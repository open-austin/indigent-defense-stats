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
        }
    )
    return form_data


def request_page_with_retry(
    session: requests.Session,
    url: str,
    verification_text: str,
    logger: Logger,
    data: Optional[Dict[str, Any]] = None,
    max_retries: int = 5,
    ms_wait: str = 200,
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
                logger.error(f"Verification text {verification_text} not in response")
        except requests.RequestException as e:
            logger.exception(f"Failed to get url {url}, try {i}")
            failed = True
        if not failed:
            return response.text, failed
        if i != max_retries - 1:
            sleep(ms_wait / 1000)
    return response.text, failed

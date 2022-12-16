import os, sys
import requests
from time import sleep
from datetime import date
from logging import Logger
from typing import Dict, Optional, Tuple, Literal
from enum import Enum


def write_debug_and_quit(
    page_text: str, logger: Logger, verification_text: Optional[str] = None
) -> None:
    logger.error(
        (
            f"{verification_text} could not be found in page."
            if verification_text
            else "Failed to load page."
        )
        + f" Aborting. Writing /data/debug.html with response. May not be HTML."
    )
    with open(os.path.join("data", "debug.html"), "w") as file_handle:
        file_handle.write(page_text)
    sys.exit(1)


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
                "cboJudOffc": JO_id,
                "DateSettingOnAfter": date,
                "DateSettingOnBefore": date,
                "SearchType": "JUDOFFC",  # Search by Judicial Officer
                "SearchMode": "JUDOFFC",
                "CaseCategories": "CR",  # "CR,CV,FAM,PR" criminal, civil, family, probate and mental health - these are the options
            }
        )
    else:
        form_data.update(
            {
                "SearchCriteria.SelectedHearingType": "Criminal Hearing Types",
                "SearchCriteria.SearchByType": "JudicialOfficer",
                "SearchCriteria.SelectedJudicialOfficer": JO_id,
                "SearchCriteria.DateFrom": date,
                "SearchCriteria.DateTo": date,
            }
        )
    return form_data

def create_single_case_search_form_data(hidden_values: Dict[str, str]):
    form_data = {}
    form_data.update(hidden_values)
    os_specific_time_format = "%#m/%#d/%Y" if os.name == 'nt' else "%-m/%-d/%Y"
    form_data.update(
        {
            "SearchBy": "0",
            "DateSettingOnAfter": "1/1/1970",
            "DateSettingOnBefore": date.today().strftime(os_specific_time_format),
            "SearchType": "CASE",  # Search by case id
            "SearchMode": "CASENUMBER",
            "CaseCategories": "",
        }
    )
    return form_data


class HTTPMethod(Enum):
    POST: int = 1
    GET: int = 2


def request_page_with_retry(
    session: requests.Session,
    url: str,
    logger: Logger,
    verification_text: Optional[str] = None,
    http_method: Literal[HTTPMethod.POST, HTTPMethod.GET] = HTTPMethod.POST,
    params: Dict[str, str] = {},
    data: Optional[Dict[str, str]] = None,
    max_retries: int = 5,
    ms_wait: str = 200,
) -> Tuple[str, bool]:
    response = None
    for i in range(max_retries):
        sleep(ms_wait / 1000 * (i + 1))
        failed = False
        try:
            if http_method == HTTPMethod.POST:
                if not data:
                    response = session.post(url, params=params)
                else:
                    response = session.post(url, data=data, params=params)
            elif http_method == HTTPMethod.GET:
                if not data:
                    response = session.get(url, params=params)
                else:
                    response = session.get(url, data=data, params=params)
            response.raise_for_status()
            print(response.text)
            if verification_text:
                if verification_text not in response.text:
                    failed = True
                    logger.error(
                        f"Verification text {verification_text} not in response"
                    )
        except requests.RequestException as e:
            logger.exception(f"Failed to get url {url}, try {i}")
            failed = True
        if failed:
            write_debug_and_quit(
                verification_text=verification_text,
                page_text=response.text,
                logger=logger,
            )
    return response.text

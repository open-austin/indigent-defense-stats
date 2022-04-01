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


from enum import Enum
from typing import Literal


class HTTPMethod(Enum):
    POST: int = 1
    GET: int = 2


def request_page_with_retry(
    session: requests.Session,
    url: str,
    verification_text: str,
    logger: Logger,
    http_method: Literal[HTTPMethod.POST, HTTPMethod.GET] = HTTPMethod.POST,
    data: Optional[Dict[str, str]] = None,
    max_retries: int = 5,
    ms_wait: str = 200,
) -> Tuple[str, bool]:
    response = ""
    for i in range(max_retries):
        sleep(ms_wait / 1000)
        failed = False
        try:
            if http_method == HTTPMethod.POST:
                if not data:
                    response = session.post(url)
                else:
                    response = session.post(url, data=data)
            elif http_method == HTTPMethod.GET:
                if not data:
                    response = session.get(url)
                else:
                    response = session.get(url, data=data)
            response.raise_for_status()
            if verification_text not in response.text:
                failed = True
                logger.error(f"Verification text {verification_text} not in response")
        except requests.RequestException as e:
            logger.exception(f"Failed to get url {url}, try {i}")
            failed = True
        if not failed:
            return response.text, failed
    return response.text, failed

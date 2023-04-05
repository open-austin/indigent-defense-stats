import logging, os, urllib.parse, json
from datetime import datetime, timedelta
from time import time

from bs4 import BeautifulSoup

from helpers import *

logger = logging.getLogger(name=str(os.getpid()))


def scrape(session, base_url, logger, args, case_html_path):
    # hit the search page to gather initial data
    search_page_html = request_page_with_retry(
        session=session,
        url=urllib.parse.urljoin(base_url, "Home/Dashboard/26"),
        verification_text="SearchCriteria.SelectedCourt",
        http_method=HTTPMethod.GET,
        logger=logger,
        ms_wait=args.ms_wait,
    )
    search_soup = BeautifulSoup(search_page_html, "html.parser")

    # we need these hidden values to POST a search
    hidden_values = {
        hidden["name"]: hidden["value"]
        for hidden in search_soup.select('input[type="hidden"]')
        if hidden.has_attr("name")
    }
    # get more hidden values
    hidden_values["SearchCriteria.SelectedCourt"] = hidden_values[
        "Settings.DefaultLocation"
    ]  # TODO: Search in default court. Might need to add further logic later to loop through courts.

    # Individual case search logic
    if args.case_number:
        # totally untested path
        exit

    # get a list of JOs to their IDs from the search page
    judicial_officer_to_ID = {
        option.text: option["value"]
        for option in search_soup.select('select[id="selHSJudicialOfficer"] > option')
        if option.text
    }
    # if juidicial_officers param is not specified, use all of them
    if not args.judicial_officers:
        args.judicial_officers = list(judicial_officer_to_ID.keys())

    # initialize variables to time script and build a list of already scraped cases
    START_TIME = time()
    cached_case_list = [
        file_name.split(".")[0] for file_name in os.listdir(case_html_path)
    ]

    # loop through each day
    for date in (
        args.start_date + timedelta(n)
        for n in range((args.end_date - args.start_date).days + 1)
    ):
        date_string = datetime.strftime(date, "%m/%d/%Y")
        # loop through each judicial officer
        for JO_name in args.judicial_officers:
            if JO_name not in judicial_officer_to_ID:
                logger.error(
                    f"judicial officer {JO_name} not found on search page. Continuing."
                )
                continue
            JO_id = judicial_officer_to_ID[JO_name]
            logger.info(f"Searching cases on {date_string} for {JO_name}")
            # POST a request for search results
            results_page_html = request_page_with_retry(
                session=session,
                url=urllib.parse.urljoin(
                    base_url, "Hearing/SearchHearings/HearingSearch"
                ),
                verification_text="Search Results",
                logger=logger,
                data=create_search_form_data_post2017(
                    date_string, JO_id, hidden_values
                ),
                ms_wait=args.ms_wait,
            )

            # Need to POST this page to get a JSON of the search results after the initial POST
            case_list_json = request_page_with_retry(
                session=session,
                url=urllib.parse.urljoin(base_url, "Hearing/HearingResults/Read"),
                verification_text="AggregateResults",
                logger=logger,
            )
            case_list_json = json.loads(case_list_json)
            logger.info(f"{case_list_json['Total']} cases found")
            for case_json in case_list_json["Data"]:
                case_id = str(case_json["CaseId"])
                if case_id in cached_case_list and not args.overwrite:
                    logger.info(f"{case_id} already scraped case")
                    continue
                logger.info(f"{case_id} scraping case")
                # make request for the case
                case_html = request_page_with_retry(
                    session=session,
                    url=urllib.parse.urljoin(base_url, "Case/CaseDetail"),
                    verification_text="Case Information",
                    logger=logger,
                    ms_wait=args.ms_wait,
                    params={
                        "eid": case_json["EncryptedCaseId"],
                        "CaseNumber": case_json["CaseNumber"],
                    },
                )
                # make request for financial info
                case_html += request_page_with_retry(
                    session=session,
                    url=urllib.parse.urljoin(
                        base_url, "Case/CaseDetail/LoadFinancialInformation"
                    ),
                    verification_text="Financial",
                    logger=logger,
                    ms_wait=args.ms_wait,
                    params={
                        "caseId": case_json["CaseId"],
                    },
                )
                # write case html data
                logger.info(f"{len(case_html)} response string length")
                with open(
                    os.path.join(case_html_path, f"{case_id}.html"), "w"
                ) as file_handle:
                    file_handle.write(case_html)
                if case_id not in cached_case_list:
                    cached_case_list.append(case_id)
                if args.test:
                    logger.info("Testing, stopping after first case")
                    sys.exit()

    logger.info(f"\nTime to run script: {round(time() - START_TIME, 2)} seconds")

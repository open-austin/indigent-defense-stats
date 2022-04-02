import logging, os, re, csv, urllib.parse, json
from arguments import args
from datetime import datetime, timedelta
from time import time

from helpers import *
from arguments import args  # argument settings here

import requests
from bs4 import BeautifulSoup


def main() -> None:
    # disable SSL warnings
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )

    # start session
    session = requests.Session()
    # allow bad ssl
    session.verify = False

    # set up logger
    logging.root.setLevel(level=args.log)
    logger = logging.getLogger(name="pid: " + str(os.getpid()))
    logging.basicConfig()

    # make cache directories if not present
    case_html_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", args.county, "case_html"
    )
    os.makedirs(case_html_path, exist_ok=True)

    # get county portal and version year information from csv file
    main_page = ""
    odyssey_version = ""
    base_page = ""
    with open(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "resources", "texas_county_data.csv"
        ),
        mode="r",
    ) as file_handle:
        csv_file = csv.DictReader(file_handle)
        for row in csv_file:
            if row["county"].lower() == args.county.lower():
                main_page = row["portal"]
                odyssey_version = int(row["version"].split(".")[0])
                parsed_url = urllib.parse.urlparse(main_page)
                base_page = parsed_url.scheme + "://" + parsed_url.netloc
                break
        if main_page == "":
            raise ValueError("There is no portal page for this county.")

    # start scraping
    main_page_html = request_page_with_retry(
        session=session,
        url=main_page,
        verification_text="ssSearchHyperlink"
        if odyssey_version < 2017
        else "SearchCriteria.SelectedCourt",
        logger=logger,
        http_method=HTTPMethod.GET,
        ms_wait=args.ms_wait,
    )
    main_soup = BeautifulSoup(main_page_html, "html.parser")

    # Visit the search page to gather hidden values
    if odyssey_version < 2017:
        search_page_links = main_soup.select("a.ssSearchHyperlink")
        search_page_id = None
        for link in search_page_links:
            if link.text == "Court Calendar":
                search_page_id = link["href"].split("?ID=")[1].split("'")[0]
        if not search_page_id:
            write_debug_and_quit("Court Calendar link", main_page_html, logger)
        search_url = main_page + "Search.aspx?ID=" + search_page_id

        search_page_html = request_page_with_retry(
            session=session,
            url=search_url,
            verification_text="Court Calendar",
            logger=logger,
            ms_wait=args.ms_wait,
        )
        search_soup = BeautifulSoup(search_page_html, "html.parser")
    else:
        search_soup = main_soup

    # we need these hidden values to access the search page
    hidden_values = {
        hidden["name"]: hidden["value"]
        for hidden in search_soup.select('input[type="hidden"]')
        if hidden.has_attr("name")
    }
    # get nodedesc and nodeid information from main page location select box
    if odyssey_version < 2017:
        location_option = main_soup.findAll("option", text=re.compile(args.location))[0]
        hidden_values.update(
            {"NodeDesc": args.location, "NodeID": location_option["value"]}
        )
    else:
        hidden_values["SearchCriteria.SelectedCourt"] = hidden_values[
            "Settings.DefaultLocation"
        ]  # TODO: Search in default court. Might need to add further logic later to loop through courts.

    # get a list of JOs to their IDs from the search page
    judicial_officer_to_ID = {
        option.text: option["value"]
        for option in search_soup.select(
            'select[labelname="Judicial Officer:"] > option'
            if odyssey_version < 2017
            else 'select[id="selHSJudicialOfficer"] > option'
        )
        if option.text
    }
    # if juidicial_officers param is not specified, use all of them
    if not args.judicial_officers:
        args.judicial_officers = list(judicial_officer_to_ID.keys())

    # initialize some variables
    START_TIME = time()
    cached_case_list = [
        file_name.split(".")[0] for file_name in os.listdir(case_html_path)
    ]
    day_count = args.end_date - args.start_date
    day_count = day_count.days

    # days in the past starting with yesterday.
    for date_to_process in (args.start_date + timedelta(n) for n in range(day_count)):
        date_string = datetime.strftime(date_to_process, "%m/%d/%Y")
        for JO_name in args.judicial_officers:
            # error check and initialize variables for this JO
            if JO_name not in judicial_officer_to_ID:
                logger.error(
                    f"judicial officer {JO_name} not found on search page. Continuing."
                )
                continue
            JO_id = judicial_officer_to_ID[JO_name]
            logger.info(f"Searching cases on {date_string} for {JO_name}")
            results_page_html = request_page_with_retry(
                session=session,
                url=search_url
                if odyssey_version < 2017
                else urllib.parse.urljoin(
                    base_page, "OdysseyPortalJP/Hearing/SearchHearings/HearingSearch"
                ),
                verification_text="Record Count"
                if odyssey_version < 2017
                else "Search Results",
                logger=logger,
                data=create_search_form_data(
                    date_string, JO_id, hidden_values, odyssey_version
                ),
                ms_wait=args.ms_wait,
            )
            results_soup = BeautifulSoup(results_page_html, "html.parser")

            # different process for getting case data for pre and post 2017
            if odyssey_version < 2017:
                case_urls = [
                    main_page + anchor["href"]
                    for anchor in results_soup.select('a[href^="CaseDetail"]')
                ]
                logger.info(f"{len(case_urls)} cases found.")
                for case_url in case_urls:
                    case_id = case_url.split("=")[1]
                    if case_id in cached_case_list and not args.overwrite:
                        logger.info(f"{case_id} - already scraped")
                        continue
                    case_html_file_path = os.path.join(
                        case_html_path, f"{case_id}.html"
                    )

                    # make request for the case
                    logger.info(f"{case_id} - scraping")
                    case_html = request_page_with_retry(
                        session=session,
                        url=case_url,
                        verification_text="Date Filed",
                        logger=logger,
                        ms_wait=args.ms_wait,
                    )
                    # error check based on text in html result.
                    logger.info(f"Response string length: {len(case_html)}")
                    with open(case_html_file_path, "w") as file_handle:
                        file_handle.write(case_html)
                    # add case id to cached list
                    if case_id not in cached_case_list:
                        cached_case_list.append(case_id)
            else:
                case_list_json = request_page_with_retry(
                    session=session,
                    url=urllib.parse.urljoin(
                        base_page, "OdysseyPortalJP/Hearing/HearingResults/Read"
                    ),
                    verification_text="AggregateResults",
                    logger=logger,
                )
                case_list_json = json.loads(case_list_json)
                logger.info(f"{case_list_json['Total']} cases found.")
                for case_json in case_list_json["Data"]:
                    case_id = case_json["CaseId"]
                    if case_id in cached_case_list and not args.overwrite:
                        logger.info(f"{case_id} - already scraped")
                        continue
                    case_html_file_path = os.path.join(
                        case_html_path, f"{case_id}.html"
                    )

                    # make request for the case
                    logger.info(f"{case_id} - scraping")
                    params = {
                        "eid": case_json["EncryptedCaseId"],
                        "CaseNumber": case_json["CaseNumber"],
                    }
                    case_html = request_page_with_retry(
                        session=session,
                        url="https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Case/CaseDetail",
                        verification_text="Case Information",
                        logger=logger,
                        ms_wait=args.ms_wait,
                        params=params,
                    )

                    params = {
                        "caseId": case_json["CaseId"],
                    }

                    financial_html = request_page_with_retry(
                        session=session,
                        url="https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Case/CaseDetail/LoadFinancialInformation",
                        verification_text="Financial",
                        logger=logger,
                        ms_wait=args.ms_wait,
                        params=params,
                    )
                    logger.info(
                        f"Response string length: {len(case_html + financial_html)}"
                    )
                    with open(case_html_file_path, "w") as file_handle:
                        file_handle.write(case_html + financial_html)
                    # add case id to cached list
                    if case_id not in cached_case_list:
                        cached_case_list.append(case_id)

    logger.info(f"\nTime to run script: {round(time() - START_TIME, 2)} seconds")


if __name__ == "__main__":
    main()

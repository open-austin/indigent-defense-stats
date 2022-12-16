import logging, os, re, csv, urllib.parse, json
from arguments import args
from datetime import datetime, timedelta
from time import time

import requests
from bs4 import BeautifulSoup

from helpers import *
from arguments import args  # argument settings here

session = requests.Session()
# allow bad ssl and turn off warnings
session.verify = False
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

logger = logging.getLogger(name="pid: " + str(os.getpid()))
logging.basicConfig()
logging.root.setLevel(level=args.log)

# make cache directories if not present
case_html_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", args.county, "case_html"
)
os.makedirs(case_html_path, exist_ok=True)

# get county portal and version year information from csv file
base_url = odyssey_version = notes = None
with open(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "resources", "texas_county_data.csv"
    ),
    mode="r",
) as file_handle:
    csv_file = csv.DictReader(file_handle)
    for row in csv_file:
        if row["county"].lower() == args.county.lower():
            base_url = row["portal"]
            # add trailing slash if not present, otherwise urljoin breaks
            if base_url[-1] != "/":
                base_url += "/"
            logger.info(f"{base_url} - scraping this url")
            odyssey_version = int(row["version"].split(".")[0])
            notes = row["notes"]
            break
if not base_url or not odyssey_version:
    raise Exception(
        "The required data to scrape this county is not in ./resources/texas_county_data.csv"
    )

# if odyssey_version < 2017, scrape main page first to get necessary data
if odyssey_version < 2017:
    # some sites have a public guest login that must be used
    if "PUBLICLOGIN#" in notes:
        userpass = notes.split("#")[1].split("/")

        data = {
            "UserName": userpass[0],
            "Password": userpass[1],
            "ValidateUser": "1",
            "dbKeyAuth": "Justice",
            "SignOn": "Sign On",
        }

        response = request_page_with_retry(
            session=session,
            url=urllib.parse.urljoin(base_url, "login.aspx"),
            logger=logger,
            http_method=HTTPMethod.GET,
            ms_wait=args.ms_wait,
            data=data,
        )

    main_page_html = request_page_with_retry(
        session=session,
        url=base_url,
        verification_text="ssSearchHyperlink",
        logger=logger,
        http_method=HTTPMethod.GET,
        ms_wait=args.ms_wait,
    )
    main_soup = BeautifulSoup(main_page_html, "html.parser")
    # build url for court calendar
    search_page_id = None
    for link in main_soup.select("a.ssSearchHyperlink"):
        if args.court_calendar_link_text in link.text:
            search_page_id = link["href"].split("?ID=")[1].split("'")[0]
    if not search_page_id:
        write_debug_and_quit(
            verification_text="Court Calendar link",
            page_text=main_page_html,
            logger=logger,
        )
    search_url = base_url + "Search.aspx?ID=" + search_page_id

# hit the search page to gather initial data
search_page_html = request_page_with_retry(
    session=session,
    url=search_url
    if odyssey_version < 2017
    else urllib.parse.urljoin(base_url, "Home/Dashboard/26"),
    verification_text="Court Calendar"
    if odyssey_version < 2017
    else "SearchCriteria.SelectedCourt",
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
# get nodedesc and nodeid information from main page location select box
if odyssey_version < 2017:
    if args.location:
        # TODO: Made this properly sleect based on args.location
        location_option = main_soup.findAll("option")[0]
    else:
        location_option = main_soup.findAll("option")[0]
    logger.info(f"location: {location_option.text}")
    hidden_values.update(
        {"NodeDesc": location_option.text, "NodeID": location_option["value"]}
    )
else:
    hidden_values["SearchCriteria.SelectedCourt"] = hidden_values[
        "Settings.DefaultLocation"
    ]  # TODO: Search in default court. Might need to add further logic later to loop through courts.

# Individual case search logic
if args.case_number:
    # POST a request for search results
    results_page_html = request_page_with_retry(
        session=session,
        url=search_url,
        verification_text="Record Count",
        logger=logger,
        data=create_single_case_search_form_data(hidden_values, args.case_number),
        ms_wait=args.ms_wait,
    )
    results_soup = BeautifulSoup(results_page_html, "html.parser")
    case_urls = [
        base_url + anchor["href"]
        for anchor in results_soup.select('a[href^="CaseDetail"]')
    ]
    logger.info(f"{len(case_urls)} entries found")
    case_id = case_urls[0].split("=")[1]
    logger.info(f"{case_id} - scraping case")
    # make request for the case
    case_html = request_page_with_retry(
        session=session,
        url=case_urls[0],
        verification_text="Date Filed",
        logger=logger,
        ms_wait=args.ms_wait,
    )
    # write html case data
    logger.info(f"{len(case_html)} response string length")
    with open(
        os.path.join(case_html_path, f"{case_id}.html"), "w"
    ) as file_handle:
        file_handle.write(case_html)
    quit()

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

# initialize variables to time script and build a list of already scraped cases
START_TIME = time()
cached_case_list = [file_name.split(".")[0] for file_name in os.listdir(case_html_path)]

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
            url=search_url
            if odyssey_version < 2017
            else urllib.parse.urljoin(base_url, "Hearing/SearchHearings/HearingSearch"),
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

        # different process for getting case data for pre and post 2017 Odyssey versions
        if odyssey_version < 2017:
            case_urls = [
                base_url + anchor["href"]
                for anchor in results_soup.select('a[href^="CaseDetail"]')
            ]
            logger.info(f"{len(case_urls)} cases found")
            for case_url in case_urls:
                case_id = case_url.split("=")[1]
                if case_id in cached_case_list and not args.overwrite:
                    logger.info(f"{case_id} - already scraped case")
                    continue
                logger.info(f"{case_id} - scraping case")
                # make request for the case
                case_html = request_page_with_retry(
                    session=session,
                    url=case_url,
                    verification_text="Date Filed",
                    logger=logger,
                    ms_wait=args.ms_wait,
                )
                # write html case data
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
        else:
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

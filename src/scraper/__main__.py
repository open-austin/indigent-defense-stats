import logging, os, re, csv, urllib.parse, json, sys
from datetime import datetime, timedelta
from time import time
import requests
from bs4 import BeautifulSoup
from .helpers import *

class scraper:

    def __init__(self, county = 'hays', start_date = '2024-07-01', end_date = '2024-07-01', case_number = None):
        self.county = county.lower()
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        self.ms_wait = 200 #"Number of ms to wait between requests."
        self.judicial_officers = [] #"Judicial Officers to scrape. For example, -j 'mr. something' 'Rob, Albert'. By default, it will scrape all JOs.",
        self.no_overwrite = False #"Switch to don't overwrite cached html files if you want to speed up the process (but may not get the most up to date version).",
        self.log = "INFO" #"Set the level to log at.",
        self.court_calendar_link_text ="Court Calendar" #"This is the link to the Court Calendar search page at default.aspx, usually it will be 'Court Calendar', but some sites have multiple calendars e.g. Williamson",
        self.test = False #"If this parameter is present, the script will stop after the first case is scraped.",
        self.case_number = case_number #"If a case number is entered, only that single case is scraped. ex. 12-2521CR",
        self.location = False

        self.session = requests.Session()
        # allow bad ssl and turn off warnings
        self.session.verify = False
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )
        self.logger = logging.getLogger(name="pid: " + str(os.getpid()))
        logging.basicConfig()
        logging.root.setLevel(level=self.log)

        # make cache directories if not present
        self.case_html_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", self.county, "case_html"
        )
        os.makedirs(self.case_html_path, exist_ok=True)

    def scrape(self):

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
                if row["county"].lower() == self.county.lower():
                    base_url = row["portal"]
                    # add trailing slash if not present, otherwise urljoin breaks
                    if base_url[-1] != "/":
                        base_url += "/"
                    self.logger.info(f"{base_url} - scraping this url")
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
                    session=self.session,
                    url=urllib.parse.urljoin(base_url, "login.aspx"),
                    logger=self.logger,
                    http_method=HTTPMethod.GET,
                    ms_wait=self.ms_wait,
                    data=data,
                )

            main_page_html = request_page_with_retry(
                session=self.session,
                url=base_url,
                verification_text="ssSearchHyperlink",
                logger=self.logger,
                http_method=HTTPMethod.GET,
                ms_wait=self.ms_wait,
            )
            main_soup = BeautifulSoup(main_page_html, "html.parser")
            # build url for court calendar
            search_page_id = None
            for link in main_soup.select("a.ssSearchHyperlink"):
                if self.court_calendar_link_text in link.text:
                    search_page_id = link["href"].split("?ID=")[1].split("'")[0]
            if not search_page_id:
                write_debug_and_quit(
                    verification_text="Court Calendar link",
                    page_text=main_page_html,
                    logger=self.logger,
                )
            search_url = base_url + "Search.aspx?ID=" + search_page_id

        # hit the search page to gather initial data
        search_page_html = request_page_with_retry(
            session=self.session,
            url=search_url
            if odyssey_version < 2017
            else urllib.parse.urljoin(base_url, "Home/Dashboard/26"),
            verification_text="Court Calendar"
            if odyssey_version < 2017
            else "SearchCriteria.SelectedCourt",
            http_method=HTTPMethod.GET,
            logger=self.logger,
            ms_wait=self.ms_wait,
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
            if self.location:
                # TODO: Made this properly sleect based on self.location
                location_option = main_soup.findAll("option")[0]
            else:
                location_option = main_soup.findAll("option")[0]
            self.logger.info(f"location: {location_option.text}")
            hidden_values.update(
                {"NodeDesc": location_option.text, "NodeID": location_option["value"]}
            )
        else:
            hidden_values["SearchCriteria.SelectedCourt"] = hidden_values[
                "Settings.DefaultLocation"
            ]  # TODO: Search in default court. Might need to add further logic later to loop through courts.

        # Individual case search logic
        if self.case_number:
            # POST a request for search results
            results_page_html = request_page_with_retry(
                session=self.session,
                url=search_url,
                verification_text="Record Count",
                logger=self.logger,
                data=create_single_case_search_form_data(hidden_values, self.case_number),
                ms_wait=self.ms_wait,
            )
            results_soup = BeautifulSoup(results_page_html, "html.parser")
            case_urls = [
                base_url + anchor["href"]
                for anchor in results_soup.select('a[href^="CaseDetail"]')
            ]
            self.logger.info(f"{len(case_urls)} entries found")
            case_id = case_urls[0].split("=")[1]
            self.logger.info(f"{case_id} - scraping case")
            # make request for the case
            case_html = request_page_with_retry(
                session=self.session,
                url=case_urls[0],
                verification_text="Date Filed",
                logger=self.logger,
                ms_wait=self.ms_wait,
            )
            # write html case data
            self.logger.info(f"{len(case_html)} response string length")
            with open(
                os.path.join(self.case_html_path, f"{case_id}.html"), "w"
            ) as file_handle:
                file_handle.write(case_html)
            return
            #sys.exit()

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
        if not self.judicial_officers:
            self.judicial_officers = list(judicial_officer_to_ID.keys())

        # initialize variables to time script and build a list of already scraped cases
        START_TIME = time()
        cached_case_list = [file_name.split(".")[0] for file_name in os.listdir(self.case_html_path)]

        # loop through each day
        for date in (
            self.start_date + timedelta(n)
            for n in range((self.end_date - self.start_date).days + 1)
        ):
            date_string = datetime.strftime(date, "%m/%d/%Y")
            # loop through each judicial officer
            for JO_name in self.judicial_officers:
                if JO_name not in judicial_officer_to_ID:
                    self.logger.error(
                        f"judicial officer {JO_name} not found on search page. Continuing."
                    )
                    continue
                JO_id = judicial_officer_to_ID[JO_name]
                self.logger.info(f"Searching cases on {date_string} for {JO_name}")
                # POST a request for search results
                results_page_html = request_page_with_retry(
                    session=self.session,
                    url=search_url
                    if odyssey_version < 2017
                    else urllib.parse.urljoin(base_url, "Hearing/SearchHearings/HearingSearch"),
                    verification_text="Record Count"
                    if odyssey_version < 2017
                    else "Search Results",
                    logger=self.logger,
                    data=create_search_form_data(
                        date_string, JO_id, hidden_values, odyssey_version
                    ),
                    ms_wait=self.ms_wait,
                )
                results_soup = BeautifulSoup(results_page_html, "html.parser")

                # different process for getting case data for pre and post 2017 Odyssey versions
                if odyssey_version < 2017:
                    case_urls = [
                        base_url + anchor["href"]
                        for anchor in results_soup.select('a[href^="CaseDetail"]')
                    ]
                    self.logger.info(f"{len(case_urls)} cases found")
                    for case_url in case_urls:
                        case_id = case_url.split("=")[1]
                        if case_id in cached_case_list and not self.overwrite:
                            self.logger.info(f"{case_id} - already scraped case")
                            continue
                        self.logger.info(f"{case_id} - scraping case")
                        # make request for the case
                        try:
                            case_html = request_page_with_retry(
                                session=self.session,
                                url=case_url,
                                verification_text="Date Filed",
                                logger=self.logger,
                                ms_wait=self.ms_wait,
                            )
                        except:
                            self.logger.info(f"Issue with scraping this case: {case_id}. Moving to next one.")
                        # write html case data
                        self.logger.info(f"{len(case_html)} response string length")
                        with open(
                            os.path.join(self.case_html_path, f"{case_id}.html"), "w"
                        ) as file_handle:
                            file_handle.write(case_html)
                        if case_id not in cached_case_list:
                            cached_case_list.append(case_id)
                        if self.test:
                            self.logger.info("Testing, stopping after first case")
                            sys.exit()
                else:
                    # Need to POST this page to get a JSON of the search results after the initial POST
                    case_list_json = request_page_with_retry(
                        session=self.session,
                        url=urllib.parse.urljoin(base_url, "Hearing/HearingResults/Read"),
                        verification_text="AggregateResults",
                        logger=self.logger,
                    )
                    case_list_json = json.loads(case_list_json)
                    self.logger.info(f"{case_list_json['Total']} cases found")
                    for case_json in case_list_json["Data"]:
                        case_id = str(case_json["CaseId"])
                        if case_id in cached_case_list and not self.overwrite:
                            self.logger.info(f"{case_id} already scraped case")
                            continue
                        self.logger.info(f"{case_id} scraping case")
                        # make request for the case
                        case_html = request_page_with_retry(
                            session=self.session,
                            url=urllib.parse.urljoin(base_url, "Case/CaseDetail"),
                            verification_text="Case Information",
                            logger=self.logger,
                            ms_wait=self.ms_wait,
                            params={
                                "eid": case_json["EncryptedCaseId"],
                                "CaseNumber": case_json["CaseNumber"],
                            },
                        )
                        # make request for financial info
                        case_html += request_page_with_retry(
                            session=self.session,
                            url=urllib.parse.urljoin(
                                base_url, "Case/CaseDetail/LoadFinancialInformation"
                            ),
                            verification_text="Financial",
                            logger=self.logger,
                            ms_wait=self.ms_wait,
                            params={
                                "caseId": case_json["CaseId"],
                            },
                        )
                        # write case html data
                        self.logger.info(f"{len(case_html)} response string length")
                        with open(
                            os.path.join(self.case_html_path, f"{case_id}.html"), "w"
                        ) as file_handle:
                            file_handle.write(case_html)
                        if case_id not in cached_case_list:
                            cached_case_list.append(case_id)
                        if self.test:
                            self.logger.info("Testing, stopping after first case")
                            sys.exit()

        self.logger.info(f"\nTime to run script: {round(time() - START_TIME, 2)} seconds")

import logging, os, re, csv, urllib.parse, json, sys
from datetime import datetime, timedelta
from time import time
import requests
from bs4 import BeautifulSoup
from .helpers import *

class scraper:
    def __init__(self, # The parameters are the defaults.
                 county = 'hays',
                 start_date = '2024-07-01', 
                 end_date = '2024-07-01', 
                 case_number = None, 
                 judicial_officers = [],
                 ms_wait = 200,
                 no_overwrite = False,
                 log = "INFO",
                 court_calendar_link_text = "Court Calendar",
                 test = False,
                 location = False
                 ):
        
        # These are optional input fields, with a bit of validation.
        self.county = county.lower()
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        self.ms_wait = ms_wait #"Number of ms to wait between requests."
        self.judicial_officers = judicial_officers #"Judicial Officers to scrape. For example, -j 'mr. something' 'Rob, Albert'. By default, it will scrape all JOs.",
        self.no_overwrite = no_overwrite #"Switch to don't overwrite cached html files if you want to speed up the process (but may not get the most up to date version).",
        self.log = log #"Set the level to log at.",
        self.court_calendar_link_text = court_calendar_link_text #"This is the link to the Court Calendar search page at default.aspx, usually it will be 'Court Calendar', but some sites have multiple calendars e.g. Williamson",
        self.test = test #"If this parameter is present, the script will stop after the first case is scraped.",
        self.case_number = case_number #"If a case number is entered, only that single case is scraped. ex. 12-2521CR",
        self.location = location # ??

        # These are class scraper-level fields that need to be stored and used from function to function. 
        self.base_url = None
        self.odyssey_version = None
        self.main_soup = None
        self.main_page_html = None
        self.search_url = None
        self.search_soup = None
        self.hidden_values = None
        self.judicial_officer_to_ID = None
        self.START_TIME = None

        # allow bad ssl and turn off warnings
        self.session = requests.Session()
        self.session.verify = False
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )

        # configure the logger
        self.logger = logging.getLogger(name="pid: " + str(os.getpid()))
        logging.basicConfig()
        logging.root.setLevel(level=self.log)

        # make cache directories if not present
        if not self.test:
            self.case_html_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", self.county, "case_html"
            )
            os.makedirs(self.case_html_path, exist_ok=True)
            # Makes a list of existing cases on the device
            self.cached_case_list = [file_name.split(".")[0] for file_name in os.listdir(self.case_html_path)]
        else: # if test = True
            self.case_html_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "resources", 'test_files', 'test_data', self.county, "case_html"
            )
            os.makedirs(self.case_html_path, exist_ok=True)
            # Makes a list of existing cases on the device
            self.cached_case_list = [file_name.split(".")[0] for file_name in os.listdir(self.case_html_path)]

        self.logger.info("Scraper class initialized")

    def get_ody_link(self, county):
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
                if row["county"].lower() == county.lower():
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
        return base_url, odyssey_version, notes

    def scrape_main_page(self, base_url, odyssey_version, notes):

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
            return main_page_html, main_soup
        
    def build_court_cal_url(self, base_url, main_page_html, main_soup):
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
        return search_url

    def scrape_needed_info(self, odyssey_version, base_url, main_soup, search_url):
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

        return search_soup, hidden_values

    def scrape_individual_case(self, base_url, search_url, hidden_values, case_number): # Individual case search logic
        # POST a request for search results
        results_page_html = request_page_with_retry(
            session=self.session,
            url=search_url,
            verification_text="Record Count",
            logger=self.logger,
            data=create_single_case_search_form_data(hidden_values, case_number),
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
        if not self.test:
            with open(
                os.path.join(self.case_html_path, f"{case_id}.html"), "w"
            ) as file_handle:
                file_handle.write(case_html)
            return
        else: # it is a test
            with open(
                os.path.join(self.case_html_path, f"test_{case_id}.html"), "w"
            ) as file_handle:
                file_handle.write(case_html)
            return

    def scrape_jo_list(self, odyssey_version, search_soup, judicial_officers):
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
        if not judicial_officers:
            judicial_officers = list(judicial_officer_to_ID.keys())
        return judicial_officers, judicial_officer_to_ID

    def scrape_results_page(self, odyssey_version, base_url, search_url, hidden_values, JO_id, date_string):
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
        return results_soup

    def scrape_case_data_pre2017(self, cached_case_list, base_url, results_soup):
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

    def scrape_case_data_post2017(self, cached_case_list, base_url):
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

    def scrape_cases(self, cached_case_list, odyssey_version, base_url, search_url, hidden_values, judicial_officers, judicial_officer_to_ID):

        # Initializing some scraper-level fields that will only be used in this function and subfunctions
        self.results_page_html = None
        self.results_soup = None

        # loop through each day
        for date in (
            self.start_date + timedelta(n)
            for n in range((self.end_date - self.start_date).days + 1)
        ):
            date_string = datetime.strftime(date, "%m/%d/%Y")
            # loop through each judicial officer
            for JO_name in judicial_officers:
                if JO_name not in judicial_officer_to_ID:
                    self.logger.error(
                        f"judicial officer {JO_name} not found on search page. Continuing."
                    )
                    continue
                JO_id = judicial_officer_to_ID[JO_name]
                self.logger.info(f"Searching cases on {date_string} for {JO_name}")

                # scrapes the results page with the search parameters and returns the html
                results_soup = self.scrape_results_page(odyssey_version, base_url, search_url, hidden_values, JO_id, date_string)

                # different process for getting case data for pre and post 2017 Odyssey versions
                if odyssey_version < 2017:
                    self.scrape_case_data_pre2017(self, cached_case_list, base_url, results_soup)
                else:
                    self.scrape_case_data_post2017(self, cached_case_list, base_url)

    def scrape(self):
        self.base_url, self.odyssey_version, self.notes = self.get_ody_link(self.county)
        self.main_page_html, self.main_soup = self.scrape_main_page(self.base_url, self.odyssey_version, self.notes)
        self.search_url = self.build_court_cal_url(self.base_url, self.main_page_html, self.main_soup)
        self.search_soup, self.hidden_values = self.scrape_needed_info(self.odyssey_version, self.base_url, self.main_soup, self.search_url)
        if self.case_number:
            self.scrape_individual_case(self.base_url, self.search_url, self.hidden_values, self.case_number)
        else:
            self.judicial_officers, self.judicial_officer_to_ID = self.scrape_jo_list(self.odyssey_version, self.search_soup, self. judicial_officers)
            self.START_TIME = time() # initialize variables to time script and build a list of already scraped cases
            self.scrape_cases(self.cached_case_list, self.odyssey_version, self.base_url, self.search_url, self.hidden_values, self.judicial_officers, self.judicial_officer_to_ID)
            self.logger.info(f"\nTime to run script: {round(time() - self.START_TIME, 2)} seconds")

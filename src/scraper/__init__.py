import logging
import os
import re
import csv
import urllib.parse
import json
import sys
from datetime import datetime, timedelta
from time import time
import requests
from bs4 import BeautifulSoup
from .helpers import *
import importlib

class Scraper:
    def __init__(self):
        pass

    def set_defaults(self, start_date, end_date, court_calendar_link_text, case_number):
        if not start_date:
            start_date = '2024-07-01'
        if not end_date:
            end_date = '2024-07-01'
        if not court_calendar_link_text:
            court_calendar_link_text = "Court Calendar"
        if not case_number:
            case_number = None
        return start_date, end_date, court_calendar_link_text, case_number

    def configure_logger(self):
        # configure the logger
        logger = logging.getLogger(name="pid: " + str(os.getpid()))
        logging.basicConfig()
        logging.root.setLevel(level="INFO")
        logger.info("Scraper class initialized")
        return logger

    def format_county(self, county):
        county = county.lower()
        return county

    def create_session(self):
        session = requests.Session()
        session.verify = False
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )
        return session

    def make_directories(self, county):
        # make directories if not present
        case_html_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", county, "case_html"
        )
        os.makedirs(case_html_path, exist_ok=True)
        return case_html_path

    def get_ody_link(self, county, logger):
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
                    logger.info(f"{base_url} - scraping this url")
                    odyssey_version = int(row["version"].split(".")[0])
                    notes = row["notes"]
                    break
        if not base_url or not odyssey_version:
            raise Exception(
                "The required data to scrape this county is not in ./resources/texas_county_data.csv"
            )
        return base_url, odyssey_version, notes

    def get_class_and_method(self, county):
        # Construct the module, class, and method names
        module_name = county #ex: 'hays'
        class_name = f"Scraper{county.capitalize()}" #ex: 'ScraperHays'
        method_name = f"scraper_{county}" #ex: 'scraper_hays'
        
        # Add the current directory to the system path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        try:
            # Dynamically import the module
            module = importlib.import_module(module_name)
            
            # Retrieve the class from the module
            cls = getattr(module, class_name)
            if cls is None:
                print(f"Class '{class_name}' not found in module '{module_name}'.")
                return None, None
            
            # Instantiate the class
            instance = cls()
            
            # Retrieve the method with the specified name
            method = getattr(instance, method_name, None)
            if method is None:
                print(f"Method '{method_name}' not found in class '{class_name}'.")
                return instance, None
            
            return instance, method
        except ModuleNotFoundError:
            print(f"Module '{module_name}' not found.")
            return None, None

    def scrape_main_page(self, base_url, odyssey_version, session, notes, logger):
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

                response = request_page(
                    session=session,
                    url=urllib.parse.urljoin(base_url, "login.aspx"),
                    logger=logger,
                    http_method=HTTPMethod.GET,
                    data=data,
                )

            main_page_html = request_page(
                session=session,
                url=base_url,
                verification_text="ssSearchHyperlink",
                logger=logger,
                http_method=HTTPMethod.GET,
            )
            main_soup = BeautifulSoup(main_page_html, "html.parser")
            return main_page_html, main_soup
        
    def scrape_search_page(self, base_url, odyssey_version, main_page_html, main_soup, session, logger, court_calendar_link_text):
        # build url for court calendar
        search_page_id = None
        for link in main_soup.select("a.ssSearchHyperlink"):
            if court_calendar_link_text in link.text:
                search_page_id = link["href"].split("?ID=")[1].split("'")[0]
        if not search_page_id:
            write_debug_and_quit(
                verification_text="Court Calendar link",
                page_text=main_page_html,
                logger=logger,
            )
        search_url = base_url + "Search.aspx?ID=" + search_page_id

        # hit the search page to gather initial data
        search_page_html = request_page(
            session=session,
            url=search_url
            if odyssey_version < 2017
            else urllib.parse.urljoin(base_url, "Home/Dashboard/26"),
            verification_text="Court Calendar"
            if odyssey_version < 2017
            else "SearchCriteria.SelectedCourt",
            http_method=HTTPMethod.GET,
            logger=logger
        )
        search_soup = BeautifulSoup(search_page_html, "html.parser")

        return search_url, search_page_html, search_soup

    def get_hidden_values(self, odyssey_version, main_soup, search_soup, logger):
        # we need these hidden values to POST a search
        hidden_values = {
            hidden["name"]: hidden["value"]
            for hidden in search_soup.select('input[type="hidden"]')
            if hidden.has_attr("name")
        }
        # get nodedesc and nodeid information from main page location select box
        if odyssey_version < 2017:
            location_option = main_soup.findAll("option")[0]
            logger.info(f"location: {location_option.text}")
            hidden_values.update(
                {"NodeDesc": location_option.text, "NodeID": location_option["value"]}
            )
        else:
            hidden_values["SearchCriteria.SelectedCourt"] = hidden_values[
                "Settings.DefaultLocation"
            ]  # TODO: Search in default court. Might need to add further logic later to loop through courts.
        return hidden_values

    def get_search_results(self, session, search_url, logger, hidden_values, case_number):
        # POST a request for search results
        results_page_html = request_page(
            session=session,
            url=search_url,
            verification_text="Record Count",
            logger=logger,
            data=create_single_case_search_form_data(hidden_values, case_number)
        )
        results_soup = BeautifulSoup(results_page_html, "html.parser")
        return results_soup

    def scrape_individual_case(self, base_url, search_url, hidden_values, case_number, case_html_path, session, logger): # Individual case search logic
        results_soup = self.get_search_results(session, search_url, logger, hidden_values, case_number)
        case_urls = [
            base_url + anchor["href"]
            for anchor in results_soup.select('a[href^="CaseDetail"]')
        ]
        logger.info(f"{len(case_urls)} entries found")
        case_id = case_urls[0].split("=")[1]
        logger.info(f"{case_id} - scraping case")
        # make request for the case
        case_html = request_page(
            session=session,
            url=case_urls[0],
            verification_text="Date Filed",
            logger=logger
        )
        # write html case data
        logger.info(f"{len(case_html)} response string length")

        with open(
            os.path.join(case_html_path, f"{case_id}.html"), "w"
        ) as file_handle:
            file_handle.write(case_html)

    def scrape_jo_list(self, odyssey_version, search_soup, judicial_officers, logger):
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

    def scrape_results_page(self, odyssey_version, base_url, search_url, hidden_values, JO_id, date_string, session, logger):
        # POST a request for search results
        logger.info(f"date_string:{date_string}")
        results_page_html = request_page(
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
            )
            )
        results_soup = BeautifulSoup(results_page_html, "html.parser")
        return results_page_html, results_soup

    # Not currently in use. Should be moved to a county-specific module, class, and method when a post2017 county is included
    """def scrape_case_data_post2017(self, base_url, case_html_path, session, logger):
        # Need to POST this page to get a JSON of the search results after the initial POST
        case_list_json = request_page(
            session=session,
            url=urllib.parse.urljoin(base_url, "Hearing/HearingResults/Read"),
            verification_text="AggregateResults",
            logger=logger,
        )
        case_list_json = json.loads(case_list_json)
        logger.info(f"{case_list_json['Total']} cases found")
        for case_json in case_list_json["Data"]:
            case_id = str(case_json["CaseId"])
            logger.info(f"{case_id} scraping case")
            # make request for the case
            case_html = request_page(
                session=session,
                url=urllib.parse.urljoin(base_url, "Case/CaseDetail"),
                verification_text="Case Information",
                logger=logger,
                params={
                    "eid": case_json["EncryptedCaseId"],
                    "CaseNumber": case_json["CaseNumber"],
                },
            )
            # make request for financial info
            case_html += request_page(
                session=session,
                url=urllib.parse.urljoin(
                    base_url, "Case/CaseDetail/LoadFinancialInformation"
                ),
                verification_text="Financial",
                logger=logger,
                params={
                    "caseId": case_json["CaseId"],
                },
            )
            # write case html data
            logger.info(f"{len(case_html)} response string length")
            with open(
                os.path.join(case_html_path, f"{case_id}.html"), "w"
            ) as file_handle:
                file_handle.write(case_html)"""

    def scrape_multiple_cases(self, county, odyssey_version, base_url, search_url, hidden_values, judicial_officers, judicial_officer_to_ID, case_html_path, logger, session, start_date, end_date):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        # loop through each day
        for date in (
            start_date + timedelta(n)
            for n in range((end_date - start_date).days + 1)
        ):
            date_string = datetime.strftime(date, "%m/%d/%Y")
            # loop through each judicial officer
            for JO_name in judicial_officers:
                if JO_name not in judicial_officer_to_ID:
                    logger.error(f"judicial officer {JO_name} not found on search page. Continuing.")
                    continue
                JO_id = judicial_officer_to_ID[JO_name]
                logger.info(f"Searching cases on {date_string} for {JO_name}")
                # scrapes the results page with the search parameters and returns the soup. it also returns the html but it's not used at this time
                results_html, results_soup = self.scrape_results_page(odyssey_version, base_url, search_url, hidden_values, JO_id, date_string, session, logger)
                # get a different scraper for each county
                self.get_class_and_method(county)
                # gets the county-specific scraper class and method
                scraper_instance, scraper_function = self.get_class_and_method(county=county)
                if scraper_instance is not None and scraper_function is not None:
                    scraper_function(base_url, results_soup, case_html_path, logger, session)
                else:
                    print("Error: Could not obtain parser instance or function.")

    def scrape(self, county, judicial_officers, start_date, end_date, court_calendar_link_text, case_number, case_html_path):
        start_date, end_date, court_calendar_link_text, case_number = self.set_defaults(start_date, end_date, court_calendar_link_text, case_number)
        logger = self.configure_logger()
        county = self.format_county(county)
        session = self.create_session()
        self.make_directories(county) if not case_html_path else case_html_path
        base_url, odyssey_version, notes = self.get_ody_link(county, logger)
        main_page_html, main_soup = self.scrape_main_page(base_url, odyssey_version, session, notes, logger)
        search_url, search_page_html, search_soup = self.scrape_search_page(base_url, odyssey_version, main_page_html, main_soup, session, logger, court_calendar_link_text)
        hidden_values = self.get_hidden_values(odyssey_version, main_soup, search_soup, logger)
        if case_number: # just scrapes the one case
            self.scrape_individual_case(base_url, search_url, hidden_values, case_number, case_html_path, session, logger)
        else: # scrape a list of JOs between a start and end date
            judicial_officers, judicial_officer_to_ID = self.scrape_jo_list(odyssey_version, search_soup, judicial_officers, logger)
            SCRAPER_START_TIME = time()
            self.scrape_multiple_cases(odyssey_version, base_url, search_url, hidden_values, judicial_officers, judicial_officer_to_ID, case_html_path, logger, session, start_date, end_date)
            logger.info(f"\nTime to run script: {round(time() - SCRAPER_START_TIME, 2)} seconds")

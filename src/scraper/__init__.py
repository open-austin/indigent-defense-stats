import logging
import os
import csv
import urllib.parse
import sys
from datetime import datetime, timedelta
from time import time
import requests
from bs4 import BeautifulSoup
from .helpers import *
import importlib
from typing import Optional, Tuple, Callable, Type, List
import importlib.util
import re

class Scraper:
    """Scrape Odyssey html files into an output folder"""
    def __init__(self):
        pass

    def set_defaults(
        self, 
        ms_wait: int | None = None, 
        start_date: str | None = None, 
        end_date: str | None = None, 
        court_calendar_link_text: str | None = None, 
        case_number: str | None = None,
        ssl: bool | None = None,
        county: str | None = None,
        case_html_path: str | None = None,
    ) -> Tuple[int, str, str, str, Optional[str], bool, str, str]:
        """
        Sets default values for the provided optional parameters.

        Defaults:
        - `ms_wait`: 200 milliseconds if not provided.
        - `start_date`: '2024-07-01' if not provided.
        - `end_date`: '2024-07-01' if not provided.
        - `court_calendar_link_text`: 'Court Calendar' if not provided.
        - `case_number`: None if not provided.

        :param ms_wait: Milliseconds to wait.
        :param start_date: Start date in YYYY-MM-DD format.
        :param end_date: End date in YYYY-MM-DD format.
        :param court_calendar_link_text: Text for the court calendar link.
        :param case_number: Case number, or None.

        :returns: A tuple containing:
            - ms_wait (int): Milliseconds to wait.
            - start_date (str): Start date.
            - end_date (str): End date.
            - court_calendar_link_text (str): Text for court calendar link.
            - case_number (Optional[str]): Case number or None.
        """

        # Assign default values if parameters are not provided
        ms_wait = ms_wait if ms_wait is not None else 200
        start_date = start_date if start_date is not None else '2024-07-01'
        end_date = end_date if end_date is not None else '2024-07-01'
        court_calendar_link_text = court_calendar_link_text if court_calendar_link_text is not None else "Court Calendar"
        # case_number defaults to None if not provided
        case_number = case_number
        ssl = ssl if ssl is not None else True
        county = county if county is not None else 'hays'
        case_html_path = case_html_path if case_html_path is not None else os.path.join(os.path.dirname(__file__), "..", "..", "data", county, "case_html")
        return ms_wait, start_date, end_date, court_calendar_link_text, case_number, ssl, county, case_html_path

    def configure_logger(self) -> logging.Logger:
        """
        Configures and returns a logger instance for the scraper class.

        This method sets up the logger with a unique name based on the process ID, 
        configures the logging level to INFO, and logs an initialization message.

        :returns: Configured logger instance.
        """
        # Configure the logger
        logger = logging.getLogger(name=f"scraper: pid: {os.getpid()}")
        
        # Set up basic configuration for the logging system
        logging.basicConfig(level=logging.INFO)

        scraper_log_path = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        now = datetime.now()
        # Format it as "DD-MM-YYYY - HH:MM"
        formatted_date_time = now.strftime("%d-%m-%Y-%H.%M")
        scraper_log_name = formatted_date_time + '_scraper_logger_log.txt'

        file_handler = logging.FileHandler(os.path.join(scraper_log_path, scraper_log_name))
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
                
        return logger

    def format_county(self, county: str) -> str:
        """
        Formats the county name to lowercase.

        :param county: The name of the county to be formatted.
        :returns: The county name in lowercase.
        :raises TypeError: If the provided county name is not a string.
        """
        
        return re.sub(r'[^\w]+', '', county.lower())

    def create_session(self, logger: logging.Logger, ssl) -> requests.sessions.Session:
        """
        Sets up a `requests.Session` with or without SSL verification and suppresses 
        related warnings.

        Defaults to enable SSL.

        :param logger: Logger instance for logging errors.
        :returns: Configured session object.
        """
        # Create and configure the session
        session = requests.Session()

        # Optionally SSL certificate verification. Default to True unless False passed.
        session.verify = ssl
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        
        return session

    def make_directories(self, case_html_path: str, logger):
        """Looks for a directory at the case_html_path location or creates it if it doesn't exist."""
        try:
            if not os.path.exists(case_html_path):
                os.makedirs(case_html_path)
                logger.info(f"Directory '{case_html_path}' created successfully.")
            else:
                logger.info(f"Directory '{case_html_path}' already exists.")
        except OSError as e:
            logger.error(f"Error creating directory '{case_html_path}': {e}")

    # get county portal URL, Odyssey version, and notes from csv file
    def get_ody_link(self, 
                     county: str, 
                     logger: logging.Logger
                     ) -> Tuple[str, str, str ]:
        """
        Retrieves Odyssey-related information for a given county from a CSV file.

        This function reads county-specific data from a CSV file located in the `resources` directory. 
        It searches for the county name in the CSV file, extracts the corresponding base URL, Odyssey 
        version, and any additional notes. The base URL is formatted with a trailing slash if necessary.

        :param county: The name of the county for which to retrieve Odyssey information.
        :param logger: Logger instance for logging errors and information.
        :returns: A tuple containing:
            - base_url (str): The base URL for the county’s portal.
            - odyssey_version (str): The major version of Odyssey associated with the county.
            - notes (str): Additional notes related to the county.
        :raises Exception: If the county is not found in the CSV file or if required data is missing.
        """

        try:
            base_url = odyssey_version = notes = None
            # CSV is located in 'resources' folder
            with open(
                os.path.join(os.path.dirname(__file__), "..", "..", "resources", "texas_county_data.csv"),
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
                raise Exception("The required data to scrape this county is not in /resources/texas_county_data.csv")
        except Exception as e:
            logger.exception(e, "Error getting county-specific information from csv.")
            raise
        return base_url, odyssey_version, notes

    def get_class_and_method(
        self,
        county: str, 
        logger: logging.Logger
    ) -> Tuple[Type[object], Callable]:
        
        """
        Dynamically imports a module, retrieves a class, and gets a method from it based on the county name.

        :param county: The name of the county, used to construct module, class, and method names.
        :param logger: Logger instance for logging errors.
        :returns: A tuple containing the instance of the class and the method callable.
        :raises ImportError: If the module cannot be imported.
        :raises AttributeError: If the class or method cannot be found.
        """

        module_name = f"s_{county}"  # ex: 's_hays'
        class_name = f"Scraper{county.capitalize()}"
        method_name = f"scraper_{county}"

        # Add the current directory to the system path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        try:
            # Dynamically import the module
            module = importlib.import_module(module_name)
            
            # Retrieve the class from the module
            cls = getattr(module, class_name, None)
            if cls is None:
                raise AttributeError(f"Class '{class_name}' not found in module '{module_name}'")

            # Instantiate the class
            instance = cls()
            
            # Retrieve the method with the specified name
            method = getattr(instance, method_name, None)
            if method is None:
                raise AttributeError(f"Method '{method_name}' not found in class '{class_name}'")

            return instance, method

        except (FileNotFoundError, ImportError, AttributeError) as e:
            logger.exception(e, "Error dynamically loading module or retrieving class/method.")
            raise

    def scrape_main_page(self, 
                         base_url: str, 
                         odyssey_version: int, 
                         session: requests.sessions.Session, 
                         notes: str, 
                         logger: logging.Logger, 
                         ms_wait: int
                         ) -> Tuple[str, BeautifulSoup]:
        """
        Scrapes the main page of the Odyssey site, handling login if required, and returns the page's HTML and parsed content.

        This function handles a special case where some sites may require a public guest login. If the `notes` parameter 
        contains a "PUBLICLOGIN#" identifier, it will extract the username and password from the `notes`, perform the login, 
        and then proceed to scrape the main page.

        :param base_url: The base URL of the main page to scrape.
        :param odyssey_version: The version of Odyssey; currently not used in this function.
        :param session: The `requests` session object used for making HTTP requests.
        :param notes: A string containing notes that may include login credentials in the format "PUBLICLOGIN#username/password".
        :param logger: Logger instance for logging errors and debug information.
        :param ms_wait: The number of milliseconds to wait between retry attempts.
        :returns: A tuple containing:
            - main_page_html (str): The raw HTML content of the main page.
            - main_soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML content.
        :raises Exception: If any error occurs during the HTTP requests or HTML parsing.
        """

        try:
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

                request_page_with_retry(
                    session=session,
                    url=urllib.parse.urljoin(base_url, "login.aspx"),
                    logger=logger,
                    http_method=HTTPMethod.GET,
                    ms_wait=ms_wait,
                    data=data,
                )

            main_page_html = request_page_with_retry(
                session=session,
                url=base_url,
                verification_text="ssSearchHyperlink",
                logger=logger,
                http_method=HTTPMethod.GET,
                ms_wait=ms_wait,
            )
            main_soup = BeautifulSoup(main_page_html, "html.parser")
        except Exception as e:
            logger.exception(e, f"Error scraping main page for main page HTML.")
            raise
        return main_page_html, main_soup
        
    def scrape_search_page(
        self,
        base_url: str,
        odyssey_version: int,
        main_page_html: str,
        main_soup: BeautifulSoup,
        session: requests.sessions.Session,
        logger: logging.Logger,
        ms_wait: int,
        court_calendar_link_text: str
    ) -> Tuple[str, str, BeautifulSoup]:
        """
        Scrapes the search page URL and data based on the main page content.

        This method extracts the search page ID from the court calendar link, constructs the URL for the search page,
        and retrieves the search page HTML. Depending on the Odyssey version, it either uses the extracted URL or a
        default URL. It then parses the search page HTML into a BeautifulSoup object.

        :param base_url: The base URL for constructing full URLs.
        :param odyssey_version: The version of Odyssey, used to determine the correct URL and verification text.
        :param main_page_html: The HTML content of the main page.
        :param main_soup: Parsed BeautifulSoup object of the main page HTML.
        :param session: The session object for making HTTP requests.
        :param logger: Logger instance for logging errors and information.
        :param ms_wait: Milliseconds to wait before making requests.
        :param court_calendar_link_text: Text to search for in the court calendar link.
        :returns: A tuple containing the search page URL, search page HTML, and the BeautifulSoup object of the search page.
        :raises ValueError: If the court calendar link is not found on the main page.
        """

        # Extract the search page ID from the court calendar link
        search_page_id = None
        for link in main_soup.select("a.ssSearchHyperlink"):
            if court_calendar_link_text in link.text:
                search_page_id = link["href"].split("?ID=")[1].split("'")[0]
                break  # Exit loop once the link is found

        if not search_page_id:
            write_debug_and_quit(
                verification_text="Court Calendar link",
                page_text=main_page_html,
                logger=logger,
            )
            raise ValueError("Court Calendar link not found on the main page.")

        # Build the URL for the search page
        search_url = f"{base_url}Search.aspx?ID={search_page_id}"
        
        # Determine the correct URL and verification text based on Odyssey version
        if odyssey_version < 2017:
            search_url = search_url
            verification_text = "Court Calendar"
        else:
            search_url = urllib.parse.urljoin(base_url, "Home/Dashboard/26")
            verification_text = "SearchCriteria.SelectedCourt"
        
        # Hit the search page to gather initial data
        search_page_html = request_page_with_retry(
            session=session,
            url=search_url,
            verification_text=verification_text,
            http_method=HTTPMethod.GET,
            logger=logger,
            ms_wait=ms_wait,
        )
        search_soup = BeautifulSoup(search_page_html, "html.parser")

        return search_url, search_page_html, search_soup

    def get_hidden_values(
        self,
        odyssey_version: int,
        main_soup: BeautifulSoup,
        search_soup: BeautifulSoup,
        logger: logging.Logger
    ) -> Dict[str, str]:
        """
        Extracts hidden input values and additional data from the search page.

        :param odyssey_version: The version of Odyssey to determine logic.
        :param main_soup: Parsed BeautifulSoup object of the main page HTML.
        :param search_soup: Parsed BeautifulSoup object of the search page HTML.
        :param logger: Logger instance for logging information.
        :returns: Dictionary of hidden input names and their values.
        """

        # Extract hidden input values
        hidden_values = {
            hidden["name"]: hidden["value"]
            for hidden in search_soup.select('input[type="hidden"]')
            if hidden.has_attr("name")
        }

        # Get NodeDesc and NodeID information based on Odyssey version
        if odyssey_version < 2017:
            location_option = main_soup.find_all("option")[0]
            logger.info(f"Location: {location_option.text}")
            hidden_values.update({
                "NodeDesc": location_option.text,
                "NodeID": location_option["value"]
            })
        else:
            hidden_values["SearchCriteria.SelectedCourt"] = hidden_values.get("Settings.DefaultLocation", "")

        return hidden_values

    def get_search_results(
        self,
        session: requests.sessions.Session,
        search_url: str,
        logger: logging.Logger,
        ms_wait: int,
        hidden_values: Dict[str, str],
        case_number: Optional[str]
    ) -> BeautifulSoup:
        """
        Retrieves search results from the search page.

        :param session: The session object for making HTTP requests.
        :param search_url: The URL to request search results from.
        :param logger: Logger instance for logging information.
        :param ms_wait: Milliseconds to wait before making requests.
        :param hidden_values: Dictionary of hidden input values.
        :param case_number: Case number for searching.
        :returns: Parsed BeautifulSoup object of the search results page HTML.
        """

        results_page_html = request_page_with_retry(
            session=session,
            url=search_url,
            verification_text="Record Count",
            logger=logger,
            data=create_single_case_search_form_data(hidden_values, case_number),
            ms_wait=ms_wait,
        )
        return BeautifulSoup(results_page_html, "html.parser")

    def scrape_individual_case(
        self,
        base_url: str,
        search_url: str,
        hidden_values: Dict[str, str],
        case_number: Optional[str],
        case_html_path: str,
        session: requests.sessions.Session,
        logger: logging.Logger,
        ms_wait: int
    ) -> None:

        results_soup = self.get_search_results(session, search_url, logger, ms_wait, hidden_values, case_number)
        case_urls = [
            base_url + anchor["href"]
            for anchor in results_soup.select('a[href^="CaseDetail"]')
        ]
        
        logger.info(f"scraper: {len(case_urls)} entries found")
        
        if case_urls:
            case_id = case_urls[0].split("=")[1]
            logger.info(f"{case_id} - scraping case")
            
            case_html = request_page_with_retry(
                session=session,
                url=case_urls[0],
                verification_text="Date Filed",
                logger=logger,
                ms_wait=ms_wait,
            )
            
            logger.info(f"scraper: {len(case_html)} response string length")

            with open(
                os.path.join(case_html_path, f"{case_id}.html"), "w"
            ) as file_handle:
                file_handle.write(case_html)
        else:
            logger.warning("No case URLs found.")

    def scrape_jo_list(
        self,
        odyssey_version: int,
        search_soup: BeautifulSoup,
        judicial_officers: Optional[List[str]],
        logger: logging.Logger
    ) -> Tuple[List[str], Dict[str, str]]:
        """
        Scrapes a list of judicial officers and their IDs from the search page.

        Optionally receives a list of judicial officers to scrape.

        :param odyssey_version: The version of Odyssey to determine the selector.
        :param search_soup: Parsed BeautifulSoup object of the search page HTML.
        :param judicial_officers: List of specific judicial officers to use.
        :param logger: Logger instance for logging information.
        :returns: Tuple containing a list of judicial officers to use and a dictionary of judicial officers and their IDs.
        """

        selector = 'select[labelname="Judicial Officer:"] > option' if odyssey_version < 2017 else 'select[id="selHSJudicialOfficer"] > option'
        judicial_officer_to_ID = {
            option.text: option["value"]
            for option in search_soup.select(selector)
            if option.text
        }
        
        if not judicial_officers:
            judicial_officers = list(judicial_officer_to_ID.keys())
            logger.info(f"scraper: No judicial officers specified, so scraping all of them: {len(judicial_officers)}")
        else:
            logger.info(f"scraper: Judicial officers were specified, so only scraping these: {judicial_officers}")            
        
        return judicial_officers, judicial_officer_to_ID

    def scrape_results_page(
        self,
        odyssey_version: int,
        base_url: str,
        search_url: str,
        hidden_values: dict[str, str],
        jo_id: str,
        date_string: str,
        session: requests.sessions.Session,
        logger: logging.Logger,
        ms_wait: int
    ) -> Tuple[str, BeautifulSoup]:
        """
        Scrapes the results page based on Odyssey version and search criteria.

        :param odyssey_version: The version of Odyssey to determine the URL and verification text.
        :param base_url: The base URL for constructing full URLs.
        :param search_url: The URL to request search results from.
        :param hidden_values: Dictionary of hidden input values.
        :param jo_id: Judicial officer ID for searching.
        :param date_string: Date string for searching.
        :param session: The session object for making HTTP requests.
        :param logger: Logger instance for logging information.
        :param ms_wait: Milliseconds to wait before making requests.
        :returns: A tuple containing the HTML of the results page and the parsed BeautifulSoup object.
        """

        search_url = (
            search_url
            if odyssey_version < 2017
            else urllib.parse.urljoin(base_url, "Hearing/SearchHearings/HearingSearch")
        )
        
        verification_text = (
            "Record Count"
            if odyssey_version < 2017
            else "Search Results"
        )
        
        results_page_html = request_page_with_retry(
            session=session,
            url=search_url,
            verification_text=verification_text,
            logger=logger,
            data=create_search_form_data(date_string, jo_id, hidden_values, odyssey_version),
            ms_wait=ms_wait,
        )
        
        results_soup = BeautifulSoup(results_page_html, "html.parser")
        
        return results_page_html, results_soup

    def scrape_multiple_cases(
        self,
        county: str,
        odyssey_version: int,
        base_url: str,
        search_url: str,
        hidden_values: Dict[str, str],
        judicial_officers: List[str],
        judicial_officer_to_ID: Dict[str, str],
        case_html_path: Optional[str],
        logger: logging.Logger,
        session: requests.Session,
        ms_wait: int,
        start_date: str,
        end_date: str
    ) -> None:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        for date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
            date_string = date.strftime("%m/%d/%Y")
            
            for JO_name in judicial_officers:
                if JO_name not in judicial_officer_to_ID:
                    logger.error(f"Judicial officer {JO_name} not found on search page. Continuing.")
                    continue
                
                jo_id = judicial_officer_to_ID[JO_name]
                logger.info(f"Searching cases on {date_string} for {JO_name}")
                
                results_page_html, results_soup = self.scrape_results_page(
                    odyssey_version, base_url, search_url, hidden_values, jo_id, date_string, session, logger, ms_wait
                )
                
                scraper_instance, scraper_function = self.get_class_and_method(county, logger)
                scraper_function(base_url, results_soup, case_html_path, logger, session, ms_wait)

    def scrape(
        self,
        county: str,
        judicial_officers: List[str],
        ms_wait: int,
        start_date: str,
        end_date: str,
        court_calendar_link_text: Optional[str],
        case_number: Optional[str],
        case_html_path: Optional[str],
        ssl: Optional[bool] = True
    ) -> None:
        ms_wait, start_date, end_date, court_calendar_link_text, case_number, ssl, county, case_html_path = self.set_defaults(
            ms_wait, start_date, end_date, court_calendar_link_text, case_number, ssl, county, case_html_path
        )
        
        logger = self.configure_logger()
        county = self.format_county(county)
        session = self.create_session(logger, ssl)
        
        self.make_directories(case_html_path, logger)
        
        base_url, odyssey_version, notes = self.get_ody_link(county, logger)
        main_page_html, main_soup = self.scrape_main_page(base_url, odyssey_version, session, notes, logger, ms_wait)
        search_url, search_page_html, search_soup = self.scrape_search_page(
            base_url, odyssey_version, main_page_html, main_soup, session, logger, ms_wait, court_calendar_link_text
        )
        
        hidden_values = self.get_hidden_values(odyssey_version, main_soup, search_soup, logger)
        
        if case_number:
            self.scrape_individual_case(
                base_url, search_url, hidden_values, case_number, case_html_path, session, logger, ms_wait
            )
        else:
            judicial_officers, judicial_officer_to_ID = self.scrape_jo_list(
                odyssey_version, search_soup, judicial_officers, logger
            )
            scraper_start_time = time()
            self.scrape_multiple_cases(
                county, odyssey_version, base_url, search_url, hidden_values, judicial_officers, judicial_officer_to_ID,
                case_html_path, logger, session, ms_wait, start_date, end_date
            )
            logger.info(f"\nTime to run script: {round(time() - scraper_start_time, 2)} seconds")

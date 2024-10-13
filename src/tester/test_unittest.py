from datetime import datetime, timedelta
import unittest
import sys
import os
import json
import logging
from unittest.mock import patch, MagicMock, mock_open
import tempfile
from bs4 import BeautifulSoup

# Import all of the programs modules within the parent_dir
from scraper import Scraper
from parser import Parser
from cleaner import Cleaner
from updater import Updater

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)

sys.path.append(parent_dir)

SKIP_SLOW = os.getenv("SKIP_SLOW", "false").lower().strip() == "true"


def log(
    message, level="INFO"
):  # Provide message and info level (optional, defaulting to info)
    # configure the logger
    log = logging.getLogger(name="pid: " + str(os.getpid()))
    logging.basicConfig()
    logging.root.setLevel(level=level)
    log.info(message)


class ScraperTestCase(unittest.TestCase):
    # Defaults for each program are set at the function level.

    def test_scrape_get_ody_link(self, county="hays"):
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        base_url = scraper_instance.get_ody_link(county, logger)
        self.assertIsNotNone(base_url, "No URL found for this county.")

    def test_scrape_main_page(
        self,
        base_url=r"http://public.co.hays.tx.us/",
        odyssey_version=2003,
        notes="",
        ms_wait=None,
        start_date=None,
        end_date=None,
        court_calendar_link_text=None,
        case_number=None,
        ssl=True,
        case_html_path=None,
        county="hays",
    ):
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        (
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        ) = scraper_instance.set_defaults(
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        )
        session = scraper_instance.create_session(logger, ssl)
        main_page_html, main_soup = scraper_instance.scrape_main_page(
            base_url, odyssey_version, session, notes, logger, ms_wait
        )
        self.assertIsNotNone(
            main_page_html, "No main page HTML came through. main_page_html = None."
        )
        self.assertTrue(
            "ssSearchHyperlink" in main_page_html,
            "There is no 'ssSearchHyperlink' text found in this main page html.",
        )  # Note: This validation is already being done using the 'verification_text' field.
        self.assertTrue(
            "Hays County Courts Records Inquiry" in main_page_html,
            "There is no 'Hays County Courts Records Inquiry' listed in this Hays County main page HTML.",
        )

    def test_scrape_search_page(
        self,
        base_url=r"http://public.co.hays.tx.us/",
        odyssey_version=2003,
        main_page_html=None,
        main_soup=None,
        session=None,
        logger=None,
        ms_wait=None,
        court_calendar_link_text=None,
        start_date=None,
        end_date=None,
        case_number=None,
        ssl=True,
        case_html_path=None,
        county="hays",
    ):
        # Open the mocked main page HTML
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "test_files",
                "hays_main_page.html",
            ),
            "r",
            encoding="utf-8",
        ) as file_handle:
            main_page_html = (
                file_handle.read()
            )  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")
        # Look for the court calendar link
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        (
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        ) = scraper_instance.set_defaults(
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        )
        session = scraper_instance.create_session(logger, ssl)
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(
            base_url,
            odyssey_version,
            main_page_html,
            main_soup,
            session,
            logger,
            ms_wait,
            court_calendar_link_text,
        )
        # Verify the court calendar link
        self.assertIsNotNone(
            main_page_html, "No search url came through. search_url = None."
        )
        self.assertTrue(
            search_url == r"http://public.co.hays.tx.us/Search.aspx?ID=900",
            "The link was not properly parsed from the test main page HTML.",
        )
        self.assertIsNotNone(
            search_page_html, "No search HTML came through. search_page_html = None."
        )
        self.assertIsNotNone(
            search_soup,
            "No search HTML parsed into beautiful soup came through. search_soup = None.",
        )
        # Verify the html or soup of the search page -- need to write more validation here: What do I want to know about it?
        # self.assertTrue(??????, ??????)

    def test_get_hidden_values(
        self,
        odyssey_version=2003,
        main_soup=None,
        search_soup=None,
        logger=None,
        ms_wait=None,
        court_calendar_link_text=None,
        start_date=None,
        end_date=None,
        case_number=None,
        ssl=True,
        case_html_path=None,
        county="hays",
    ):
        # Open the mocked main page HTML
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "test_files",
                "hays_main_page.html",
            ),
            "r",
            encoding="utf-8",
        ) as file_handle:
            main_page_html = (
                file_handle.read()
            )  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")

        # Open the mocked search page HTML
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "test_files",
                "hays_search_page.html",
            ),
            "r",
            encoding="utf-8",
        ) as file_handle:
            search_page_html = (
                file_handle.read()
            )  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        search_soup = BeautifulSoup(search_page_html, "html.parser")

        # Run the function
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        (
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        ) = scraper_instance.set_defaults(
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        )
        hidden_values = scraper_instance.get_hidden_values(
            odyssey_version, main_soup, search_soup, logger
        )
        self.assertIsNotNone(
            hidden_values, "No hidden values came through. hidden_values = None."
        )
        self.assertTrue(
            type(hidden_values) == dict,
            "The hidden values fields is not a dictionary but it needs to be.",
        )

    # Note: This doesn't run the scrape function directly the way the others do. The scrape function requires other functions to run first to populate variables in the class name space first.
    def test_scrape_individual_case(
        self,
        base_url=None,
        search_url=None,
        hidden_values=None,
        case_number="CR-16-0002-A",
        county="hays",
        judicial_officers=[],
        ms_wait=None,
        start_date=None,
        end_date=None,
        court_calendar_link_text=None,
        case_html_path=os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "resources",
            "test_files",
            "test_data",
            "hays",
            "case_html",
        ),
        ssl=True,
    ):
        # This starts a timer to compare the run start time to the last updated time of the resulting HTML to ensure the HTML was created after run start time
        now = datetime.now()

        # makes the test directory
        os.makedirs(case_html_path, exist_ok=True)

        # Call the functions being tested. In this case, the functions being called are all of the subfunctions required and effectively replicates the shape of scrape.
        scraper_instance = Scraper()
        (
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        ) = scraper_instance.set_defaults(
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        )
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        session = scraper_instance.create_session(logger, ssl)
        case_html_path = (
            scraper_instance.make_directories(county)
            if not case_html_path
            else case_html_path
        )
        base_url, odyssey_version, notes = scraper_instance.get_ody_link(county, logger)
        main_page_html, main_soup = scraper_instance.scrape_main_page(
            base_url, odyssey_version, session, notes, logger, ms_wait
        )
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(
            base_url,
            odyssey_version,
            main_page_html,
            main_soup,
            session,
            logger,
            ms_wait,
            court_calendar_link_text,
        )
        hidden_values = scraper_instance.get_hidden_values(
            odyssey_version, main_soup, search_soup, logger
        )
        scraper_instance.scrape_individual_case(
            base_url,
            search_url,
            hidden_values,
            case_number,
            case_html_path,
            session,
            logger,
            ms_wait,
        )

        # Test #1: Did the scraper create a new file called 12947592.html in the right location?
        # this creates the file path, checks to see if the HTML file is there, and then checks to see that HTML file has been updated since the program started running.
        test_case_html_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "resources",
            "test_files",
            "test_data",
            "hays",
            "case_html",
            "12947592.html",
        )
        self.assertTrue(
            os.path.isfile(test_case_html_path),
            "There is no HTML file the correct name in the correct folder.",
        )
        # this gets the time the file was last updated and converts it from unix integer to date time
        test_html_updated_time = os.path.getmtime(test_case_html_path)
        seconds = int(test_html_updated_time)
        microseconds = int((test_html_updated_time - seconds) * 1e6)
        test_html_updated_time = datetime.fromtimestamp(seconds) + timedelta(
            microseconds=microseconds
        )
        self.assertTrue(
            test_html_updated_time > now,
            "This HTML has not been updated since this test started running.",
        )

        # Test #2: Is the resulting HTML file longer than 1000 characters?
        with open(test_case_html_path, "r") as file_handle:
            case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")
        self.assertTrue(
            len(case_soup.text) > 1000,
            "This HTML is smaller than 1000 characters and may be an error.",
        )

        # Test #3: Does the resulting HTML file container the cause number in the expected header location?
        self.assertTrue(test_html_updated_time > now)
        # Parse the HTML in the expected location for the cause number.
        case_number_html = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
            0
        ].text
        self.assertTrue(
            case_number_html == "CR-16-0002-A",
            "The cause number is not where it was expected to be in the HTML.",
        )
        # self.logger.info(f"Scraper test sucessful for cause number CR-16-0002-A.")

    # This begins the tests related the scrape_cases function for scraping multiple cases.

    def test_scrape_jo_list(
        self,
        base_url=r"http://public.co.hays.tx.us/",
        odyssey_version=2003,
        notes="",
        search_soup=None,
        judicial_officers=None,
        ms_wait=None,
        start_date=None,
        end_date=None,
        court_calendar_link_text=None,
        case_number=None,
        county="hays",
        session=None,
        logger=None,
        ssl=True,
        case_html_path=None,
    ):
        # This test requires that certain dependency functions run first.
        scraper_instance = Scraper()
        (
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        ) = scraper_instance.set_defaults(
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        )
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        session = scraper_instance.create_session(logger, ssl)
        main_page_html, main_soup = scraper_instance.scrape_main_page(
            base_url, odyssey_version, session, notes, logger, ms_wait
        )
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(
            base_url,
            odyssey_version,
            main_page_html,
            main_soup,
            session,
            logger,
            ms_wait,
            court_calendar_link_text,
        )
        judicial_officers, judicial_officer_to_ID = scraper_instance.scrape_jo_list(
            odyssey_version, search_soup, judicial_officers, logger
        )
        log(f"Number of judicial officers found: {len(judicial_officers)}")
        self.assertIsNotNone(
            judicial_officers,
            "No judicial officers came through. judicial_officers = None.",
        )
        self.assertTrue(
            type(judicial_officers) == list,
            "The judicial_officers variable is not a list but it should be.",
        )
        self.assertIsNotNone(
            judicial_officer_to_ID,
            "No judicial officers IDs came through. judicial_officers_to_ID = None.",
        )
        self.assertTrue(
            type(judicial_officer_to_ID) == dict,
            "The judicial_officers_to_ID variable is not a dictionary but it should be.",
        )

    def test_scrape_results_page(
        self,
        odyssey_version=2003,
        county="hays",
        base_url=r"http://public.co.hays.tx.us/",
        search_url=r"http://public.co.hays.tx.us/Search.aspx?ID=900",
        hidden_values=None,
        JO_id="39607",  # 'Boyer, Bruce'
        date_string="07-01-2024",
        notes="",
        ms_wait=None,
        start_date=None,
        end_date=None,
        court_calendar_link_text=None,
        case_number=None,
        ssl=True,
        case_html_path=None,
    ):
        # Read in the test 'hidden values' that are necessary for searching a case
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "test_files",
                "test_hidden_values.txt",
            ),
            "r",
            encoding="utf-8",
        ) as file_handle:
            hidden_values = (
                file_handle.read()
            )  # Read the entire file content into a string
        hidden_values = hidden_values.replace("'", '"')
        hidden_values = json.loads(hidden_values)
        scraper_instance = Scraper()
        (
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        ) = scraper_instance.set_defaults(
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        )
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        session = scraper_instance.create_session(logger, ssl)
        # Open the example main page HTML
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "test_files",
                "hays_main_page.html",
            ),
            "r",
            encoding="utf-8",
        ) as file_handle:
            main_page_html = (
                file_handle.read()
            )  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")

        # This test requires that certain dependency functions run first.
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(
            base_url,
            odyssey_version,
            main_page_html,
            main_soup,
            session,
            logger,
            ms_wait,
            court_calendar_link_text,
        )
        results_html, results_soup = scraper_instance.scrape_results_page(
            odyssey_version,
            base_url,
            search_url,
            hidden_values,
            JO_id,
            date_string,
            session,
            logger,
            ms_wait,
        )
        self.assertIsNotNone(
            results_soup, "No results page HTML came through. results_soup = None."
        )
        self.assertTrue(
            "Record Count" in results_html,
            "'Record Count' was not the results page HTML, but it should have been.",
        )  # Note: This is already validated by "verification_text" within the request_page_with_retry function.
        # TODO: Add more validation here of what one should expect from the results page HTML.

    # This unit test for scrape_cases also covers unit testing for scrape_case_data_pre2017 and scrape_case_data_post2017. Only one or the other is used, and scrape_cases is mostly the pre or post2017 code.
    # In the future unit tests could be written for:
    # def scrape_case_data_pre2017()
    # def scrape_case_data_post2017()

    @unittest.skipIf(SKIP_SLOW, "slow")
    def test_scrape_multiple_cases(
        self,
        county="hays",
        odyssey_version=2003,
        base_url=r"http://public.co.hays.tx.us/",
        search_url=r"https://public.co.hays.tx.us/Search.aspx?ID=900",
        hidden_values=None,
        judicial_officers=["Boyer, Bruce"],
        judicial_officer_to_ID={"Boyer, Bruce": "39607"},
        JO_id="39607",
        date_string="07-01-2024",
        court_calendar_link_text=None,
        case_number=None,
        ms_wait=200,
        start_date="2024-07-01",
        end_date="2024-07-01",
        case_html_path=os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "resources",
            "test_files",
            "test_data",
            "hays",
            "case_html",
        ),
        ssl=True,
    ):
        # This starts a timer to compare the run start time to the last updated time of the resulting HTML to ensure the HTML was created after run start time
        now = datetime.now()

        # makes the test directory
        os.makedirs(case_html_path, exist_ok=True)

        # Open the example main page HTML
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "test_files",
                "hays_main_page.html",
            ),
            "r",
            encoding="utf-8",
        ) as file_handle:
            main_page_html = (
                file_handle.read()
            )  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")

        # Read in the test 'hidden values' that are necessary for searching a case
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "test_files",
                "test_hidden_values.txt",
            ),
            "r",
            encoding="utf-8",
        ) as file_handle:
            hidden_values = (
                file_handle.read()
            )  # Read the entire file content into a string
        hidden_values = hidden_values.replace("'", '"')
        hidden_values = json.loads(hidden_values)

        # There are some live depency functions that have to be run before the primary code can be run.
        scraper_instance = Scraper()
        (
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        ) = scraper_instance.set_defaults(
            ms_wait,
            start_date,
            end_date,
            court_calendar_link_text,
            case_number,
            ssl,
            county,
            case_html_path,
        )
        logger = scraper_instance.configure_logger()
        session = scraper_instance.create_session(logger, ssl)
        case_html_path = (
            scraper_instance.make_directories(county)
            if not case_html_path
            else case_html_path
        )
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(
            base_url,
            odyssey_version,
            main_page_html,
            main_soup,
            session,
            logger,
            ms_wait,
            court_calendar_link_text,
        )
        results_html, results_soup = scraper_instance.scrape_results_page(
            odyssey_version,
            base_url,
            search_url,
            hidden_values,
            JO_id,
            date_string,
            session,
            logger,
            ms_wait,
        )
        scraper_instance.scrape_multiple_cases(
            county,
            odyssey_version,
            base_url,
            search_url,
            hidden_values,
            judicial_officers,
            judicial_officer_to_ID,
            case_html_path,
            logger,
            session,
            ms_wait,
            start_date,
            end_date,
        )

        # Test #1: Did the scraper create a new file called test_12947592.html in the right location?
        # This creates the file path, checks to see if the HTML file is there, and then checks to see that HTML file has been updated since the program started running.
        test_case_html_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "resources",
            "test_files",
            "test_data",
            "hays",
            "case_html",
            "12947592.html",
        )
        self.assertTrue(
            os.path.isfile(test_case_html_path),
            "There is no HTML file the correct name in the correct folder.",
        )
        # This gets the time the file was last updated and converts it from unix integer to date time
        test_html_updated_time = os.path.getmtime(test_case_html_path)
        seconds = int(test_html_updated_time)
        microseconds = int((test_html_updated_time - seconds) * 1e6)
        test_html_updated_time = datetime.fromtimestamp(seconds) + timedelta(
            microseconds=microseconds
        )
        self.assertTrue(
            test_html_updated_time > now,
            "This HTML has not been updated since this test started running.",
        )

        # Test #2: Is the resulting HTML file longer than 1000 characters?
        with open(test_case_html_path, "r") as file_handle:
            case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")
        self.assertTrue(
            len(case_soup.text) > 1000,
            "This HTML is smaller than 1000 characters and may be an error.",
        )

        # Test #3: Does the resulting HTML file container the cause number in the expected header location?
        self.assertTrue(test_html_updated_time > now)
        # Parse the HTML in the expected location for the cause number.
        case_number_html = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
            0
        ].text
        self.assertTrue(
            case_number_html == "CR-16-0002-A",
            "The cause number is not where it was expected to be in the HTML.",
        )
        # self.logger.info(f"Scraper test sucessful for cause number CR-16-0002-A.")


class ParseTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.case_json_path = os.path.join(self.test_dir, "hays", "case_json")
        os.makedirs(self.case_json_path, exist_ok=True)

        self.mock_logger = MagicMock()
        self.parser_instance = Parser()
        self.case_html_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../resources/test_files/parser_testing"
            )
        )

    @patch("parser.Parser.get_class_and_method")
    def test_parser_class_and_method(self, mock_import_module):
        mock_logger = MagicMock()
        mock_class = MagicMock()
        mock_method = MagicMock()

        mock_import_module.return_value = mock_class.return_value, mock_method

        parser_instance = Parser()

        instance, method = parser_instance.get_class_and_method(
            logger=mock_logger, county="hays", test=True
        )

        self.assertEqual(instance, mock_class.return_value)
        self.assertEqual(method, mock_method)

    @patch("os.makedirs")
    def test_parser_directories_single_file(self, mock_makedirs):
        mock_logger = MagicMock()
        parser_instance = Parser()
        case_html_path, case_json_path = parser_instance.get_directories(
            "hays", mock_logger, parse_single_file=True
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        expected_path = os.path.join(base_dir, "resources", "test_files")

        self.assertEqual(case_html_path, expected_path)
        self.assertEqual(case_json_path, expected_path)
        mock_logger.info.assert_called()

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    def test_parser_directories_multiple_files(self, mock_exists, mock_makedirs):
        mock_logger = MagicMock()
        parser_instance = Parser()
        case_html_path, case_json_path = parser_instance.get_directories(
            "hays", mock_logger, parse_single_file=False
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        expected_html_path = os.path.join(base_dir, "data", "hays", "case_html")
        expected_json_path = os.path.join(base_dir, "data", "hays", "case_json")

        self.assertEqual(case_html_path, expected_html_path)
        self.assertEqual(case_json_path, expected_json_path)
        mock_makedirs.assert_called_once_with(expected_json_path, exist_ok=True)
        mock_logger.info.assert_called()

    def test_parser_list_of_single_html_file(self):
        case_number = "51652356"
        case_list = self.parser_instance.get_list_of_html(
            self.case_html_path,
            case_number,
            "hays",
            self.mock_logger,
            parse_single_file=True,
        )

        relative_path = os.path.join(project_root, "resources", "test_files")

        expected_path = os.path.join(relative_path, f"test_{case_number}.html")

        self.assertEqual(case_list, [expected_path])
        self.mock_logger.info.assert_called()

    def test_parser_list_of_single_html_file_by_casenumber(self):
        case_number = "51652356"

        case_list = self.parser_instance.get_list_of_html(
            self.case_html_path,
            case_number,
            "hays",
            self.mock_logger,
            parse_single_file=True,
        )

        relative_path = os.path.join(project_root, "resources", "test_files")

        expected_list = [os.path.join(relative_path, f"test_{case_number}.html")]

        self.assertEqual(case_list, expected_list)
        self.mock_logger.info.assert_called()

    @patch("os.path.join", side_effect=lambda *args: "\\".join(args))
    def test_parser_list_of_multiple_html_files(self, mock_join):
        os.makedirs(self.case_html_path, exist_ok=True)

        with open(os.path.join(self.case_html_path, "test_1.html"), "w") as f:
            f.write("test")
        with open(os.path.join(self.case_html_path, "test_2.html"), "w") as f:
            f.write("test")

        updated_html_path = os.path.join(self.case_html_path, "multiple_html_files")
        case_number = ""
        case_list = self.parser_instance.get_list_of_html(
            updated_html_path,
            case_number,
            "hays",
            self.mock_logger,
            parse_single_file=False,
        )

        expected_list = [
            os.path.join(updated_html_path, "test_1.html"),
            os.path.join(updated_html_path, "test_2.html"),
        ]

        self.assertEqual(set(case_list), set(expected_list))
        self.mock_logger.info.assert_called()

    def test_parser_get_list_of_html_error_handling(self):
        invalid_path = "invalid/path"
        case_number = "12345"

        with self.assertRaises(Exception):
            self.parser_instance.get_list_of_html(
                invalid_path,
                case_number,
                "hays",
                self.mock_logger,
                parse_single_file=False,
            )
        self.mock_logger.info.assert_called()

    @patch("os.path.join")
    @patch("logging.getLogger")
    def test_get_html_path(self, mock_logger, mock_path_join):
        updated_html_path = os.path.join(self.case_html_path, "multiple_html_files")
        case_html_file_name = "parserTest_51652356.html"
        case_number = "51652356"

        mock_path_join.return_value = f"{updated_html_path}/{case_html_file_name}"

        result = self.parser_instance.get_html_path(
            updated_html_path, case_html_file_name, case_number, self.mock_logger
        )

        self.assertEqual(result, f"{updated_html_path}/{case_html_file_name}")

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dumps")
    @patch("parser.logging.getLogger")
    def test_write_json_data(self, mock_logger, mock_json_dumps, mock_open_func):
        case_json_path = "/mock/path"
        case_number = "123456"
        case_data = {"data": "value"}

        self.parser_instance.write_json_data(
            case_json_path, case_number, case_data, mock_logger
        )

        mock_open_func.assert_called_once_with(
            os.path.join(case_json_path, case_number + ".json"), "w"
        )
        mock_json_dumps.assert_called_once_with(case_data, indent=4)

    @patch("builtins.open", new_callable=mock_open)
    @patch("parser.logging.getLogger")
    def test_write_error_log(self, mock_logger, mock_open_func):
        county = "hays"
        case_number = "123456"

        self.parser_instance.write_error_log(county, case_number)

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        error_log_path = os.path.join(
            base_dir, "data", county, "cases_with_parsing_error.txt"
        )

        mock_open_func.assert_called_once_with(error_log_path, "w")

    def test_parser_end_to_end(self, county="hays", case_number='123456'):

        parser = Parser()
        parser.parse(county=county, 
                     case_number=case_number, 
                     parse_single_file=True,
                     test = True)

class CleanTestCase(unittest.TestCase):
    def test_cleaner_hays(self):
        now = datetime.now()
        now_string = now.strftime("%H:%M:%S")
        # Call the function being tested
        # cleaner(counter="hays")

        # Need to finish coding this.

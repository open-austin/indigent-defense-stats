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
from .. import scraper
from .. import parser
from .. import cleaner
from .. import updater

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)

SKIP_SLOW = os.getenv("SKIP_SLOW", "false").lower().strip() == "true"


def log(
    message, level="INFO"
):  # Provide message and info level (optional, defaulting to info)
    # configure the logger
    log = logging.getLogger(__name__)
    log.info(message)


class ScraperTestCase(unittest.TestCase):
    # Defaults for each program are set at the function level.

    def test_scrape_get_ody_link(self, county="hays"):
        scraper_instance = scraper.Scraper()
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
        scraper_instance = scraper.Scraper()
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
        scraper_instance = scraper.Scraper()
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
        scraper_instance = scraper.Scraper()
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
        scraper_instance = scraper.Scraper()
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
        # self.logger.info(f"scraper.Scraper test sucessful for cause number CR-16-0002-A.")

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
        scraper_instance = scraper.Scraper()
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
        scraper_instance = scraper.Scraper()
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
        scraper_instance = scraper.Scraper()
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

        self.mock_logger = logging.getLogger(__name__)
        self.parser_instance = parser.Parser()
        self.case_html_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../resources/test_files/parser_testing"
            )
        )

    def test_parser_class_and_method(self):
        parser_instance = parser.Parser()

        instance, method = parser_instance.get_class_and_method(
            logger=self.mock_logger, county="hays", test=True
        )
        self.assertIn('extract_rows', dir(instance))

    @patch("os.makedirs")
    def test_parser_directories_single_file(self, mock_makedirs):
        parser_instance = parser.Parser()
        case_html_path, case_json_path = parser_instance.get_directories(
            "hays", self.mock_logger, parse_single_file=True
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        expected_path = os.path.join(base_dir, "resources", "test_files")

        self.assertEqual(case_html_path, expected_path)
        self.assertEqual(case_json_path, expected_path)

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    def test_parser_directories_multiple_files(self, mock_exists, mock_makedirs):
        parser_instance = parser.Parser()
        case_html_path, case_json_path = parser_instance.get_directories(
            "hays", self.mock_logger, parse_single_file=False
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        expected_html_path = os.path.join(base_dir, "data", "hays", "case_html")
        expected_json_path = os.path.join(base_dir, "data", "hays", "case_json")

        self.assertEqual(case_html_path, expected_html_path)
        self.assertEqual(case_json_path, expected_json_path)
        mock_makedirs.assert_called_once_with(expected_json_path, exist_ok=True)

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

    def test_parser_list_of_multiple_html_files(self):
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

    def test_get_html_path(self):
        updated_html_path = os.path.join(self.case_html_path, "multiple_html_files")
        case_html_file_name = "parserTest_51652356.html"
        case_number = "51652356"

        result = self.parser_instance.get_html_path(
            updated_html_path, case_html_file_name, case_number, self.mock_logger
        )

        self.assertEqual(result, f"{updated_html_path}/{case_html_file_name}")

    @patch("builtins.open", new_callable=mock_open)
    def test_write_json_data(self, mock_open_func):
        case_json_path = "/mock/path"
        case_number = "123456"
        case_data = {"data": "value"}

        self.parser_instance.write_json_data(
            case_json_path, case_number, case_data, self.mock_logger
        )

        mock_open_func.assert_called_once_with(
            os.path.join(case_json_path, case_number + ".json"), "w"
        )

    @patch("builtins.open", new_callable=mock_open)
    def test_write_error_log(self, mock_open_func):
        county = "hays"
        case_number = "123456"

        self.parser_instance.write_error_log(county, case_number)

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        error_log_path = os.path.join(
            base_dir, "data", county, "cases_with_parsing_error.txt"
        )

        mock_open_func.assert_called_once_with(error_log_path, "w")

    def test_parser_end_to_end(self, county="hays", case_number='123456'):

        self.parser_instance.parse(county=county, 
                     case_number=case_number, 
                     parse_single_file=True,
                     test = True)

class CleanTestCase(unittest.TestCase):
    def setUp(self):
        self.cleaner = Cleaner() # Create Cleaner instance here to avoid repeating this in every test

    @patch('os.makedirs') 
    @patch('os.path.exists', return_value=False)
    def test_get_or_create_folder_path(self, mock_exists, mock_makedirs):
        mock_exists.return_value = False
        county = "hays"
        folder_type = "case_json"
        cleaner_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cleaner"))
        expected_path = os.path.join(cleaner_dir, "..", "..", "data", county, folder_type)

        folder_path = self.cleaner.get_or_create_folder_path(county, folder_type)

        mock_exists.assert_called_once_with(expected_path)  # Check if os.path.exists was called
        mock_makedirs.assert_called_once_with(expected_path)  # Check if os.makedirs was called
        self.assertEqual(folder_path, expected_path)  # Check that the path is correct

        # Test when folder already exists
        mock_exists.return_value = True
        folder_path = self.cleaner.get_or_create_folder_path(county, folder_type)
        mock_makedirs.assert_called_once() # Should not be called again

    def test_load_json_file(self):
        # Test successful load
        with patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}'):
            result = self.cleaner.load_json_file("fake_path.json")
            self.assertEqual(result, {"key": "value"})

        # Test file not found
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = self.cleaner.load_json_file("nonexistent.json")
            self.assertEqual(result, {})
        
        # Test invalid JSON
        with patch("builtins.open", new_callable=mock_open, read_data='invalid json'):
            result = self.cleaner.load_json_file("invalid.json")
            self.assertEqual(result, {})

    def test_load_and_map_charge_names(self):
        # Test successful mapping
        test_data = '[{"charge_name": "Charge1", "details": "Some details"}]'
        with patch("builtins.open", new_callable=mock_open, read_data=test_data):
            result = self.cleaner.load_and_map_charge_names("fake_path.json")
            self.assertEqual(result, {"Charge1": {"charge_name": "Charge1", "details": "Some details"}})

        # Test empty file
        with patch("builtins.open", new_callable=mock_open, read_data='[]'):
            with self.assertRaises(FileNotFoundError):
                self.cleaner.load_and_map_charge_names("empty.json")

        # Test file not found
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                self.cleaner.load_and_map_charge_names("nonexistent.json")

    def test_hash_defense_attorney(self):
        input_data = {
            "party information": {
                "defense attorney": "John Doe",
                "defense attorney phone number": "555-1234"
            }
        }
        result = self.cleaner.hash_defense_attorney(input_data)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "John Doe:555-1234")

        # Test consistency
        result2 = self.cleaner.hash_defense_attorney(input_data)
        self.assertEqual(result, result2)

        # Test different input
        input_data2 = {
            "party information": {
                "defense attorney": "Jane Doe",
                "defense attorney phone number": "555-5678"
            }
        }
        result3 = self.cleaner.hash_defense_attorney(input_data2)
        self.assertNotEqual(result, result3)

        # Test missing data
        input_data3 = {"party information": {}}
        result4 = self.cleaner.hash_defense_attorney(input_data3)
        self.assertEqual(result4, "")

    def test_redact_cause_number(self):
        # Test case 1: Normal input and consistency
        input_dict = {"code": "123-ABC-456"}
        result1 = self.cleaner.redact_cause_number(input_dict)
        result2 = self.cleaner.redact_cause_number(input_dict)
    
        self.assertIsInstance(result1, str)
        self.assertEqual(len(result1), 16)  # xxHash produces a 16-character hexadecimal string
        self.assertEqual(result1, result2)  # Ensure consistent hashing
    
        # Test case 2: Different input produces different hash
        input_dict2 = {"code": "789-XYZ-012"}
        result3 = self.cleaner.redact_cause_number(input_dict2)
        self.assertNotEqual(result1, result3)
    
        # Test case 3: Empty input
        self.assertNotEqual(self.cleaner.redact_cause_number({"code": ""}), result1)
    
        # Test case 4: Missing 'code' key
        with self.assertRaises(KeyError):
            self.cleaner.redact_cause_number({})

    def test_process_charges(self):
        charges = [
            {"level": "Misdemeanor", "charges": "Charge1", "statute": "123", "date": "12/01/2023"},
            {"level": "Felony", "charges": "Charge2", "statute": "456", "date": "11/15/2023"},
        ]
        charge_mapping = {
            "Charge1": {"mapped_field": "mapped_value1"},
            "Charge2": {"mapped_field": "mapped_value2"}
        }

        processed_charges, earliest_date = self.cleaner.process_charges(charges, charge_mapping)

        self.assertEqual(len(processed_charges), 2)
        self.assertEqual(processed_charges[0]['charge_date'], "2023-12-01")
        self.assertEqual(processed_charges[1]['charge_date'], "2023-11-15")
        self.assertEqual(earliest_date, "2023-11-15")

        # Test invalid date
        charges_invalid_date = [{"level": "Misdemeanor", "charges": "Charge1", "statute": "123", "date": "invalid"}]
        processed_charges, earliest_date = self.cleaner.process_charges(charges_invalid_date, charge_mapping)
        self.assertEqual(len(processed_charges), 0)
        self.assertEqual(earliest_date, "")
    
    def test_contains_good_motion(self):
        self.assertTrue(self.cleaner.contains_good_motion("Motion To Suppress", "Event: Motion To Suppress"))
        self.assertTrue(self.cleaner.contains_good_motion("Motion To Suppress", ["Other", "Motion To Suppress"]))
        self.assertFalse(self.cleaner.contains_good_motion("Motion To Suppress", "Other Motion"))
        self.assertFalse(self.cleaner.contains_good_motion("Motion To Suppress", ["Other1", "Other2"]))

    def test_find_good_motions(self):
        events = [
            "Motion To Suppress",
            "Motion to Reduce Bond",
            "Other Event",
            "Motion For Speedy Trial"
        ]

        result = self.cleaner.find_good_motions(events, GOOD_MOTIONS)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["Motion To Suppress", "Motion to Reduce Bond", "Motion For Speedy Trial"])

        # Test with no matching motions
        events_no_match = ["Other1", "Other2"]
        result_no_match = self.cleaner.find_good_motions(events_no_match, GOOD_MOTIONS)
        self.assertEqual(result_no_match, [])

    @patch("cleaner.Cleaner.load_json_file")
    @patch("cleaner.Cleaner.write_json_output")
    @patch("cleaner.Cleaner.load_and_map_charge_names")
    def test_process_single_case(self, mock_load_map, mock_write, mock_load):
        mock_load.return_value = {
            "code": "123",
            "county": "test_county",
            "party information": {
                "defense attorney": "John Doe",
                "defense attorney phone number": "555-1234",
                "appointed or retained": "appointed"
            },
            "charge information": [
                {"level": "Misdemeanor", "charges": "Charge1", "statute": "123", "date": "12/01/2023"}
            ],
            "other events and hearings": ["Motion To Suppress"],
            "html_hash": "test_hash"
        }
        mock_load_map.return_value = {"Charge1": {"mapped_field": "mapped_value"}}

        county = "test_county"
        folder_path = "case_json_folder"
        case_file = "case1.json"

        self.cleaner.process_single_case(county, folder_path, case_file)

        mock_load.assert_called_once()
        mock_write.assert_called_once()

        # Check that the output contains expected fields
        output_data = mock_write.call_args[0][1]
        self.assertTrue("case_number" in output_data)
        self.assertTrue("charges" in output_data)
        self.assertTrue("motions" in output_data)
        self.assertTrue("defense_attorney" in output_data)
        self.assertTrue("county" in output_data)
        self.assertTrue("html_hash" in output_data)
        self.assertTrue("attorney_type" in output_data)
        self.assertTrue("earliest_charge_date" in output_data)
        self.assertTrue("has_evidence_of_representation" in output_data)
        self.assertTrue("parsing_date" in output_data)

    @patch("os.listdir", return_value=["case1.json", "case2.json"])
    @patch("cleaner.Cleaner.get_or_create_folder_path")
    @patch("cleaner.Cleaner.process_single_case")
    def test_process_json_files(self, mock_process, mock_get_folder, mock_listdir):
        county = "test_county"
        folder_path = "case_json_folder"
        mock_get_folder.return_value = "cleaned_folder_path"

        self.cleaner.process_json_files(county, folder_path)

        mock_get_folder.assert_called_once_with(county, "case_json_cleaned")
        self.assertEqual(mock_process.call_count, 2)
        mock_process.assert_any_call(folder_path, "case1.json", "cleaned_folder_path")
        mock_process.assert_any_call(folder_path, "case2.json", "cleaned_folder_path")

    @patch("json.dump")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_json_output(self, mock_file, mock_json_dump):
        file_path = "test_output.json"
        data = {"key": "value"}
        self.cleaner.write_json_output(file_path, data)

        mock_file.assert_called_once_with(file_path, "w")
        mock_json_dump.assert_called_once_with(data, mock_file())

    @patch.object(Cleaner, 'get_or_create_folder_path')
    @patch.object(Cleaner, 'process_json_files')
    def test_clean(self, mock_process_json_files, mock_get_folder):
        mock_get_folder.return_value = "mock_path"
        county = "hays"

        with self.assertLogs(level='INFO') as log:
            self.cleaner.clean(county)

        self.assertTrue(f"INFO:root:Processing data for county: {county}" in log.output)
        self.assertTrue(f"INFO:root:Completed processing for county: {county}" in log.output)

        mock_get_folder.assert_called_once_with(county, "case_json")
        mock_process_json_files.assert_called_once_with(county, "mock_path")

        # Test exception handling
        mock_process_json_files.side_effect = Exception("Test error")
        with self.assertLogs(level='ERROR') as log:
            self.cleaner.clean(county)
        self.assertIn(f"ERROR:root:Error during cleaning process for county: {county}. Error: Test error", log.output)
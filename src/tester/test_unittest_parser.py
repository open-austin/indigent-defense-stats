from datetime import datetime, timedelta
import unittest
import sys
import os
import json
import logging
from unittest.mock import patch, MagicMock, mock_open
import tempfile
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))

current_dir = os.path.dirname(os.path.abspath(__file__))
print(f'current directory: {current_dir}')
# Import all of the programs modules within the parent_dir
import scraper
import parser
import cleaner
import updater

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)

SKIP_SLOW = os.getenv("SKIP_SLOW", "false").lower().strip() == "true"

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

        self.assertEqual(result, f"{os.path.join(updated_html_path,case_html_file_name)}")

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
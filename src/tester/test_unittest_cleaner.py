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

class CleanTestCase(unittest.TestCase):
    def setUp(self):
        self.cleaner = cleaner.Cleaner() # Create Cleaner instance here to avoid repeating this in every test

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
        self.assertEqual(result, result3)

        # Test missing data
        input_data3 = {"party information": {}}
        result4 = self.cleaner.hash_defense_attorney(input_data3)
        self.assertEqual(result4, "")

    def test_redact_cause_number(self):
        # Test case 1: Normal input and consistency
        input_dict = {"Case Metadata":{"code": "123-ABC-456"}}
        result1 = self.cleaner.redact_cause_number(input_dict)
        result2 = self.cleaner.redact_cause_number(input_dict)
    
        self.assertIsInstance(result1, str)
        self.assertEqual(len(result1), 16)  # xxHash produces a 16-character hexadecimal string
        self.assertEqual(result1, result2)  # Ensure consistent hashing
    
        # Test case 2: Different input produces different hash
        input_dict2 = {"Case Metadata":{"code": "789-XYZ-012"}}
        result3 = self.cleaner.redact_cause_number(input_dict2)
        self.assertNotEqual(result1, result3)
    
        # Test case 3: Empty input
        self.assertNotEqual(self.cleaner.redact_cause_number({"Case Metadata":{"code": ""}}), result1)
    
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

        result = self.cleaner.find_good_motions(events, cleaner.GOOD_MOTIONS)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["Motion To Suppress", "Motion to Reduce Bond", "Motion For Speedy Trial"])

        # Test with no matching motions
        events_no_match = ["Other1", "Other2"]
        result_no_match = self.cleaner.find_good_motions(events_no_match, cleaner.GOOD_MOTIONS)
        self.assertEqual(result_no_match, [])

    def test_process_single_case(self):
        county = "hays"
        input_folder_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "test_files")
        case_file = "test_123456.json"
        output_folder_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "test_files", "cleaned_test_json")

        self.cleaner.process_single_case(input_folder_path, case_file, output_folder_path)

        output_file_path = os.path.join(output_folder_path, case_file)

        with open(output_file_path, 'r') as f:
            output_data = json.load(f)
            self.assertTrue("Case Metadata" in output_data)
            self.assertTrue("Defendant Information" in output_data)
            self.assertTrue("Charge Information" in output_data)
            self.assertTrue("Case Details" in output_data)
            self.assertTrue("parsing_date" in output_data)
            self.assertTrue("html_hash" in output_data)
            self.assertTrue("Good Motions" in output_data)
            self.assertTrue("cause_number_redacted" in output_data)

    # Will need 
    """@patch("os.listdir", return_value=["case1.json", "case2.json"])
    @patch("src.cleaner.Cleaner.get_or_create_folder_path")
    @patch("src.cleaner.Cleaner.process_single_case")
    def test_process_json_files(self, mock_process, mock_get_folder, mock_listdir):
        county = "test_county"
        folder_path = "case_json_folder"
        mock_get_folder.return_value = "cleaned_folder_path"

        self.cleaner.process_json_files(county, folder_path)

        mock_get_folder.assert_called_once_with(county, "case_json_cleaned")
        self.assertEqual(mock_process.call_count, 2)
        mock_process.assert_any_call(folder_path, "case1.json", "cleaned_folder_path")
        mock_process.assert_any_call(folder_path, "case2.json", "cleaned_folder_path")"""

    @patch.object(cleaner.Cleaner, 'get_or_create_folder_path')
    @patch.object(cleaner.Cleaner, 'process_json_files')
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
import unittest, sys, os, json, warnings
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import all of the programs modules within the parent_dir
from scraper.__main__  import scraper
from parser.__main__  import parser
from cleaner.__main__  import cleaner
from updater.__main__  import updater

class ScraperTestCase(unittest.TestCase):
    
    def test_scraper_hays(self):
        now = datetime.now()
        now_string = now.strftime("%H:%M:%S")
        # Call the function being tested
        scraper_instance = scraper('hays', '2024-07-01', '2024-07-01', 'CR-16-0002-A')
        scraper_instance.scrape()

        # Test #1: Did the scraper create a new file called 12947592.html in the right location?
            #This creates the file path, checks to see if the HTML file is there, and then checks to see that HTML file has been updated since the program started running.
        test_case_html_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", 'hays', "case_html",'12947592.html')
        self.assertEqual(os.path.isfile(test_case_html_path), True, "There is no HTML file the correct name in the correct folder.")
            #This gets the time the file was last updated and converts it from unix integer to date time
        test_html_updated_time = os.path.getmtime(test_case_html_path)
        seconds = int(test_html_updated_time)
        microseconds = int((test_html_updated_time - seconds) * 1e6)
        test_html_updated_time = datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds)
        test_html_updated_time_string = test_html_updated_time.strftime("%H:%M:%S")
        self.assertEqual(test_html_updated_time > now, True)

        # Test #2: Is the resulting HTML file longer than 1000 characters?
        with open(test_case_html_path, "r") as file_handle:
            case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")   
        self.assertEqual(len(case_soup.text) > 1000, True, "This HTML is smaller than 1000 characters and may be an error.")

        # Test #3: Does the resulting HTML file container the cause number in the expected header location?
        self.assertEqual(test_html_updated_time > now, True)
        # Parse the HTML in the expected location for the cause number.
        case_number_html = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[0].text
        self.assertEqual(case_number_html=='CR-16-0002-A', True, "The cause number is not where it was expected to be in the HTML.")
        #self.logger.info(f"Scraper test sucessful for cause number CR-16-0002-A.")

class ParseTestCase(unittest.TestCase):

    def test_parser_hays(self):

        now = datetime.now()
        now_string = now.strftime("%H:%M:%S")
        # Call the function being tested
        parser_instance = parser(county = 'hays', case_number = '51652356', test = True)
        parser_instance.parse()
        # Test #1: Check to see if there is a JSON called 51652356.json created in the correct location and that it was updated since this test started running
        test_case_json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", 'hays', "case_json",'51652356.json')
        self.assertEqual(os.path.isfile(test_case_json_path), True, "There is no JSON file the correct name in the correct folder.")
            #This gets the time the file was last updated and converts it from unix integer to date time
        test_json_updated_time = os.path.getmtime(test_case_json_path)
        seconds = int(test_json_updated_time)
        microseconds = int((test_json_updated_time - seconds) * 1e6)
        test_json_updated_time = datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds)
        test_json_updated_time_string = test_json_updated_time.strftime("%H:%M:%S")
        self.assertEqual(test_json_updated_time > now, True)

        # Test #2: Check to see that JSON parsed all of the necessary fields and did so properly. 

        #Run the json against the field validation database
        def validate_field(field):
            
            # This locates where a field should be in the JSON based on its logical level (top level, charge level, party level, etc.) 
            def field_locator(logical_level):
                if logical_level == 'top':
                    location = json_dict
                elif logical_level == 'party':
                    location = json_dict['party information']
                elif logical_level == 'charge': # This only looks at the first charge in the JSON
                    location = json_dict['charge information'][0]
                return location
            
            def check_exists(field_name, logical_level, importance):
                location = field_locator(logical_level)
                # Check for the field in the expected location: Raise error if not present if field 'necessary' but only raise warning otherwise
                if importance == 'necessary':
                    message = f"The '{field_name}' field has '{importance}' importance but is missing."
                    self.assertEqual(field_name in location, True, message)
                if importance == 'high' or importance == 'medium':
                    if field_name not in location:
                        message = f"The '{field_name}' field has {importance} importance but is missing."
                        warnings.warn(message, UserWarning)
                if importance == 'low':
                    # Don't bother checking.
                    pass

            def check_length(field_name, logical_level, importance, estimated_min_length):
                location = field_locator(logical_level)
                #Gets the length of the field and the field's text using the dynamic location.
                field_text = location[field_name]
                field_length = len(field_text)
                # Check for the expected length of the field: Raise error if too short if field 'necessary' but only raise warning otherwise
                if importance == 'necessary':
                    message = f"This necessary field called '{field_name}' was expected to be more than {estimated_min_length} but it is actually {field_length}: {field_text}."
                    self.assertEqual(field_length < estimated_min_length, False, message)
                if importance == 'high' or importance == 'medium':
                    message = f"The '{field_name}' field has an estimated minimum length of {estimated_min_length} characters, but it instead has {field_length} characters. {importance}"
                    if field_length < estimated_min_length:
                        warnings.warn(message, UserWarning)
                if importance == 'low':
                    #Don't bother checking.
                    pass

            check_exists(
                field_name = field['name'],
                logical_level = field['logical_level'],
                importance = field['importance'])
            
            check_length(
                field_name = field['name'], 
                logical_level = field['logical_level'],
                importance = field['importance'],
                estimated_min_length = field['estimated_min_length'])

        #Opening the test json
        with open(test_case_json_path, "r") as f:
            json_dict = json.load(f)

        #Opening the field validation json with expected fields and their features 
        FIELDS_VALIDATION_DICT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'field_validation_list.json')
        with open(FIELDS_VALIDATION_DICT_PATH, "r") as f:
            FIELDS_VALIDATION_DICT = json.load(f)

        for field in FIELDS_VALIDATION_DICT:
            print(f"validating field: {field['name']}")
            validate_field(field)
        print(f'Field validation complete for {len(FIELDS_VALIDATION_DICT)} fields.')

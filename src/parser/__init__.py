import os
import csv
import json
import traceback
import xxhash
from time import time
import sys
import importlib
from bs4 import BeautifulSoup

class Parser:

    def __init__(self):
        pass

    def get_class_and_method(self, county):
        # Construct the module, class, and method names
        module_name = county #ex: 'hays'
        class_name = f"Parser{county.capitalize()}" #ex: 'ParserHays'
        method_name = f"parser_{county}" #ex: 'parser_hays'
        
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

    def get_directories(self, county, test):
        #TODO: Check for dependencies. Raise if county is missing.
        if not test:
            case_html_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", county, "case_html"
            )
            case_json_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", county, "case_json"
            )
            if not os.path.exists(case_json_path):
                os.makedirs(case_json_path, exist_ok=True)
        else: # if test = True
            case_html_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "resources", 'test_files', 'test_data', county, "case_html"
            )
            case_json_path = os.path.join(
                os.path.dirname(__file__),  "..", "..", "resources", 'test_files', 'test_data', county, "case_json"
            )
            if not os.path.exists(case_json_path):
                os.makedirs(case_json_path, exist_ok=True)        
        return case_html_path, case_json_path


    def get_list_of_html(self, case_html_path, case_number, county, test):
        # This will loop through the html in the folder they were scraped to.
        case_html_list = os.listdir(case_html_path)

        # However, if an optional case number is passed to the function, then read in the case number html file from the data folder 
        #   -Assumes that the requested parsed case number has been scraped to html

        if case_number:
            #Replace the entire set of HTML files to parse to just the one file path of the requested case number.
            case_html_list = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", county, "case_html", case_number + 'html'
            )
            # If this is a test then use the file path to the redacted test json file in the resources folder.
            if test:
                case_html_list = [case_number + '.html']
        return case_html_list

    def get_html_path(self, case_html_path, case_html_file_name, case_number, test):
        # This will change the file path to look at the test function if it is a test. 
        if test:
            case_html_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files', 'test_'+ case_number + '.html')
        else:
            case_html_file_path = os.path.join(case_html_path, case_html_file_name)
        return case_html_file_path

    def write_json_data(self, case_json_path, case_number, case_data, test):
        # Write JSON data
        if not test:
            with open(os.path.join(case_json_path, case_number + ".json"), "w") as file_handle:
                file_handle.write(json.dumps(case_data))
        else: # if test = True
            with open(os.path.join(case_json_path, 'test_'+ case_number + ".json"), "w") as file_handle:
                file_handle.write(json.dumps(case_data))

    def write_error_log(self, county, case_number):
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "data",
                county,
                "cases_with_parsing_error.txt",
            ),
            "w",
        ) as file_handle:
            file_handle.write(case_number + "\n")        

    def parse(self, county, case_number, test): #remove the test value here and just have the tests pass the test data (may have to set path)

        county = county.lower()
        # get input and output directories and make json dir if not present
        case_html_path, case_json_path = self.get_directories(county, test)
        # start 
        START_TIME_PARSER = time()

        # creating a list of json files already parsed 
        # TODO: Consider overwriting or deleting all parsed json files. When the parser is in production and parsing the same case ids 
        # repeatedly on different days, it will need to know that it SHOULD parse the case id again as it will have been updated. 
        # Perhaps there is a clean up step that removes old parsed json after each run or perhaps it overwrites.
        cached_case_json_list = [
            file_name.split(".")[0] for file_name in os.listdir(case_json_path)
        ]

        # Get a list of the HTML files that it needs to parse. This includes handling of test files.
        case_html_list = self.get_list_of_html(case_html_path, case_number, county, test)

        #Loops through all of the case html either in the folder where it was scraped, only a single case if specified, or a single test case.
        for case_html_file_name in case_html_list:
            try:
                # This will grab the case id and look for it in the cashed json and won't continue if it exists (unless it's a test)
                # TODO: Follow up with making updates here depending on if the caching is no longer used. 
                case_number = case_html_file_name.split(".")[0]
                if case_number in cached_case_json_list and test == False:
                    continue

                case_html_file_path = self.get_html_path(case_html_path, case_html_file_name, case_number, test)

                print(f"{case_number} - parsing")
                with open(case_html_file_path, "r") as file_handle:
                    case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")

                # Get the county-specific parser class and method
                parser_instance, parser_function = self.get_class_and_method(county=county)
                if parser_instance is not None and parser_function is not None:
                    case_data = parser_function(county, case_number, case_soup)
                else:
                    # Handle the case where parser_instance or parser_function is None
                    print("Error: Could not obtain parser instance or function.")

                # Adds county field to data
                case_data['county'] = county

                # Adds a hash to the JSON file of the underlying HTML
                body = case_soup.find("body")
                balance_table = body.find_all("table")[-1]
                if "Balance Due" in balance_table.text:
                    balance_table.decompose()
                case_data["html_hash"] = xxhash.xxh64(str(body)).hexdigest()

                self.write_json_data(case_json_path, case_number, case_data, test)

            except Exception:
                print(traceback.format_exc())
                self.write_error_log(county, case_number)

        RUN_TIME_PARSER = time() - START_TIME_PARSER
        print(f"Parsing took {RUN_TIME_PARSER} seconds")

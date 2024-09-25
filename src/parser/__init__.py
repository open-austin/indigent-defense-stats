import logging
import os
import csv
import json
import traceback
import xxhash
from time import time
import sys
import importlib
from bs4 import BeautifulSoup
from typing import Tuple, List, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)

class Parser:

    def __init__(self):
        pass

    def configure_logger(self):
        logger = logging.getLogger(name="pid: " + str(os.getpid()))
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("parser_log.txt"),
                logging.StreamHandler() 
            ]
        )
        logger.info("Logger configured")
        return logger
    
    def get_class_and_method(self, logger, county: str, test = False) -> Tuple[Optional[object], Optional[callable]]:
        if test:
            logger.info(f"Test mode is on")
        # Construct the module, class, and method names
        module_name = county #ex: 'hays'
        class_name = f"Parser{county.capitalize()}" #ex: 'ParserHays'
        method_name = f"parser_{county}" #ex: 'parser_hays'

        logger.info(f"Module: {module_name}\nClass: {class_name}\nMethod: {method_name}\n")

        # Add the current directory to the system path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        try:
            # Dynamically import the module
            module = importlib.import_module(module_name)

            logger.info(f"Module '{module_name}' imported successfully.")

            # Retrieve the class from the module
            cls = getattr(module, class_name)

            logger.info(f"Class '{class_name}' retrieved successfully.")

            if cls is None:
                logger.info(f"Class '{class_name}' not found in module '{module_name}'.")
                return None, None
            
            # Instantiate the class
            instance = cls()
            
            # Retrieve the method with the specified name
            method = getattr(instance, method_name, None)
            logger.info(f"Method '{method_name}' retrieved successfully.")
            
            if method is None:
                logger.info(f"Method '{method_name}' not found in class '{class_name}'.")
                return instance, None
            
            return instance, method
        except ModuleNotFoundError as e:
            logger.info(f"Module '{module_name}' not found: {e}")
        except AttributeError as e:
            logger.info(f"Error retrieving class or method: {e}")
        except Exception as e:
            logger.info(f"Unexpected error: {e}")
        return None, None

    def get_directories(self, county: str, logger, parse_single_file: bool = False) -> Tuple[str, str]:
        # Determine the base directory of your project
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        logger.info(f"get_directories function called\nbase_dir: {base_dir}\n")
        try:
            if parse_single_file:
                case_html_path = os.path.join(base_dir, "resources", "test_files")
                case_json_path = os.path.join(base_dir, "resources", "test_files")
            else:
                case_html_path = os.path.join(base_dir, "data", county, "case_html")
                case_json_path = os.path.join(base_dir, "data", county, "case_json")
                if not os.path.exists(case_json_path):
                    os.makedirs(case_json_path, exist_ok=True)
            logger.info(f"Returning case_html_path: {case_html_path}\nReturning case_json_path: {case_json_path}\n")
            return case_html_path, case_json_path
        except Exception as e:
            logger.info(f"Error in get_directories: {e}")
            raise

    def get_list_of_html(self, case_html_path: str, case_number: str, county: str, logger, parse_single_file: bool = False) -> List[str]:
        logger.info(f"get_list_of_html function called\n")
        try:
            if parse_single_file:
                logger.info(f"parse_single_file is True\n")
                relative_path = os.path.join(project_root, 'resources', 'test_files')
                return [os.path.join(relative_path, f'test_{case_number}.html')]
            # This will loop through the html in the folder they were scraped to.
            case_html_list = os.listdir(case_html_path)

            # However, if an optional case number is passed to the function, then read in the case number html file from the data folder 
            #   -Assumes that the requested parsed case number has been scraped to html
            if case_number:
                case_html_list = [f'{case_number}.html']
            case_html_list = [os.path.join(case_html_path, file_name) for file_name in case_html_list]
            logger.info(f"Returning case_html_list: {case_html_list}\n")
            return case_html_list
        except Exception as e:
            logger.info(f"Error in get_list_of_html: {e}")
            raise

    def get_html_path(self, case_html_path: str, case_html_file_name: str, case_number: str, logger) -> str:
        logger.info(f"get_html_path function called\n")
        try:
            case_html_file_path = os.path.join(case_html_path, case_html_file_name)
            logger.info(f"Constructed path: {case_html_file_path}")
            return case_html_file_path
        except Exception as e:
            logger.info(f"Error in get_html_path: {e}")
            raise

    def write_json_data(self, case_json_path: str, case_number: str, case_data: str, logger) -> None:
        try:
            indent_level = 4
            logger.info(f"Writing JSON to: {case_json_path}")
            with open(os.path.join(case_json_path, case_number + ".json"), "w") as file_handle:
                file_handle.write(json.dumps(case_data, indent=indent_level))
        except Exception as e:
            logger.info(f"Error in write_json_data: {e}")
            raise

    def write_error_log(self, county: str, case_number: str) -> None:
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            error_log_path = os.path.join(base_dir, 'data', county, "cases_with_parsing_error.txt")
            with open(
                error_log_path,
                "w",
            ) as file_handle:
                file_handle.write(case_number + "\n")        
        except Exception as e:
            print(f"Error in write_error_log: {e}")
            raise
     
    def parse(self, county: str, case_number: str, parse_single_file: bool = False, test = False) -> None:
        logger = self.configure_logger()

        # For simple testing purposes
        # Comment out for larger scale testing
        # Case number is from /resources/test_files/test_{case_number}.html
        if not case_number:
            case_number = '51652356'


        logger.info(f"Starting parsing for {county} county with case number {case_number}")
        county = county.lower()
        try:
            # get input and output directories and make json dir if not present
            case_html_path, case_json_path = self.get_directories(county, logger, test)

            # start 
            START_TIME_PARSER = time()
            logger.info(f'Time started: {START_TIME_PARSER}')
            # creating a list of json files already parsed 
            cached_case_json_list = [
                file_name.split(".")[0] for file_name in os.listdir(case_json_path)
            ]

            # Get a list of the HTML files that it needs to parse.
            case_html_list = self.get_list_of_html(case_html_path, case_number, county, logger, parse_single_file)
            logger.info(f'Starting for loop to parse {len(case_html_list)} cases')
            for case_html_file_path in case_html_list:
                try:
                    case_number = os.path.basename(case_html_file_path).split(".")[0]

                    logger.info(f"{case_number} - parsing")

                    with open(case_html_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        case_soup = BeautifulSoup(file, "html.parser")

                    parser_instance, parser_function = self.get_class_and_method(county=county, logger=logger, test=test)   

                    if parser_instance is not None and parser_function is not None:
                        case_data = parser_function(county, case_number, logger, case_soup)
                    else:
                        logger.info("Error: Could not obtain parser instance or function.")
                        continue

                    body = case_soup.find("body")
                    tables = body.find_all("table")
                    if tables:
                        balance_table = tables[-1]
                        if "Balance Due" in balance_table.text:
                            balance_table.decompose()
                    case_data["html_hash"] = xxhash.xxh64(str(body)).hexdigest()

                    self.write_json_data(case_json_path, case_number, case_data, logger)

                except Exception:
                    print(traceback.format_exc())
                    self.write_error_log(county, case_number)

            RUN_TIME_PARSER = time() - START_TIME_PARSER
            logger.info(f"Parsing took {RUN_TIME_PARSER} seconds")
        except Exception as e:
            logger.info(f"Error in parse: {e}")
            raise

if __name__ == "__main__":
    parser = Parser()
    parser.parse(county="hays", case_number=None, parse_single_file=True)
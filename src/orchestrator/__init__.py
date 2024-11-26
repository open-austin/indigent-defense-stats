import os
import csv
import sys
import logging
import shutil
from datetime import datetime

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

class Orchestrator:
    def __init__(self):
        #Sets our base parameters
        self.counties = []
        self.start_date = '2024-01-01'       #Update start date here
        self.end_date = '2024-01-31'         #Update end date here
        self.create_logs_folder()
        self.logger = self.configure_logger()
        now = datetime.now()
        formatted_date_time = now.strftime("%d-%m-%Y-%H.%M")
        self.logger.info("~~~~~~~Starting TDD Program~~~~~~~")
        self.logger.info(f"Starting date and time is {formatted_date_time}.")
        self.logger.info(f"Scraping Start Date: {self.start_date}.")
        self.logger.info(f"Scraping End Date: {self.end_date}.")

    def configure_logger(self):
        # Configure logging
        logger = logging.getLogger(name=f"orchestrator: pid: {os.getpid()}")
        # Set up basic configuration for the logging system
        logging.basicConfig(level=logging.INFO)

        orchestrator_log_path = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        now = datetime.now()
        # Format it as "DD-MM-YYYY - HH:MM"
        formatted_date_time = now.strftime("%d-%m-%Y-%H.%M")
        orchestrator_log_name = formatted_date_time + '_orchestrator_logger_log.txt'

        file_handler = logging.FileHandler(os.path.join(orchestrator_log_path, orchestrator_log_name))
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def create_logs_folder(self):
        # Define the root folder
        logs_folder = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        if not os.path.exists(logs_folder):
            os.makedirs(logs_folder)

    def file_reset(self, county):
        # Define the root folder and subfolders
        root_folder = os.path.join(os.path.dirname(__file__), "..", "..", "data", county)
        subfolders = ['case_html', 'case_json', 'case_json_cleaned']

        # Loop through each subfolder and remove all files
        for subfolder in subfolders:
            folder_path = os.path.join(root_folder, subfolder)
            
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Loop through all the files in the subfolder
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    
                    # Check if it's a file and remove it
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    # If it's a directory, remove the directory and all its contents
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f'Removed directory and its contents: {file_path}')
            else:
                self.logger.error(f"{subfolder} folder not found here: {folder_path}")
        self.logger.info("Finished removing files.")

    def orchestrate(self):
        #This open the county data CSV to see which counties should be scraped, parsed, cleaned, and updated.
        with open(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "resources", "texas_county_data.csv"
            ),
            mode="r",
        ) as file_handle:
            csv_file = csv.DictReader(file_handle)
            for row in csv_file:
                #This only selects the counties from the csv that should be parsed.
                if row["scrape"].lower() == "yes":
                    self.counties.append(row["county"])

        #This runs the different modules in order
        #src/scraper
        for c in self.counties:
            c = c.lower()
            print(f"Starting to scrape, parse, clean, and update this county: {c}")
            scraper.Scraper().scrape(county = c,
                                    start_date = self.start_date,
                                    end_date = self.end_date,
                                    court_calendar_link_text = None,
                                    case_number = None,
                                    case_html_path = None,
                                    judicial_officers = None,
                                    ms_wait = None)
            #src/parser
            parser.Parser().parse(county = c,
                            case_number = None,
                            parse_single_file = False,
                            test=False)
            #src/cleaner
            cleaner.Cleaner().clean(county = c)
            #src/updater
            updater.Updater(c).update()
            self.file_reset(c)
            print(f"Completed with scraping, parsing, cleaning, and updating of this county: {c}")

if __name__ == '__main__':
    Orchestrator().orchestrate()

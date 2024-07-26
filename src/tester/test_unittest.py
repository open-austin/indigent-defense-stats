import unittest, sys, os
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
#from scraper.arguments import *

class ScraperTestCase(unittest.TestCase):
    
    def test_scraper_hays(self):
        now = datetime.now()
        now_string = now.strftime("%H:%M:%S")
        #my_function()  # Call the function being tested
        scraper_instance = scraper('hays', '2024-07-01', '2024-07-01', 'CR-16-0002-A')
        scraper_instance.scrape()

        # Test #1: Did the scraper create a file called 12947592.html in the right location?
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

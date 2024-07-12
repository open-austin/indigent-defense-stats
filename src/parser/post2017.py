from typing import Dict

from bs4 import BeautifulSoup

class post2017_parser():
    def __init__(self, case_id, county):
        self.case_id = case_id
        self.county = county

    def parse_post2017(self, case_soup: BeautifulSoup) -> Dict:

        case_data = {}
        case_data["odyssey id"] = self.case_id
        return case_data

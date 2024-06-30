from typing import Dict

from bs4 import BeautifulSoup


def parse(case_soup: BeautifulSoup, case_id: str, county: str) -> Dict:
    case_data = {}
    case_data["odyssey id"] = case_id
    return case_data

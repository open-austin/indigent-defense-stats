import os
import requests

from bs4 import BeautifulSoup

MS_WAIT_PER_REQUEST = 100

main_page_url = "http://public.co.hays.tx.us/"

Judicial_Officers = [
    "visiting_officer",
    "Boyer_Bruce",
    "Johnson_Chris",
    "Robison_Jack",
    "Sherri_Tibbe",
    "Henry_Bill",
    "Steel_Gary",
    "Updegrove_Robert",
    "Zelhart_Tacie",
]

if __name__ == "__main__":
    # Initial setup for the session
    session = requests.Session()
    main_page = session.get(main_page_url)
    # calendar_page = session.get(calendar_page_url)
    # soup = BeautifulSoup(calendar_page.text, "html.parser")
    # viewstate = soup.find(id="__VIEWSTATE")["value"]

    # Data dir setup - added this to gitignore for now, may want to remove later
    if not os.path.exists("data_by_JO"):
        os.mkdir("data_by_JO")
    for JO_name in Judicial_Officers:
        JO_path = os.path.join("data_by_JO", JO_name)
        JO_case_path = os.path.join(JO_path, "case_data")
        if not os.path.exists(JO_path):
            os.mkdir(JO_path)
        if not os.path.exists(JO_case_path):
            os.mkdir(JO_case_path)

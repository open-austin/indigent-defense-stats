import os
import requests
from time import sleep

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
        print(f"Processing {JO_name}")
        # Make folders if they don't exist
        JO_path = os.path.join("data_by_JO", JO_name)
        JO_case_path = os.path.join(JO_path, "case_html")
        JO_cal_path = os.path.join(JO_path, "calendar_html")
        if not os.path.exists(JO_path):
            os.mkdir(JO_path)
        if not os.path.exists(JO_case_path):
            os.mkdir(JO_case_path)
        if not os.path.exists(JO_cal_path):
            os.mkdir(JO_cal_path)

        for cal_html_file in os.scandir(JO_cal_path):
            if not cal_html_file.is_dir():
                print(f"Processing {cal_html_file.path}")
                with open(cal_html_file.path, "r") as file_handle:
                    cal_html_str = file_handle.read()
                cal_soup = BeautifulSoup(cal_html_str, "html.parser")
                case_anchors = cal_soup.select('a[href^="CaseDetail"]')
                for case_anchor in case_anchors:
                    case_url = main_page_url + case_anchor["href"]
                    # Make request for the case
                    # case_results = session.get(case_url)

                    print(case_results.text)
                    quit()

                    # Rate limiting - convert ms to seconds
                    sleep(MS_WAIT_PER_REQUEST / 1000)

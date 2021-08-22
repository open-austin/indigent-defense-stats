import os
import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup

from config import (
    make_form_data,
    judicial_officer_to_ID,
    main_page_url,
    calendar_page_url,
    MS_WAIT_PER_REQUEST,
)

DAYS_OF_RECORDS = 5 * 365
TODAY = datetime.datetime.today()

if __name__ == "__main__":
    # Initial setup for the session
    session = requests.Session()
    main_page = session.get(main_page_url)
    # May not be necessary, grabbing viewstate for form data
    calendar_page = session.get(calendar_page_url)
    soup = BeautifulSoup(calendar_page.text, "html.parser")
    viewstate_token = soup.find(id="__VIEWSTATE")["value"]

    # Data dir setup - added this to gitignore for now, may want to remove later
    if not os.path.exists("data_by_JO"):
        os.mkdir("data_by_JO")
    for JO_name in judicial_officer_to_ID.keys():
        JO_path = os.path.join("data_by_JO", JO_name)
        JO_cal_path = os.path.join(JO_path, "calendar_html")
        if not os.path.exists(JO_path):
            os.mkdir(JO_path)
        if not os.path.exists(JO_cal_path):
            os.mkdir(JO_cal_path)

    # Days in the past starting with yesterday.
    for DAY_OFFSET in range(1, DAYS_OF_RECORDS):
        date_string = datetime.datetime.strftime(
            TODAY - datetime.timedelta(days=DAY_OFFSET), format="%m/%d/%Y"
        )
        file_name = f"{date_string.replace('/','-')}.html"
        for JO_name, JO_id in judicial_officer_to_ID.items():
            print(f"Capturing data for JO: {JO_name} on {date_string}")
            cal_html_file_path = os.path.join(
                "data_by_JO", JO_name, "calendar_html", file_name
            )
            # Check if the file is already cached before requesting
            if not os.path.exists(cal_html_file_path):
                cal_results = session.post(
                    calendar_page_url,
                    data=make_form_data(date_string, JO_id, viewstate_token),
                )
                # Error check based on text in html result.
                if "Record Count" in cal_results.text:
                    print(f"Writing file: {cal_html_file_path}")
                    with open(cal_html_file_path, "w") as file_handle:
                        file_handle.write(cal_results.text)
                    # Rate limiting - convert ms to seconds
                    sleep(MS_WAIT_PER_REQUEST / 1000)
                else:
                    print(
                        f'ERROR: "Record Count" substring not found in calendar html page. Aborting. Writing ./debug.html'
                    )
                    with open("debug.html", "w") as file_handle:
                        file_handle.write(cal_results.text)
                    quit()
            else:
                print("Data is already cached. Skipping.")

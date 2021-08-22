import os
import argparse
from time import sleep

import requests
from bs4 import BeautifulSoup

from config import (
    make_form_data,
    judicial_officer_to_ID,
    main_page_url,
    calendar_page_url,
    argparser,
)

argparser.description = "Scrape case data using cached JO calendar html data."
args = argparser.parse_args()

if __name__ == "__main__":
    # Initial setup for the session
    session = requests.Session()
    main_page = session.get(main_page_url)

    # May not be necessary, grabbing viewstate for form data
    calendar_page = session.get(calendar_page_url)
    soup = BeautifulSoup(calendar_page.text, "html.parser")
    viewstate_token = soup.find(id="__VIEWSTATE")["value"]

    # Make data dir if it doesn't exist
    if not os.path.exists("data_by_JO"):
        os.mkdir("data_by_JO")

    for JO_name, JO_id in judicial_officer_to_ID.items():
        print(f"Processing {JO_name}")
        JO_case_path = os.path.join("data_by_JO", JO_name, "case_html")
        JO_cal_path = os.path.join("data_by_JO", JO_name, "calendar_html")

        # Begin processing each calendar html file for this JO
        for cal_html_file in os.scandir(JO_cal_path):
            if not cal_html_file.is_dir():
                case_date = cal_html_file.name.split(".")[0]
                print(f"Processing cases from {case_date} for {JO_name}")

                # Read the case URLs from the calendar page html
                with open(cal_html_file.path, "r") as file_handle:
                    cal_html_str = file_handle.read()
                cal_soup = BeautifulSoup(cal_html_str, "html.parser")
                case_anchors = cal_soup.select('a[href^="CaseDetail"]')

                # Setup for processing the cases
                if case_anchors:
                    # If all cases are cached, continue
                    if all(
                        os.path.exists(
                            os.path.join(
                                JO_case_path,
                                f"{case_date} {case_anchor['href'].split('=')[1]}.html",
                            )
                        )
                        for case_anchor in case_anchors
                    ):
                        print("All cases are cached for this file.")
                        continue
                    # We need to visit the calendar page for this case before visiting it with the session
                    session.post(
                        calendar_page_url,
                        data=make_form_data(case_date, JO_id, viewstate_token),
                    )
                    # Rate limiting - convert ms to seconds
                    sleep(args.ms_wait / 1000)

                # Process each case
                for case_anchor in case_anchors:
                    case_url = main_page_url + case_anchor["href"]
                    case_id = case_url.split("=")[1]
                    case_html_file_path = os.path.join(
                        JO_case_path, f"{case_date} {case_id}.html"
                    )

                    # Check if the case is cached
                    if not os.path.exists(case_html_file_path):
                        # Make request for the case
                        print("Visiting", case_url)
                        case_results = session.get(case_url)
                        # Error check based on text in html result.
                        if "Date Filed" in case_results.text:
                            print(f"Writing file: {case_html_file_path}")
                            with open(case_html_file_path, "w") as file_handle:
                                file_handle.write(case_results.text)
                            # Rate limiting - convert ms to seconds
                            sleep(args.ms_wait / 1000)
                        else:
                            curr_vars = f"{JO_name = }\n{case_url = }"
                            print(
                                'ERROR: "Date Filed" substring not found in case html page. Aborting.\n',
                                "Writing ./debug.html with response and ./debug.txt with current variables.\n",
                                curr_vars,
                            )
                            with open("debug.html", "w") as file_handle:
                                file_handle.write(case_results.text)
                            with open("debug.txt", "w") as file_handle:
                                file_handle.write(curr_vars)
                            quit()
                    else:
                        print("Data is already cached. Skipping.")

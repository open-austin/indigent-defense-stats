import os
from time import sleep

import requests
from bs4 import BeautifulSoup

from libraries.scrape_config import (
    make_form_data,
    setup_directories,
    argparser,
)

argparser.description = "Scrape case data using cached JO calendar html data."
args = argparser.parse_args()
if "default.aspx" in args.main_page:
    args.main_page = args.main_page.replace("default.aspx", "")

# Initial setup for the session
session = requests.Session()
main_response = session.get(args.main_page)
main_soup = BeautifulSoup(main_response.text, "html.parser")
calendar_response = session.get(args.main_page + "Search.aspx?ID=900")
calendar_soup = BeautifulSoup(calendar_response.text, "html.parser")
if "Court Calendar" not in calendar_soup.text:
    print("ERROR: Couldn't access Court Calendar page. Quitting.")
    quit()
hidden_values = {
    hidden["name"]: hidden["value"]
    for hidden in calendar_soup.select('input[type="hidden"]')
}
judicial_officer_to_ID = {
    option.text: option["value"]
    for option in calendar_soup.select('select[labelname="Judicial Officer:"] > option')
}
node_info = main_soup.select_one('select[id="sbxControlID2"] > option')
hidden_values.update({"NodeDesc": node_info.text, "NodeID": node_info["value"]})


# Make all data folders if they don't exist
setup_directories(args.judicial_officers)

for JO_name in args.judicial_officers:
    JO_case_path = os.path.join("data_by_JO", JO_name, "case_html")
    JO_cal_path = os.path.join("data_by_JO", JO_name, "calendar_html")
    if JO_name not in judicial_officer_to_ID:
        print(
            f"ERROR: judicial officer {JO_name} not found on calendar page. Continuing."
        )
        continue
    JO_id = judicial_officer_to_ID[JO_name]

    # Begin processing each calendar html file for this JO
    for cal_html_file in os.scandir(JO_cal_path):
        if not cal_html_file.is_dir():
            case_date = cal_html_file.name.split(".")[0]
            print(JO_name, "on", case_date)

            # Read the case URLs from the calendar page html
            with open(cal_html_file.path, "r") as file_handle:
                cal_html_str = file_handle.read()
            cal_soup = BeautifulSoup(cal_html_str, "html.parser")
            case_anchors = cal_soup.select('a[href^="CaseDetail"]')
            print(len(case_anchors), "cases found.")
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
                # We need to visit the calendar page for this set of cases before visiting them with the session
                session.post(
                    args.main_page + "Search.aspx?ID=900",
                    data=make_form_data(case_date, JO_id, hidden_values),
                )
                # Rate limiting - convert ms to seconds
                sleep(args.ms_wait / 1000)

            # Process each case
            for case_anchor in case_anchors:
                case_url = args.main_page + case_anchor["href"]
                case_id = case_url.split("=")[1]
                case_html_file_path = os.path.join(
                    JO_case_path, f"{case_date} {case_id}.html"
                )

                # Check if the case is cached
                if not os.path.exists(case_html_file_path):
                    # Make request for the case
                    print("Visiting:", case_url)
                    case_results = session.get(case_url)
                    # Error check based on text in html result.
                    if "Date Filed" in case_results.text:
                        print("Writing file:", case_html_file_path)
                        print("Response string length:", len(case_results.text))
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

import os
from datetime import datetime, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup

from libraries.scrape_config import (
    make_form_data,
    judicial_officer_to_ID,
    argparser,
)

argparser.description = "Scrape calendar html data from judicial officers."
argparser.add_argument(
    "--days",
    "--d",
    type=int,
    default=5 * 365,
    help="Number of days to scrape (backwards).",
)
argparser.add_argument(
    "--start_offset",
    "--s",
    type=int,
    default=1,
    help="The number of days ago to start scraping. 1 is Yesterday.",
)
args = argparser.parse_args()
TODAY = datetime.today()

# Initial setup for the session
session = requests.Session()
session.get(args.main_page)
# May not be necessary, grabbing viewstate for form data
viewstate_token = BeautifulSoup(
    session.get(args.calendar_page).text, "html.parser"
).find(id="__VIEWSTATE")["value"]

# Days in the past starting with yesterday.
for day_offset in range(args.start_offset, args.days):
    date_string = datetime.strftime(TODAY - timedelta(days=day_offset), "%m/%d/%Y")
    file_name = f"{date_string.replace('/','-')}.html"
    for JO_name, JO_id in judicial_officer_to_ID.items():
        print(f"Capturing data for JO {JO_name} on {date_string}")
        cal_html_file_path = os.path.join(
            "data_by_JO", JO_name, "calendar_html", file_name
        )
        # Check if the file is already cached before requesting
        if not os.path.exists(cal_html_file_path):
            cal_results = session.post(
                args.calendar_page,
                data=make_form_data(date_string, JO_id, viewstate_token),
            )
            # Error check based on text in html result.
            if "Record Count" in cal_results.text:
                print("Writing file:", cal_html_file_path)
                print("Response string length:", len(cal_results.text))
                with open(cal_html_file_path, "w") as file_handle:
                    file_handle.write(cal_results.text)
                # Rate limiting - convert ms to seconds
                sleep(args.ms_wait / 1000)
            else:
                curr_vars = f"{day_offset = }\n{JO_name = }\n{date_string = }"
                print(
                    'ERROR: "Record Count" substring not found in calendar html page. Aborting.\n',
                    "Writing ./debug.html with response and ./debug.txt with current variables.\n",
                    curr_vars,
                )
                with open("debug.html", "w") as file_handle:
                    file_handle.write(cal_results.text)
                with open("debug.txt", "w") as file_handle:
                    file_handle.write(curr_vars)
                quit()
        else:
            print("Data is already cached. Skipping.")

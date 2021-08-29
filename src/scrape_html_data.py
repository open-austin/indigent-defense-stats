import os
from datetime import datetime, timedelta
from time import sleep, time

from bs4 import BeautifulSoup

from libraries.scrape_config import (
    make_form_data,
    args,
    hidden_values,
    judicial_officer_to_ID,
    session,
)

TODAY = datetime.today()
START_TIME = time()

# Days in the past starting with yesterday.
for day_offset in range(args.start_offset, args.days):
    date_string = datetime.strftime(TODAY - timedelta(days=day_offset), "%m/%d/%Y")
    cal_html_file = f"{date_string.replace('/','-')}.html"
    for JO_name in args.judicial_officers:
        VISITED_CAL_PAGE = False
        # error check and initialize variables for this JO
        if JO_name not in judicial_officer_to_ID:
            print(
                f"ERROR: judicial officer {JO_name} not found on calendar page. Continuing."
            )
            continue
        JO_case_path = os.path.join("data_by_JO", JO_name, "case_html")
        JO_cal_path = os.path.join("data_by_JO", JO_name, "calendar_html")
        JO_id = judicial_officer_to_ID[JO_name]
        print(f"Getting calendar page data for JO {JO_name} on {date_string}")
        cal_html_file_path = os.path.join(JO_cal_path, cal_html_file)

        # Check if the file is already cached before requesting and writing
        if not os.path.exists(cal_html_file_path):
            cal_results = session.post(
                args.main_page + "Search.aspx?ID=900",
                data=make_form_data(date_string, JO_id, hidden_values),
            )
            VISITED_CAL_PAGE = True
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
            print("Calendar data is already cached. Skip writing.")

        # get the case data for this date
        print(f"Getting individual case data for {JO_name} on {date_string}")

        # Read the case URLs from the calendar page html
        with open(cal_html_file_path, "r") as file_handle:
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
                        f"{date_string} {case_anchor['href'].split('=')[1]}.html",
                    )
                )
                for case_anchor in case_anchors
            ):
                print("All cases are cached for this JO and date.")
                continue

            # visit the calendar page if we haven't yet, needs to be done to scrape cases from it.
            if not VISITED_CAL_PAGE:
                session.post(
                    args.main_page + "Search.aspx?ID=900",
                    data=make_form_data(date_string, JO_id, hidden_values),
                )
                VISITED_CAL_PAGE = True
                # Rate limiting - convert ms to seconds
                sleep(args.ms_wait / 1000)

        # Process each case
        for case_anchor in case_anchors:
            case_url = args.main_page + case_anchor["href"]
            case_id = case_url.split("=")[1]
            case_html_file_path = os.path.join(
                JO_case_path, f"{date_string.replace('/','-')} {case_id}.html"
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

print("\nTime to run script:", round(time() - START_TIME, 2), "seconds")

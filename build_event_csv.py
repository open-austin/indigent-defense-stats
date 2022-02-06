"""
Combine hearing & event records from multiple case files into a single csv.
"""
import csv
from datetime import datetime
import json
import os

FILE_DIR = "data"  # relative location of JSON case files


def parse_event_date(date_str):
    """Return a python `datetime` from e.g. '01/30/2021'"""
    month, day, year = date_str.split("/")
    return datetime(year=int(year), month=int(month), day=int(day))


def iso_event_date(dt):
    """Format a `datetime` instance as YYYY-MM-DD"""
    return dt.strftime("%Y-%m-%d")


def get_days_elapsed(start, end):
    """Return the number of days between two dates"""
    delta = end - start
    return delta.days


def main():
    files = [file for file in os.listdir(FILE_DIR) if file.endswith(".json")]
    events = []

    for f in files:
        with open(f"{FILE_DIR}/{f}", "r") as fin:
            """
            Extract fields of interest. you can add any attributes of interest to the
            event_record dict and they will be included in the output CSV
            """
            case = json.load(fin)
            retained = case["party information"]["appointed or retained"]
            case_id = case["odyssey id"]
            case_number = case["code"]
            first_event_date = None
            for i, event in enumerate(case["other events and hearings"]):
                event_record = {}
                event_date = parse_event_date(event[0])

                if i == 0:
                    first_event_date = event_date

                days_elapsed = get_days_elapsed(first_event_date, event_date)
                event_record["event_id"] = i + 1
                event_record["event_date"] = iso_event_date(event_date)
                event_record["first_event_date"] = iso_event_date(first_event_date)
                event_record["days_elapsed"] = days_elapsed
                event_record["event_name"] = event[1]
                event_record["attorney"] = retained
                event_record["case_id"] = case_id
                event_record["case_number"] = case_number
                events.append(event_record)

    with open("events_combined.csv", "w") as fout:
        writer = csv.DictWriter(fout, fieldnames=events[0].keys())
        writer.writeheader()
        writer.writerows(events)


if __name__ == "__main__":
    main()

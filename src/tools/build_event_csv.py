"""
Combine hearing & event records from multiple case files into a single csv.
"""
import csv
import argparse
import json
import os
from datetime import datetime

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-county",
    "-c",
    type=str,
    default="hays",
    help="The name of the county.",
)
argparser.description = "Print stats for the specified county."
args = argparser.parse_args()

FILE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", args.county, "case_json"
)


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
    charges = []

    for f_count, f_name in enumerate(files):
        if f_count % 1000 == 0:
            print(f"Processing file {f_count} of {len(files)}")

        with open(f"{FILE_DIR}/{f_name}", "r") as fin:
            """
            Extract fields of interest. you can add any attributes of interest to the
            event_record dict and they will be included in the output CSV.
            Extracts events and charges from the case file, in seperate files.
            """
            case = json.load(fin)

            # extract demographic info
            case_id = case["odyssey id"]
            case_number = case["code"]
            retained = case["party information"]["appointed or retained"]
            gender = case["party information"]["sex"]
            race = case["party information"]["race"]
            defense_attorney = case["party information"]["defense attorney"]

            # extract event data
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
                event_record["defense_attorney"] = defense_attorney
                event_record["race"] = race
                event_record["gender"] = gender
                events.append(event_record)

            # extract charge data
            for i, charge in enumerate(case["charge information"]):
                charge_record = {}
                charge_record["charge_id"] = i + 1
                charge_record["charge_name"] = charge.get("charges", "")
                charge_record["statute"] = charge.get("statute", "")
                charge_record["level"] = charge.get("level", "")

                charge_record["charge_date"] = charge.get("date", "")
                if charge_record["charge_date"]:
                    charge_record["charge_date"] = iso_event_date(
                        parse_event_date(charge_record["charge_date"])
                    )

                charge_record["case_id"] = case_id
                charge_record["case_number"] = case_number
                charges.append(charge_record)

    with open("events_combined.csv", "w", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=events[0].keys())
        writer.writeheader()
        writer.writerows(events)

    with open("charges_combined.csv", "w", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=charges[0].keys())
        writer.writeheader()
        writer.writerows(charges)


if __name__ == "__main__":
    main()

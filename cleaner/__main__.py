import json, argparse, os, datetime as dt

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-overwrite",
    "-o",
    action="store_true",
    help="Switch to overwrite already parsed data.",
)
argparser.add_argument(
    "-county",
    "-c",
    type=str,
    default="hays",
    help="The name of the county.",
)
argparser.description = "Clean data for the specified county."
args = argparser.parse_args()

case_json_folder_path = os.path.join(
    os.path.dirname(__file__), "..", "data", args.county, "case_json"
)

list_case_json_files = os.listdir(case_json_folder_path)
for case_json in list_case_json_files:
    print(case_json)
    # List of motions identified as evidenciary
    good_motions = [
        "Motion To Suppress",
        "Motion to Reduce Bond",
        "Motion to Reduce Bond Hearing",
        "Motion for Production",
        "Motion For Speedy Trial",
        "Motion for Discovery",
        "Motion In Limine",
    ]

    # Original Format
    in_file = case_json_folder_path + "\\" + case_json
    with open(in_file, "r") as f:
        input_dict = json.load(f)
    #print(f"input_dict: {input_dict}")

    # Get mappings of charge names to umich decsriptions
    charge_name_to_umich_file = os.path.join(
    os.path.dirname(__file__), "uch-uccs-database.json"
    )

    with open(charge_name_to_umich_file, "r") as f:
        charge_name_to_umich = json.load(f)
    #print(f"input_dict: {charge_name_to_umich}")

    charge_name_to_umich_dict = {}
    for item in charge_name_to_umich:
        # Assuming each item is a dictionary with 'charges' as a key
        charge_name = item['charge_name']
        charge_name_to_umich_dict[charge_name] = item

    charge_name_to_umich = charge_name_to_umich_dict
    # Cleaned Case Primary format
    out_file = {}
    out_file["case_number"] = input_dict["code"]
    out_file["attorney_type"] = input_dict["party information"]["appointed or retained"]

    # Create charges list
    charge_dates = []
    out_file["charges"] = []
    for i, charge in enumerate(input_dict["charge information"]):
        charge_dict = {
            "charge_id": i,
            "charge_level": charge["level"],
            "orignal_charge": charge["charges"],
            "statute": charge["statute"],
            "is_primary_charge": i == 0,  # True if this is the first charge
        }
        charge_datetime = dt.datetime.strptime(charge["date"], "%m/%d/%Y")
        charge_dates.append(charge_datetime)
        charge_dict["charge_date"] = dt.datetime.strftime(charge_datetime, "%Y-%m-%d")
        # Umichigan mapping
        try:
            charge_dict.update(charge_name_to_umich[charge["charges"]])
        except KeyError as KeyErrorCharge:
            print(f"Couldn't find this charge: {KeyErrorCharge}")
            pass

        out_file["charges"].append(charge_dict)
    out_file["earliest_charge_date"] = dt.datetime.strftime(min(charge_dates), "%Y-%m-%d")


    def contains_good_motion(motion, event):
        """Recursively check if a motion exists in an event list or sublist."""
        if isinstance(event, list):
            return any(contains_good_motion(motion, item) for item in event)
        return motion.lower() in event.lower()


    # Iterate through every event and see if one of our "good motions" is in it
    motions_in_events = [
        motion
        for motion in good_motions
        if contains_good_motion(motion, input_dict["other events and hearings"])
    ]
    out_file["motions"] = motions_in_events
    out_file["has_evidence_of_representation"] = len(motions_in_events) > 0

    # Original Format
    out_filepath = os.path.join(
    os.path.dirname(__file__), "..", "data", args.county, "case_json_cleaned",case_json
    )

    with open(out_filepath, "w") as f:
        json.dump(out_file, f)
    

import json, argparse, os, datetime as dt, xxhash
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

class cleaner:

    def __init__(self, county):
        self.county = county.lower()

    def clean(self):

        case_json_folder_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", self.county, "case_json"
        )
        case_json_cleaned_folder_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", self.county, "case_json_cleaned"
        )
        # Checks if the output folder exists
        if not os.path.exists(case_json_cleaned_folder_path):
            # Create the folder if it doesn't exist
            os.makedirs(case_json_cleaned_folder_path)
            print(f"Folder '{case_json_cleaned_folder_path}' created successfully.")
        else:
            print(f"Folder '{case_json_cleaned_folder_path}' already exists.")

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
            #(f"input_dict: {input_dict}")

            # Get mappings of charge names to umich decsriptions
            charge_name_to_umich_file = os.path.join(
            os.path.dirname(__file__),"..", "..", "resources", "umich-uccs-database.json"
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
            out_file["case_number"] = input_dict["code"] #Note: This may be closed to personally identifying information of the defendant.
            out_file["attorney_type"] = input_dict["party information"]["appointed or retained"]
            #Adding the county and hash values into the final version.
            out_file["county"] = input_dict["county"]
            out_file["html_hash"] = input_dict["html_hash"]

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

            # This adds a hash of the unique string per defense attorney that matches this format: 'defense attorney name:defense atttorney phone number'. 
            # This will conceal the defense attorney but keep a unique idenfier to link defense attorney between cases.
            def_atty_unique_str = input_dict["party information"]["defense attorney"] + ':' + input_dict["party information"]["defense attorney phone number"]
            def_atty_hash = xxhash.xxh64(str(def_atty_unique_str)).hexdigest()
            out_file["defense attorney"] = def_atty_hash

            # Original Format
            out_filepath = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", self.county, "case_json_cleaned",case_json
            )

            with open(out_filepath, "w") as f:
                json.dump(out_file, f)


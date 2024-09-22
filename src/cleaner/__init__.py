import json
import os
import datetime as dt
import xxhash

class Cleaner:

    # commented out for now and maybe remove as it may not be needed anymore? 
    # def __init__(self, county):
        # self.county = county.lower()

    @staticmethod
    def add_parsing_date(input_dict: dict, out_file: dict) -> dict: # removed self from args and added @staticmethod
        # This will add the date of parsing to the final cleaned json file
        today_date = dt.datetime.today().strftime('%Y-%m-%d')
        out_file['parsing_date'] = today_date
        return out_file
        
    @staticmethod
    def ensure_folder_exists(folder_path): # removed self from args and added @staticmethod
        # Checks if the output folder exists
        if not os.path.exists(folder_path):
        # Create the folder if it doesn't exist
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' created successfully.")
        else:
            print(f"Folder '{folder_path}' already exists.")

    @staticmethod
    def load_json_file(file_path): # removed self from args and added @staticmethod
        """Loads a JSON file from a given file path and returns the data as an object"""
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def map_charge_names(charge_data): # removed self from args and added @staticmethod
        """Creates a dictionary mapping charge names to their corresponding UMich data"""
        charge_mapping = {}
        for item in charge_data:
            charge_mapping[item['charge_name']] = item
        return charge_mapping

    @staticmethod
    def process_charges(charges, charge_mapping): # removed self from args and added @staticmethod
        """
        Processes a list of charges by formatting charge details, 
        mapping charges to UMich data, and finding the earliest charge date.
    
        Args:
            charges (list): A list of charges where each charge is a dictionary containing charge details.
            charge_mapping (dict): A dictionary mapping charge names to corresponding UMich data.
        
        Returns:
            tuple: A list of processed charges and the earliest charge date.
        """
        charge_dates = []
        processed_charges = []

        for i, charge in enumerate(charges):
            charge_dict = {
                "charge_id": i,
                "charge_level": charge["level"],
                "orignal_charge": charge["charges"],
                "statute": charge["statute"],
                "is_primary_charge": i == 0,
            }

            # Parse the charge date and append it to charge_dates
            charge_datetime = dt.datetime.strptime(charge["date"], "%m/%d/%Y")
            charge_dates.append(charge_datetime)
            charge_dict["charge_date"] = dt.datetime.strftime(charge_datetime, "%Y-%m-%d")

            # Try to map the charge to UMich data
            try:
                charge_dict.update(charge_mapping[charge["charges"]])
            except KeyError:
                print(f"Couldn't find this charge: {charge['charges']}")
                pass

            processed_charges.append(charge_dict)

        # Find the earliest charge date
        earliest_charge_date = dt.datetime.strftime(min(charge_dates), "%Y-%m-%d")

        return processed_charges, earliest_charge_date
    
    @staticmethod
    def contains_good_motion(motion, event): # removed self from args and added @staticmethod
        """Recursively check if a motion exists in an event list or sublist."""
        if isinstance(event, list):
            return any(Cleaner.contains_good_motion(motion, item) for item in event) #changed self.contains_good_motion to Cleaner.contains_good_motion
        return motion.lower() in event.lower()

    @staticmethod
    def find_good_motions(events, good_motions): # removed self from args and added @staticmethod
        """Finds motions in events based on list of good motions."""
        motions_in_events = [
            motion for motion in good_motions if Cleaner.contains_good_motion(motion, events) #changed self.contains_good_motion to Cleaner.contains_good_motion
        ]
        return motions_in_events

    @staticmethod
    def write_json_output(file_path, data): # removed self from args and added @staticmethod
        """Writes the given data to a JSON file at the specified file path."""
        with open(file_path, "w") as f:
            json.dump(data, f)

    @staticmethod # removed self from args and added @staticmethod
    def clean(county): # added county as argument to not rely on self.county

        case_json_folder_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", county.lower(), "case_json" #changed self.county to county.lower()
        )
        case_json_cleaned_folder_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", county.lower(), "case_json_cleaned" #changed self.county to county.lower()
        )
        # Checks that the folder exists, if not it will be created
        Cleaner.ensure_folder_exists(case_json_cleaned_folder_path) # Call method using Cleaner class name instead of self

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
            # in_file = case_json_folder_path + "\\" + case_json
            in_file = os.path.join(case_json_folder_path, case_json) # Replaced original concatenation with this. Should help prevent problems with different OS path separators

            input_dict = Cleaner.load_json_file(in_file) # Call method using Cleaner class name instead of self
            #(f"input_dict: {input_dict}")

            # Get mappings of charge names to umich decsriptions
            charge_name_to_umich_file = os.path.join(
                os.path.dirname(__file__),"..", "..", "resources", "umich-uccs-database.json"
            )

            # ADD VARIABLE FOR Cleaner.load_json_file(charge_name_to_umich_file

            charge_name_to_umich = Cleaner.map_charge_names(Cleaner.load_json_file(charge_name_to_umich_file)) # Call method using Cleaner class name instead of self
            #print(f"input_dict: {charge_name_to_umich}")

            # Cleaned Case Primary format
            out_file = {}
            out_file["case_number"] = input_dict["code"] #Note: This may be closed to personally identifying information of the defendant.
            out_file["attorney_type"] = input_dict["party information"]["appointed or retained"]
            #Adding the county and hash values into the final version.
            out_file["county"] = input_dict["county"]
            out_file["html_hash"] = input_dict["html_hash"]

            # Create charges list
            out_file["charges"], out_file["earliest_charge_date"] = Cleaner.process_charges(input_dict["charge information"], charge_name_to_umich) # Call method using Cleaner class name instead of self

            # Stores list of motions from good_motions that exist inside input_dict["other events and hearings"]
            out_file["motions"] = Cleaner.find_good_motions(input_dict["other events and hearings"], good_motions) # Call method using Cleaner class name instead of self
            # Sets boolean based on whether any good motions were found
            out_file["has_evidence_of_representation"] = len(out_file["motions"]) > 0

            # This adds a hash of the unique string per defense attorney that matches this format: 'defense attorney name:defense atttorney phone number'. 
            # This will conceal the defense attorney but keep a unique idenfier to link defense attorney between cases.
            def_atty_unique_str = input_dict["party information"]["defense attorney"] + ':' + input_dict["party information"]["defense attorney phone number"]
            def_atty_hash = xxhash.xxh64(str(def_atty_unique_str)).hexdigest()
            out_file["defense_attorney"] = def_atty_hash # added underscore in defense_attorney for consistency

            # This adds the date of parsing to the final cleaned json
            out_file = Cleaner.add_parsing_date(input_dict, out_file) # Call method using Cleaner class name instead of self

            # Original Format
            out_filepath = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", county.lower(), "case_json_cleaned",case_json # changed self.county to county.lower()
            )

            Cleaner.write_json_output(out_filepath, out_file) # Call method using Cleaner class name instead of self

import json
import os
import datetime as dt
import xxhash

class Cleaner:

    # commented out for now and maybe remove as it may not be needed anymore? 
    # def __init__(self, county):
        # self.county = county.lower()

    GOOD_MOTIONS = [
        "Motion To Suppress",
        "Motion to Reduce Bond",
        "Motion to Reduce Bond Hearing",
        "Motion for Production",
        "Motion For Speedy Trial",
        "Motion for Discovery",
        "Motion In Limine",
    ]

    @staticmethod
    def add_parsing_date(input_dict: dict, output_json_data: dict) -> dict:
        # This will add the date of parsing to the final cleaned json file
        today_date = dt.datetime.today().strftime('%Y-%m-%d')
        output_json_data['parsing_date'] = today_date
        return output_json_data
    
    @staticmethod
    def get_folder_path(county, folder_type):
        """Returns the path for the specified folder type ('case_json' or 'case_json_cleaned')."""
        return os.path.join(os.path.dirname(__file__), "..", "..", "data", county.lower(), folder_type)

    @staticmethod
    def ensure_folder_exists(folder_path):
        """Checks if the output folder exists and creates it if it doesn't"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' created successfully.")
        else:
            print(f"Folder '{folder_path}' already exists.")

    @staticmethod
    def get_and_ensure_folder(county, folder_type):
        """Gets the folder path and ensures that the folder exists as this folder will contain the cleaned json files."""
        folder_path = Cleaner.get_folder_path(county, folder_type)
        Cleaner.ensure_folder_exists(folder_path)

    @staticmethod
    def load_json_file(file_path):
        """Loads a JSON file from a given file path and returns the data as an object"""
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def map_charge_names(charge_data):
        """Creates a dictionary mapping charge names to their corresponding UMich data"""
        charge_mapping = {}
        for item in charge_data:
            charge_mapping[item['charge_name']] = item
        return charge_mapping

    @staticmethod
    def load_and_map_charge_names(file_path):
        """Loads a JSON file and maps charge names to their corresponding UMich data."""
        charge_data = Cleaner.load_json_file(file_path)
        return Cleaner.map_charge_names(charge_data)


    @staticmethod
    def process_charges(charges, charge_mapping):
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
    def contains_good_motion(motion, event):
        """Recursively check if a motion exists in an event list or sublist."""
        if isinstance(event, list):
            return any(Cleaner.contains_good_motion(motion, item) for item in event) 
        return motion.lower() in event.lower()

    @staticmethod
    def find_good_motions(events, good_motions):
        """Finds motions in events based on list of good motions."""
        motions_in_events = [
            motion for motion in good_motions if Cleaner.contains_good_motion(motion, events)
        ]
        return motions_in_events

    @staticmethod
    def hash_defense_attorney(input_dict):
        """Hashes the defense attorney info to anonymize it."""
        def_atty_unique_str = f'{input_dict["party information"]["defense attorney"]}:{input_dict["party information"]["defense attorney phone number"]}'
        return xxhash.xxh64(def_atty_unique_str).hexdigest()


    @staticmethod
    def write_json_output(file_path, data):
        """Writes the given data to a JSON file at the specified file path."""
        with open(file_path, "w") as f:
            json.dump(data, f)

    @staticmethod
    def process_single_case(county, case_json_folder_path, case_json_filename):
        """Process a single case JSON file."""
        input_json_path = os.path.join(case_json_folder_path, case_json_filename)
        input_dict = Cleaner.load_json_file(input_json_path)

        # Initialize cleaned output data
        output_json_data = {
            "case_number": input_dict["code"],
            "attorney_type": input_dict["party information"]["appointed or retained"],
            "county": input_dict["county"],
            "html_hash": input_dict["html_hash"],
            "charges": [],
            "earliest_charge_date": "",
            "motions": [],
            "has_evidence_of_representation": False,
            "defense_attorney": Cleaner.hash_defense_attorney(input_dict)
        }

        # Load charge mappings
        charge_name_to_umich_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "resources", "umich-uccs-database.json"
        )
        charges_mapped = Cleaner.load_and_map_charge_names(charge_name_to_umich_file)

        # Process charges and motions
        output_json_data["charges"], output_json_data["earliest_charge_date"] = Cleaner.process_charges(
            input_dict["charge information"], charges_mapped
        )
        output_json_data["motions"] = Cleaner.find_good_motions(
            input_dict["other events and hearings"], Cleaner.GOOD_MOTIONS
        )
        output_json_data["has_evidence_of_representation"] = len(output_json_data["motions"]) > 0

        # Add parsing date
        output_json_data = Cleaner.add_parsing_date(input_dict, output_json_data)

        # Write output to file
        output_filepath = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", county.lower(), "case_json_cleaned", case_json_filename
        )
        Cleaner.write_json_output(output_filepath, output_json_data)

    @staticmethod
    def process_json_files(county, case_json_folder_path):
        """Processes all JSON files in the specified folder."""
        list_case_json_files = os.listdir(case_json_folder_path)
        for case_json_filename in list_case_json_files:
            Cleaner.process_single_case(county, case_json_folder_path, case_json_filename)

    @staticmethod
    def clean(county):
        """
        Cleans and processes case data for a given county.
        This method performs the following steps:
        1. Loads raw JSON case data from the 'case_json' folder for the specified county.
        2. Processes and maps charges using an external UMich data source.
        3. Identifies relevant motions from a predefined list of good motions.
        4. Hashes defense attorney information to anonymize but uniquely identify the attorney.
        5. Adds metadata, such as parsing date and case number, to the cleaned data.
        6. Writes the cleaned data to the 'case_json_cleaned' folder for the specified county.
        """
        case_json_folder_path = Cleaner.get_folder_path(county, "case_json")
        Cleaner.get_and_ensure_folder(county, "case_json_cleaned")
        Cleaner.process_json_files(county, case_json_folder_path)

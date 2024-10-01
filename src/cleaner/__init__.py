import json
import os
import datetime as dt
import xxhash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Cleaner:

    GOOD_MOTIONS = [
        "Motion To Suppress",
        "Motion to Reduce Bond",
        "Motion to Reduce Bond Hearing",
        "Motion for Production",
        "Motion For Speedy Trial",
        "Motion for Discovery",
        "Motion In Limine",
    ]

    def __init__(self):
        pass

    def get_or_create_folder_path(self, county: str, folder_type: str) -> str:
        """Returns and ensures the existence of the folder path."""
        folder_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", county.lower(), folder_type)
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                logging.info(f"Folder '{folder_path}' created successfully.")
            else:
                logging.info(f"Folder '{folder_path}' already exists.")
        except OSError as e:
            logging.error(f"Error creating folder '{folder_path}': {e}")
        return folder_path

    def load_json_file(self, file_path: str) -> dict:
        """Loads a JSON file from a given file path and returns the data as an object"""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading file at {file_path}: {e}")
            return {}

    def load_and_map_charge_names(self, file_path: str) -> dict:
        """Loads a JSON file and maps charge names to their corresponding UMich data."""
        charge_data = self.load_json_file(file_path)
        # Check if the file loaded successfully
        if not charge_data:
            logging.error(f"Failed to load charge data from {file_path}")
            raise FileNotFoundError(f"File not found or is empty: {file_path}")
        # Create dictionary mapping charge names 
        try:
            return {item['charge_name']: item for item in charge_data}
        except KeyError as e:
            logging.error(f"Error in mapping charge names: {e}")
            raise ValueError(f"Invalid data structure: {file_path}")

    def process_charges(self, charges: list[dict], charge_mapping: dict) -> tuple[list[dict], str]:
        """
        Processes a list of charges by formatting charge details, 
        mapping charges to UMich data, and finding the earliest charge date.
    
        Args:
            charges: A list of charges where each charge is a dictionary containing charge details.
            charge_mapping: A dictionary mapping charge names to corresponding UMich data.
        
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
            try:
                charge_datetime = dt.datetime.strptime(charge["date"], "%m/%d/%Y")
                charge_dates.append(charge_datetime)
                charge_dict["charge_date"] = dt.datetime.strftime(charge_datetime, "%Y-%m-%d")
            except ValueError:
                logging.error(f"Error parsing date for charge: {charge}")
                continue

            # Try to map the charge to UMich data
            try:
                charge_dict.update(charge_mapping[charge["charges"]])
            except KeyError:
                logging.warning(f"Couldn't find this charge: {charge['charges']}")
                continue

            processed_charges.append(charge_dict)

        # Find the earliest charge date
        if charge_dates:
            earliest_charge_date = dt.datetime.strftime(min(charge_dates), "%Y-%m-%d")
        else:
            logging.warning("No valid charge dates found.")
            earliest_charge_date = ""

        return processed_charges, earliest_charge_date

    def contains_good_motion(self, motion: str, event: list | str) -> bool:
        """Recursively check if a motion exists in an event list or sublist."""
        if isinstance(event, list):
            return any(self.contains_good_motion(motion, item) for item in event) 
        return motion.lower() in event.lower()

    def find_good_motions(self, events: list | str, good_motions: list[str]) -> list[str]:
        """Finds motions in events based on list of good motions."""
        return [motion for motion in good_motions if self.contains_good_motion(motion, events)]        

    def hash_defense_attorney(self, input_dict: dict) -> str:
        """Hashes the defense attorney info to anonymize it."""
        try:
            def_atty_unique_str = f'{input_dict["party information"]["defense attorney"]}:{input_dict["party information"]["defense attorney phone number"]}'
            return xxhash.xxh64(def_atty_unique_str).hexdigest()
        except KeyError as e:
            logging.error(f"Missing defense attorney data: {e}")
            return ""


    def write_json_output(self, file_path: str, data: dict) -> None:
        """Writes the given data to a JSON file at the specified file path."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f)
            logging.info(f"Successfully wrote cleaned data to {file_path}")
        except OSError as e:
            logging.error(f"Failed to write JSON output to {file_path}: {e}")

    def process_single_case(self, case_json_folder_path: str, case_json_filename:str, cleaned_folder_path: str) -> None:
        """Process a single case JSON file."""
        input_json_path = os.path.join(case_json_folder_path, case_json_filename)
        input_dict = self.load_json_file(input_json_path)

        if not input_dict:
            logging.error(f"Failed to load case data from {input_json_path}")
            return

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
            "defense_attorney": self.hash_defense_attorney(input_dict),
            "parsing_date": dt.datetime.today().strftime('%Y-%m-%d')
        }

        # Load charge mappings
        charge_name_to_umich_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "resources", "umich-uccs-database.json"
        )
        charges_mapped = self.load_and_map_charge_names(charge_name_to_umich_file)

        # Process charges and motions
        output_json_data["charges"], output_json_data["earliest_charge_date"] = self.process_charges(
            input_dict["charge information"], charges_mapped
        )
        output_json_data["motions"] = self.find_good_motions(
            input_dict["other events and hearings"], self.GOOD_MOTIONS
        )
        output_json_data["has_evidence_of_representation"] = len(output_json_data["motions"]) > 0

        # Write output to file
        output_filepath = os.path.join(cleaned_folder_path, case_json_filename)
        self.write_json_output(output_filepath, output_json_data)

    def process_json_files(self, county: str, case_json_folder_path: str) -> None:
        """Processes all JSON files in the specified folder."""
        try:
            list_case_json_files = os.listdir(case_json_folder_path)
        except (FileNotFoundError, Exception) as e:
            logging.error(f"Error reading directory {case_json_folder_path}: {e}")
            return
        
        # Ensure the case_json_cleaned folder exists
        cleaned_folder_path = self.get_or_create_folder_path(county, "case_json_cleaned")

        for case_json_filename in list_case_json_files:
            try:
                self.process_single_case(case_json_folder_path, case_json_filename, cleaned_folder_path)
            except Exception as e:
                logging.error(f"Error processing file {case_json_filename}. Error: {e}")

    def clean(self, county: str) -> None:
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
        try:
            case_json_folder_path = self.get_or_create_folder_path(county, "case_json")
            logging.info(f"Processing data for county: {county}")
            self.process_json_files(county, case_json_folder_path)
            logging.info(f"Completed processing for county: {county}")
        except Exception as e:
            logging.error(f"Error during cleaning process for county: {county}. Error: {e}")

import json, argparse, os, xxhash
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
from datetime import datetime as dt
import logging

class Updater():
    def __init__(self, county):
        self.county = county.lower()
        self.case_json_cleaned_folder_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", self.county, "case_json_cleaned"
        )
        self.processed_path = os.path.join(self.case_json_cleaned_folder_path, 
                                           f"result_{dt.today().strftime('%Y-%m-%d.%H:%M:%S.%f')}")
        
        # open or create a output directory for a log and successfully processed data
        if os.path.exists(self.case_json_cleaned_folder_path) and \
            not os.path.exists(self.processed_path): 
            os.makedirs(self.processed_path)
        self.logger = self.configure_logger()

        self.COSMOSDB_CONTAINER_CASES_CLEANED = self.get_database_container()

    def configure_logger(self):
        logger = logging.getLogger(name="pid: " + str(os.getpid()))
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(os.path.join(self.processed_path, 'logger_log.txt'))
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger
    
    def get_database_container(self):
        #This loads the environment for interacting with CosmosDB #Dan: Should this be moved to the .env file?
        load_dotenv()
        URL = os.getenv("URL")
        KEY = os.getenv("KEY")
        DATA_BASE_NAME = os.getenv("DATA_BASE_NAME")
        CONTAINER_NAME_CLEANED = os.getenv("CONTAINER_NAME_CLEANED")
        try:
            client = CosmosClient(URL, credential=KEY)
        except Exception as e:
            self.logger.error(f"Error instantiating CosmosClient: {e.status_code} - {e.message}")
            return
        try:
            database = client.get_database_client(DATA_BASE_NAME)
        except Exception as e:
            self.logger.error(f"Error instantiating DatabaseClient: {e.status_code} - {e.message}")
            return
        try:
            COSMOSDB_CONTAINER_CASES_CLEANED = database.get_container_client(CONTAINER_NAME_CLEANED)
        except Exception as e:
            self.logger.error(f"Error instantiating ContainerClient: {e.status_code} - {e.message}")
            return
        
        return COSMOSDB_CONTAINER_CASES_CLEANED
        
    def update(self):
        if not os.path.exists(self.case_json_cleaned_folder_path):
            self.logger.error(f'The following path doesn\'t exits: \n{self.case_json_cleaned_folder_path}')
            return
        
        if not self.COSMOSDB_CONTAINER_CASES_CLEANED:
            return

        list_case_json_files = os.listdir(self.case_json_cleaned_folder_path)

        for case_json in list_case_json_files:
            in_file = self.case_json_cleaned_folder_path + "/" + case_json
            if os.path.isfile(in_file):
                dest_file = self.processed_path + "/" + case_json
            else:
                continue

            with open(in_file, "r") as f:
                input_dict = json.load(f)
            self.logger.info(f"[Case Filename: {case_json}, Case Number: {input_dict.get('case_number', None)}, HTML Hash: {input_dict.get('html_hash', None)}]")

            # Querying case databse to fetch all items that match the hash.
            hash_query = f"SELECT * FROM COSMOSDB_CONTAINER_CASES_CLEANED WHERE COSMOSDB_CONTAINER_CASES_CLEANED['html_hash'] = '{input_dict['html_hash']}'"
            try:
                # Execute the query
                cases = list(self.COSMOSDB_CONTAINER_CASES_CLEANED.query_items(query=hash_query,enable_cross_partition_query=True))
            except Exception as e:
                self.logger.error(f"Error querying cases-cleaned database for an existing hash: {e.status_code} - {e.message}")
                continue

            if len(cases) > 0:
                # There already exists one with the same hash, so skip this entirely.
                # Move the file to the processed folder.
                os.rename(in_file, dest_file)
                self.logger.info(f"The case's HTML hash already exists in the databse: {case_json}. Not updating the database.")
                continue

            # Querying case databse to fetch all items that match the cause number.
            case_query = f"SELECT * FROM COSMOSDB_CONTAINER_CASES_CLEANED WHERE COSMOSDB_CONTAINER_CASES_CLEANED['case_number'] = '{input_dict['case_number']}'"
            try:
                # Execute the query
                cases = list(self.COSMOSDB_CONTAINER_CASES_CLEANED.query_items(query=case_query,enable_cross_partition_query=True))
            except Exception as e:
                self.logger.error(f"Error querying cases-cleaned database for an existing cases: {e.status_code} - {e.message}")
                continue

            #If there are no cases that match the cause number, then create the case ID, add a version number of 1 to the JSON and push the JSON to the database.
            today = dt.today()
            input_dict['id'] = input_dict['case_number'] + ":" + input_dict['county'] + ":" + today.strftime('%m-%d-%Y') + input_dict['html_hash']
            input_dict['version'] = max(int(case['version']) for case in cases) + 1 if len(cases) > 0 else 1
            try:
                self.COSMOSDB_CONTAINER_CASES_CLEANED.create_item(body=input_dict)
            except Exception as e:
                self.logger.error(f"Error inserting this case to cases-cleaned database: {e.status_code} - {e.message}")
                continue

            # This case is inserted successfully.
            # Move the file to the processed folder.
            os.rename(in_file, dest_file)
            self.logger.info(f"Insertion successfully done with id: {input_dict['id']}, version: { input_dict['version']}")

if __name__ == '__main__':
    Updater('Hays').update()
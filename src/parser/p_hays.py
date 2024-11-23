from typing import Dict, List
from bs4 import BeautifulSoup
import traceback

CHARGE_SEVERITY = {
    "First Degree Felony": 1,
    "Second Degree Felony": 2,
    "Third Degree Felony": 3,
    "State Jail Felony": 4,
    "Misdemeanor A": 5,
    "Misdemeanor B": 6,
}

class ParserHays:

    def __init__(self):
        pass

    def extract_rows(self, table: BeautifulSoup, logger) -> List[List[str]]:
        try:
            rows = [
                [
                    tag.strip().replace("\xa0", "").replace("Â", "")
                    for tag in tr.find_all(text=True)
                    if tag.strip()
                ]
                for tr in table.select("tr")
            ]
            return [row for row in rows if row]
        except Exception as e:
            logger.info(f"Error extracting rows: {e}")
            return []
    
    def get_charge_severity(self, charge: str, logger) -> int:
        try:
            for charge_name, severity in CHARGE_SEVERITY.items():
                if charge_name in charge:
                    return severity
            return float('inf')
        except Exception as e:
            logger.info(f"Error getting charge severity: {e}")
            return float('inf')

    def count_dismissed_charges(self, dispositions: List[Dict], logger) -> int:
        try:
            return sum(
                1 for disposition in dispositions
                for detail in disposition.get("details", [])
                if detail.get("outcome", "").lower() == 'dismissed'
            )
        except Exception as e:
            logger.info(f"Error counting dismissed charges: {e}")
            return "Unknown"

    def get_top_charge(self, dispositions: List[Dict], charge_information: List[Dict], logger) -> Dict:
        try:
            top_charge = None
            min_severity = float('inf')

            charge_map = {info['charges']: info['level'] for info in charge_information}

            for disposition in dispositions:
                if isinstance(disposition, dict):
                    for detail in disposition.get("details", []):
                        if isinstance(detail, dict):
                            charge_text = detail.get("charge", "").strip()
                            charge_name = charge_text.split(" >=")[0].strip().lstrip("0123456789. ").strip()
                            charge_level = charge_map.get(charge_name, "Unknown")

                            severity = self.get_charge_severity(charge_level, logger)
                            if severity < min_severity:
                                min_severity = severity
                                top_charge = {
                                    "charge name": charge_name,
                                    "charge level": charge_level
                                }
                else:
                    logger.info(f"Unexpected type for disposition: {type(disposition)}")

            return top_charge
        except Exception as e:
            logger.info(f"Error getting top charge: {e}")
            return {
                "charge name": "Unknown",
                "charge level": "Unknown"
            }

    def get_case_metadata(self, county: str, case_number: str, case_soup: BeautifulSoup, logger) -> Dict[str, str]:
        try:
            #logger.info(f"Getting case metadata for {county} case {case_number}")
            return {
                "cause_number": case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[0].text,
                "odyssey id": case_number,
                "county": county
            }  
        except Exception as e:
            logger.info(f"Error getting case metadata: {e}")
            return {
                "cause_number": "Unknown",
                "odyssey id": case_number,
                "county": county
            }
        
    def get_case_details(self, table: BeautifulSoup, logger) -> Dict[str, str]:
        try:
            table_values = table.select("b")
            #logger.info(f"Getting case details")
            return {
                "name": table_values[0].text,
                "case type": table_values[1].text,
                "date filed": table_values[2].text,
                "location": table_values[3].text
            }
        except Exception as e:
            logger.info(f"Error getting case details: {e}")
            return {
                "name": "Unknown",
                "case type": "Unknown",
                "date filed": "Unknown",
                "location": "Unknown"
            }   
    
    def parse_defendant_rows(self, defendant_rows: List[List[str]], logger) -> Dict[str, str]:
        try:
            #logger.info(f"Parsing defendant rows")
            return {
                "defendant": defendant_rows[1][1],
                "sex": defendant_rows[1][2].split(" ")[0],
                "race": defendant_rows[1][2].split(" ")[1],
                "date of birth": defendant_rows[1][3],
                "height": defendant_rows[1][4].split(" ")[0],
                "weight": defendant_rows[1][4].split(" ")[1],
                "defense attorney": defendant_rows[1][5],
                "appointed or retained": defendant_rows[1][6],
                "defense attorney phone number": defendant_rows[1][7],
                "defendant address": defendant_rows[2][0] + " " + defendant_rows[2][1],
                "SID": defendant_rows[2][3],
            }
        except Exception as e:
            logger.info(f"Error parsing defendant rows: {e}")
            return {
                "defendant": "Unknown",
                "sex": "Unknown",  
                "race": "Unknown", 
                "date of birth": "Unknown",
                "height": "Unknown",
                "weight": "Unknown",
                "defense attorney": "Unknown",
                "appointed or retained": "Unknown",
                "defense attorney phone number": "Unknown",
                "defendant address": "Unknown",
                "SID": "Unknown",
            }
        
    def parse_state_rows(self, state_rows: List[List[str]], logger) -> Dict[str, str]:
        try:
            #logger.info(f"Parsing state rows")
            return {
                "prosecuting attorney": state_rows[3][2],
                "prosectuing attorney phone number": state_rows[3][3],
            }
        except Exception as e:
            logger.info(f"Error parsing state rows: {e}")
            return {
                "prosecuting attorney": "Unknown",
                "prosectuing attorney phone number": "Unknown",
            }
        
    def get_charge_information(self, table: BeautifulSoup, logger) -> List[Dict]:
        try:
            #logger.info(f"Getting charge information")
            table_rows = [
                tag.strip().replace("\xa0", " ")
                for tag in table.find_all(text=True)
                if tag.strip()
            ]

            charge_information = []
            for i in range(5, len(table_rows), 5):
                charge_information.append(
                    {
                        k: v
                        for k, v in zip(
                            ["charges", "statute", "level", "date"],
                            table_rows[i + 1 : i + 5],
                        )
                    }
                )
            return charge_information
        except Exception as e:
            logger.info(f"Error getting charge information: {e}")
            return []
        
    def format_events_and_orders_of_the_court(self, table: BeautifulSoup, case_soup: BeautifulSoup, logger) -> List:
        try:
            #logger.info(f"Formatting events and orders of the court")
            table_rows = [
                [
                    tag.strip().replace("\xa0", " ")
                    for tag in tr.find_all(text=True)
                    if tag.strip()
                ]
                for tr in table.select("tr")
                if tr.select("th")
            ]
            table_rows = [
                [" ".join(word.strip() for word in text.split()) for text in sublist]
                for sublist in table_rows
                if sublist
            ]

            disposition_rows = []
            other_event_rows = []

            for row in table_rows:
                if len(row) >= 2:
                    if row[1] in ["Disposition", "Disposition:", "Amended Disposition"]:
                        disposition_rows.append(row)
                    else:
                        other_event_rows.append(row)

            # Reverse the order of the rows
            other_event_rows = other_event_rows[::-1]
            disposition_rows = disposition_rows[::-1]

            return (disposition_rows, other_event_rows)
        except Exception as e:
            logger.info(f"Error formatting events and orders of the court: {e}")
            return ([], [])
        
    def get_disposition_information(self, row, dispositions, case_data, table, county, case_soup, logger) -> List[Dict]:
        try:
            if not row:
                #logger.info(f"No dispositions to process.")
                return dispositions 
            
            if len(row) >= 5:
                # Extract judicial officer if present
                judicial_officer = ""
                if len(row[2]) > 18 and row[2].startswith("(Judicial Officer:"):
                    judicial_officer = row[2][18:-1].strip()
                
                # Create a disposition entry
                disposition = {
                    "date": row[0],
                    "event": row[1],
                    "judicial officer": judicial_officer,
                    "details": []
                }

                # Check if this row is a disposition
                if row[1].lower() in ["disposition", "amended disposition", "deferred adjudication", "punishment hearing"]:
                    details = {
                        "charge": row[3],
                        "outcome": row[4]
                    }
                    if len(row) > 5:
                        details["additional_info"] = row[5:]
                    disposition["details"].append(details)
                    dispositions.append(disposition)
                    dispositions.reverse()
                else:
                    #logger.info("Row is not a disposition: %s", row)
                    pass

            return dispositions
        except Exception as e:
            logger.info(f"Error getting disposition information: {e}")
            return dispositions
        
    def parser_hays(self, county: str, case_number: str, logger, case_soup: BeautifulSoup) -> Dict[str, Dict]:
        try:
            root_tables = case_soup.select("body>table")

            case_data = {
                "Case Metadata": self.get_case_metadata(county, case_number, case_soup, logger)
            }

            for table in root_tables:

                if "Case Type:" in table.text and "Date Filed:" in table.text:
                    case_data["Case Details"] = self.get_case_details(table, logger)

                elif "Related Case Information" in table.text:
                    case_data["Related Cases"] = [
                        case.text.strip().replace("\xa0", " ") for case in table.select("td")]

                elif "Party Information" in table.text:
                    case_data["Defendent Information"] = self.parse_defendant_rows(self.extract_rows(table, logger), logger)
                    case_data["State Information"] = self.parse_state_rows(self.extract_rows(table, logger), logger)

                elif "Charge Information" in table.text:
                    case_data["Charge Information"] = self.get_charge_information(table, logger)

                elif "Events & Orders of the Court" in table.text:
                    disposition_rows, other_event_rows = self.format_events_and_orders_of_the_court(table, case_soup, logger)

                    dispositions = []
                    #logger.info(f"For Loop started\nGetting disposition information")
                    for row in disposition_rows:
                        case_data["Disposition Information"] = self.get_disposition_information(row, dispositions, case_data, table, county, case_soup, logger)
                    #logger.info(f"For Loop ended\n")
                    if "Disposition Information" in case_data:
                        case_data["Top Charge"] = self.get_top_charge(dispositions, case_data.get("Charge Information", []), logger)
                        case_data["Dismissed Charges Count"] = self.count_dismissed_charges(case_data["Disposition Information"], logger)
                    case_data['Other Events and Hearings'] = other_event_rows
                    
            return case_data
        except Exception as e:
            logger.error(f"Unexpected error while parsing Hays case: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}

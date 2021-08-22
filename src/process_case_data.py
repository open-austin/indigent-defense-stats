import os

from bs4 import BeautifulSoup

for JO_folder in os.scandir("data_by_JO"):
    case_data_path = os.path.join(JO_folder.path, "case_data")
    if not os.path.exists(case_data_path):
        os.mkdir(case_data_path)
    for case_html_file in os.scandir(os.path.join(JO_folder.path, "case_html")):
        case_data = {}
        with open(case_html_file.path, "r") as file_handle:
            case_html = file_handle.read()
        case_soup = BeautifulSoup(case_html, "html.parser")
        case_data["name"] = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[
            0
        ].text
        case_data["date"] = case_html_file.name.split()[0]
        case_filename = os.path.join(case_data_path, case_name + ".json")
        # TODO: if this file already exists, only overwrite it if the date in
        # it is earlier than the date for this data / case_data["date"]
        quit()

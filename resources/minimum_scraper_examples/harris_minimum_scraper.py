import requests, json

session = requests.Session()

import requests

# example, in the actual scraper get SearchCriteria.SelectedCourt from here. In the scraper I am using the hidden default court value.
# Might want to add ability to set court later, or cycle through all of them. However, Harris has 1 court, so no need.
response = session.get(
    "https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Home/Dashboard/26",
)

data = {
    "SearchCriteria.SelectedCourt": "Harris County JPs Odyssey Portal",  # would be taken from previous page in SearchCriteria.SelectedCourt element
    "SearchCriteria.SelectedHearingType": "Civil Hearing Types",
    "SearchCriteria.SearchByType": "JudicialOfficer",
    "SearchCriteria.SelectedJudicialOfficer": "63908",
    "SearchCriteria.DateFrom": "03/03/2022",
    "SearchCriteria.DateTo": "03/03/2022",
}

# need to post search query here, then use /OdysseyPortalJP/Hearing/HearingResults/Read endpoint to get the json data

response = session.post(
    "https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Hearing/SearchHearings/HearingSearch",
    data=data,
)

# get json list of cases

response = session.post(
    "https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Hearing/HearingResults/Read",
)

print("Case list JSON:")
print(response.text)

# get case html data

first_case_json = json.loads(response.text)["Data"][0]

params = {
    "eid": first_case_json["EncryptedCaseId"],
    "CaseNumber": first_case_json["CaseNumber"],
}

response = requests.get(
    "https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Case/CaseDetail",
    params=params,
)

print("Case info HTML:")
print(response.text)

params = {
    "caseId": first_case_json["CaseId"],
}

# get financial information

response = requests.get(
    "https://jpodysseyportal.harriscountytx.gov/OdysseyPortalJP/Case/CaseDetail/LoadFinancialInformation",
    params=params,
)

print("Case financial info HMTL:")
print(response.text)

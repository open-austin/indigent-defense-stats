from bs4 import BeautifulSoup as bs
import requests as r

s = r.Session()

main_page_url = "http://public.co.hays.tx.us/"
calendar_page_url = "http://public.co.hays.tx.us/Search.aspx?ID=900&NodeID=100,101,102,103,200,201,202,203,204,6112,400,401,402,403,404,405,406,407,6111,6114&NodeDesc=All%20Courts"

main_page = s.get(main_page_url)
calendar_page = s.get(calendar_page_url)

soup = bs(calendar_page.text)
viewstate = soup.find(id="__VIEWSTATE")["value"]

cal_results_form_data = {
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "__VIEWSTATE": viewstate,
    "__VIEWSTATEGENERATOR": "BBBC20B8",
    "__EVENTVALIDATION": "/wEWAgKEib6eCQKYxoa5CABRE1bdUnTyMmdE4n0IKj4cWw4t",
    "SearchBy": "3",
    "ExactName": "on",
    "CaseSearchMode": "CaseNumber",
    "CaseSearchValue": "",
    "CitationSearchValue": "",
    "CourtCaseSearchValue": "",
    "PartySearchMode": "Name",
    "AttorneySearchMode": "Name",
    "LastName": "",
    "FirstName": "",
    "cboState": "AA",
    "MiddleName": "",
    "DateOfBirth": "",
    "DriverLicNum": "",
    "CaseStatusType": "0",
    "DateFiledOnAfter": "",
    "DateFiledOnBefore": "",
    "cboJudOffc": "38628",
    "chkCriminal": "on",
    "chkDtRangeCriminal": "on",
    "chkDtRangeFamily": "on",
    "chkDtRangeCivil": "on",
    "chkDtRangeProbate": "on",
    "chkCriminalMagist": "on",
    "chkFamilyMagist": "on",
    "chkCivilMagist": "on",
    "chkProbateMagist": "on",
    "DateSettingOnAfter": "5/8/2021",
    "DateSettingOnBefore": "7/8/2021",
    "SortBy": "fileddate",
    "SearchSubmit": "Search",
    "SearchType": "JUDOFFC",
    "SearchMode": "JUDOFFC",
    "NameTypeKy": "",
    "BaseConnKy": "",
    "StatusType": "true",
    "ShowInactive": "",
    "AllStatusTypes": "true",
    "CaseCategories": "CR",
    "RequireFirstName": "True",
    "CaseTypeIDs": "",
    "HearingTypeIDs": "",
    "SearchParams": "SearchBy~~Search+By:~~Judicial+Officer~~Judicial+Officer||chkExactName~~Exact+Name:~~on~~on||cboJudOffc~~Judicial+Officer:~~Updegrove,+Robert~~Updegrove,+Robert||DateSettingOnAfter~~Date+On+or+After:~~7/8/2021~~7/8/2021||DateSettingOnBefore~~Date+On+or+Before:~~8/8/2021~~8/8/2021||selectSortBy~~Sort+By:~~Filed+Date~~Filed+Date||CaseCategories~~Case+Categories:~~CR,CV,FAM,PR~~Criminal,+Civil,+Family,+Probate+and+Mental+Health",
}


cal_results = s.post(calendar_page_url, data=cal_results_form_data)

# print(req.text)
# print(req.headers)
print(cal_results.text)
print(viewstate)

with open("test.html", "w") as fh:
    fh.write(cal_results.text)

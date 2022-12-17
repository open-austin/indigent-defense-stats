import requests

cookies = {
    'ASP.NET_SessionId': 'xje0pfakmyuhk4yoq0v3zy45',
    '.ASPXFORMSPUBLICACCESS': '724F6854DDE7787639F7E8C3B588AE79BD5986C6207D40FD40F0D20F29895AB6E6ED284310138742F5B88E3F634F9AFECF83B56875E89581AE22B0C5D4755422EA49926B78A0B62F1F7171BAB29F5DC52F9C8EF9EA493535FDCA92BCF1FB808545B41012C6626320B10F69B7F0FE58060FF1B606537B779F99438D1E9F368E22AF81AA174665943A8F70A24D6606C89177A758D5',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://public.co.hays.tx.us',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

params = {
    'ID': '900',
}

data = {
    "__EVENTTARGET":"",
    "NodeID":"100,101,102,103,200,201,202,203,204,6112,400,401,402,403,404,405,406,407,6111",
    "NodeDesc":"All+Courts",
    "SearchBy":"0",
    "CaseSearchMode":"CaseNumber",
    "CourtCaseSearchValue":"12-2521CR",
    "cboJudOffc":"38501",
    "DateSettingOnAfter":"1/1/1970",
    "DateSettingOnBefore":"12/15/2022",
    "SearchSubmit":"Search",
    "SearchType":"CASE",
    "SearchMode":"CASENUMBER",
}


# '__VIEWSTATE':'/wEPDwULLTEwOTk1NTcyNzAPZBYCZg9kFgICAQ8WAh4HVmlzaWJsZWgWAgIDDw9kFgIeB29ua2V5dXAFJnRoaXMudmFsdWUgPSB0aGlzLnZhbHVlLnRvTG93ZXJDYXNlKCk7ZGSnBpspJun0H8O1uyepgbYYqxCR2g=='
# '__VIEWSTATEGENERATOR':'BBBC20B8'
# '__EVENTVALIDATION':'/wEWAgLohsKOBgKYxoa5CF1tgF3CUdvlNXx3DxVd7HpMX9tL'
# 'NodeID':'100,101,102,103,200,201,202,203,204,6112,400,401,402,403,404,405,406,407,6111'
# 'NodeDesc':'All Courts'
# 'SearchType':''
# 'SearchMode':''
# 'NameTypeKy':''
# 'BaseConnKy':''
# 'StatusType':''
# 'ShowInactive':''
# 'AllStatusTypes':''
# 'CaseCategories':''
# 'RequireFirstName':''
# 'CaseTypeIDs':''
# 'HearingTypeIDs':''
# 'SearchParams':''


response = requests.post('https://public.co.hays.tx.us/Search.aspx', params=params, cookies=cookies, headers=headers, data=data)

print(response.text)
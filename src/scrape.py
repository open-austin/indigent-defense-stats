import requests as r

s = r.Session()

req = s.get('http://public.co.hays.tx.us/default.aspx')

# print(req.text)
# print(req.headers)
print(req.cookies)
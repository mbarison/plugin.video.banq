import requests
import codecs
import re

from datetime import datetime,timedelta
from urllib.parse import quote

_sesh = requests.session()

BASE_URL = "http://iris.banq.qc.ca/alswww2.dll/"
# form data

r=_sesh.get("http://iris.banq.qc.ca")
print(r.cookies)
r=_sesh.get(BASE_URL+"APS_ZONES", params={"fn":"QuickSearch","Style":"Portal3"})
print(r.cookies)


obj_id = re.findall('METHOD="GET" ACTION="(Obj_[0-9]+)"', r.text)[0]

queryForm = {"Style" : "Portal3",
             "SubStyle" : "",
             "Lang" : "FRE",
             "ResponseEncoding" : "utf-8",
             "Method" : "QueryWithLimits",
             "SearchType" : "QuickSearch",
             "DB" : "SearchServer",
             "TargetSearchType" : "QuickSearch",
             "q.PageSize" : "10",
             "q.limits.limit" : "medium.limits.Films",
             "q.Query" : "criterion",
             }

# try to spoof cookies
def Set_Cookie(session, name, value, expires, path, domain, secure=None):
    # set time, it's in milliseconds
    today = datetime.today()

    if expires:
        expires = expires * 60 * 60 ;
        expires_date = today + timedelta(0, expires)

    cookie = {} #name : quote(value) }
    if expires:
        cookie["expires"] = expires_date.strftime("%a, %d %b %Y %H:%M:%S %Z")
    else:
        cookie["expires"] = ""
    if path:
        cookie["path"] = path
    else:
        cookie["path"] = ""
    if domain:
        cookie["domain"] = domain
    else:
        cookie["domain"] = ""
    if secure:
        cookie["secure"] = secure
    else:
        cookie["secure"] = ""
    
    session.cookies.set(name,quote(value),path=path,domain=domain)

Set_Cookie(_sesh, "banq_lang_c", "fr", 24, "/", ".banq.qc.ca" )
Set_Cookie(_sesh, "banq_from_c", "iris", None, "/", ".banq.qc.ca" )

r = _sesh.get(BASE_URL+obj_id, params=queryForm)

print(help(_sesh.cookies.set))
print(r)
print(dir(r))
print(r.url)
#print(r.text)
f=codecs.open("C:\\Users\\Marcello\\AppData\\Local\\Temp\\test.txt","w","utf-8")
f.write(r.text)
f.close()

print(_sesh.cookies)
for i in _sesh.cookies:
    print(i.name,i.value,i.expires)
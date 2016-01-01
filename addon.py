import requests
import codecs
import re
import json
import copy
from BeautifulSoup import BeautifulSoup

hexentityMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
# replace hexadecimal character reference by decimal one
hexentityMassage += [(re.compile('&#x([^;]+);'), 
                     lambda m: '&#%d;' % int(m.group(1), 16))]

def convert(html):
    return BeautifulSoup(html,
        convertEntities=BeautifulSoup.HTML_ENTITIES,
        markupMassage=hexentityMassage).contents[0].string

from datetime import datetime,timedelta
from urllib import quote

_sesh = requests.session()

PORTAL_URL = "https://www.banq.qc.ca/idp/Authn/UserPassword"

# login
#loginForm = { "j_username" : ,
#              "j_password" : ,}

f = open("pwd.json")
loginForm = json.load(f)
f.close()

BASE_URL = "http://iris.banq.qc.ca/alswww2.dll/"
# form data

r=_sesh.get(BASE_URL+"APS_ZONES", params={"fn":"AdvancedSearch","Style":"Portal3"})

obj_id = re.findall('METHOD="?GET"? ACTION="(Obj_[0-9]+)"', r.text)[0]

#
#print r.text

# example:
# http://iris.banq.qc.ca/alswww2.dll/Obj_564731451675170?Style=Portal3&SubStyle=&Lang=FRE&ResponseEncoding=utf-8&Method=QueryWithLimits&SearchType=AdvancedSearch&TargetSearchType=AdvancedSearch&DB=SearchServer&q.PageSize=10&q.form.t1.term=TitleSeries%3D&q.form.t1.expr=criterion&q.form.t2.logic=+and+&q.form.t2.term=au%3D&q.form.t2.expr=&q.form.t3.logic=+and+&q.form.t3.term=su%3D&q.form.t3.expr=&q.limits.limit=EnLigne.limits.enligne&q.limits.limit=medium.limits.Films&q.dpStart=&q.dpEnd=

queryForm = {"Style" : "Portal3",
             "SubStyle" : "",
             "Lang" : "FRE",
             "ResponseEncoding" : "utf-8",
             "Method" : "QueryWithLimits",
             "SearchType" : "AdvancedSearch",
             "DB" : "SearchServer",
             "TargetSearchType" : "AdvancedSearch",
             "q.PageSize" : "50",
             "q.limits.limit" : ["medium.limits.Films","EnLigne.limits.enligne"],
             #"q.Query" : "criterion",
             
             # advanced terms
             "q.form.t1.term" : "TitleSeries=",
             "q.form.t1.expr" : "criterion",
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

# here we should do the parsing

r=_sesh.get("http://res.banq.qc.ca/login?url=http://search.alexanderstreet.com/view/work/2742293")

# attempt authentication with Shibboleth

sso_url = re.findall('action="(https.+?)"', r.text)[0]
relay = re.findall('<input type="hidden" name="RelayState" value="(.+?)"', r.text)[0]
saml  = re.findall('<input type="hidden" name="SAMLRequest" value="(.+?)"', r.text)[0]
print sso_url
print relay
print saml

r = _sesh.post(sso_url, data={"RelayState" : relay, "SAMLRequest" : saml})
r=  _sesh.post(PORTAL_URL, data=loginForm)

sso_url = convert(re.findall('action="(https.+?)"', r.text)[0])
relay = re.findall('<input type="hidden" name="RelayState" value="(.+?)"', r.text)[0]
saml  = re.findall('<input type="hidden" name="SAMLResponse" value="(.+?)"', r.text)[0]
print sso_url
print relay
print saml

r = _sesh.post(sso_url, data={"RelayState" : relay, "SAMLResponse" : saml})

#r=_sesh.get("http://res.banq.qc.ca/login?url=http://search.alexanderstreet.com/view/work/2742293")
r=_sesh.get("http://res.banq.qc.ca/login?url=http://search.alexanderstreet.com/view/work/2742293")

f=codecs.open("/tmp/test.html","w","utf-8")
f.write(r.text)
f.close()

print(_sesh.cookies)
for i in _sesh.cookies:
    print(i.name,i.value,i.expires)
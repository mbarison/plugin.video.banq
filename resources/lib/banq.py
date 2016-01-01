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


from urllib import quote

# implement a singleton pattern for the session class
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

#Python2
class SingleSession(requests.Session):
    __metaclass__ = Singleton
    
"""    
_sesh = requests.session()

PORTAL_URL = "https://www.banq.qc.ca/idp/Authn/UserPassword"

# login
#loginForm = { "j_username" : ,
#              "j_password" : ,}

f = open("pwd.json")
loginForm = json.load(f)
f.close()







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
"""
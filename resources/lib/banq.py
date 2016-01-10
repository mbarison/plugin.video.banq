import requests
import codecs
import re
import json
import copy
from BeautifulSoup import BeautifulSoup
from xbmc import translatePath

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
class BanqSession(requests.Session):
    __metaclass__ = Singleton
    PORTAL_URL = "https://www.banq.qc.ca/idp/Authn/UserPassword"

    def __init__(self):
        super(BanqSession, self).__init__()
        self.logged_in = False
    
    def login(self):        
        if self.logged_in:
            return
        
        f = open(translatePath("special://home/addons/plugin.video.banq/pwd.json"))
        loginForm = json.load(f)
        f.close()

        r=self.get("http://res.banq.qc.ca/login")

        # attempt authentication with Shibboleth
        sso_url = re.findall('action="(https.+?)"', r.text)[0]
        relay = re.findall('<input type="hidden" name="RelayState" value="(.+?)"', r.text)[0]
        saml  = re.findall('<input type="hidden" name="SAMLRequest" value="(.+?)"', r.text)[0]
        print sso_url
        print relay
        print saml

        r = self.post(sso_url, data={"RelayState" : relay, "SAMLRequest" : saml})
        r=  self.post(self.PORTAL_URL, data=loginForm)

        sso_url = convert(re.findall('action="(https.+?)"', r.text)[0])
        relay = re.findall('<input type="hidden" name="RelayState" value="(.+?)"', r.text)[0]
        saml  = re.findall('<input type="hidden" name="SAMLResponse" value="(.+?)"', r.text)[0]
        print sso_url
        print relay
        #print saml

        r = self.post(sso_url, data={"RelayState" : relay, "SAMLResponse" : saml})

        for i in self.cookies:
            print(i.name,i.value,i.expires)
            
        print "LOGIN COMPLETE"
        self.logged_in = True
        return

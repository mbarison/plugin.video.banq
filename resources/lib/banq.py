import requests
import codecs
import re
import json
import copy
import threading
from BeautifulSoup import BeautifulSoup



# use this for testing only
import logging

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig() 
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


try:
    from xbmc import translatePath
except:
    import os
    def translatePath(p):
        return p.replace("special://home/addons/", os.path.expanduser("~/"))

hexentityMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
# replace hexadecimal character reference by decimal one
hexentityMassage += [(re.compile('&#x([^;]+);'), 
                     lambda m: '&#%d;' % int(m.group(1), 16))]

def convert(html):
    return BeautifulSoup(html,
        convertEntities=BeautifulSoup.HTML_ENTITIES,
        markupMassage=hexentityMassage).contents[0].string


from urllib import quote

# Thread safe singleton class
# Based on tornado.ioloop.IOLoop.instance() approach.
# See https://github.com/facebook/tornado
# class SingletonMixin(object):
#     __singleton_lock = threading.Lock()
#     __singleton_instance = None
# 
#     @classmethod
#     def __call__(cls, *args, **kwargs):
#         if not cls.__singleton_instance:
#             with cls.__singleton_lock:
#                 if not cls.__singleton_instance:
#                     cls.__singleton_instance = cls()
#         return cls.__singleton_instance

# implement a thread-safe singleton pattern for the session class
class MultithreadSingleton(type):
    _instances = {}
    _singleton_lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
                with cls._singleton_lock:
                    if cls not in cls._instances:
                        cls._instances[cls] = super(MultithreadSingleton, cls).__call__(*args, **kwargs)
        print "Instances %s" % cls._instances.values()
        print "Session instance %s" % cls._instances[cls]
        return cls._instances[cls]

#Python2
class BanqSession(requests.Session):
    __metaclass__ = MultithreadSingleton
    PORTAL_URL = "https://www.banq.qc.ca/idp/Authn/UserPassword"

    def __init__(self):
        super(BanqSession, self).__init__()
        self.logged_in = False
        print "REQUESTS %s" % requests.__version__
    
    def login(self):        
        if self.logged_in:
            print "%s already logged in" % self
            return
        
        print "Logging %s in" % self
        
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
            
        print "%s LOGIN COMPLETE" % self
        self.logged_in = True    
        return

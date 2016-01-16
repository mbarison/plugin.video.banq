import requests
import codecs
import re
import json
import copy
import threading
import pickle
import os
#import codecs
from BeautifulSoup import BeautifulSoup

# # use this for testing only
# import logging
# 
# # These two lines enable debugging at httplib level (requests->urllib3->http.client)
# # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# # The only thing missing will be the response.body which is not logged.
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1
#  
# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig() 
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


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

# implement a singleton pattern for the session class
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        print "Instances %s" % cls._instances.values()
        print "Session instance %s" % cls._instances[cls]
        return cls._instances[cls]

class BanqSession(requests.Session):
    __metaclass__ = Singleton
    PORTAL_URL = "https://www.banq.qc.ca/idp/Authn/UserPassword"
    __picklableObjects__ = ['path','obj_id','clean_login']
    ptn = re.compile("Obj_[0-9]+")

    def __init__(self):
        super(BanqSession, self).__init__()
        self.path   = translatePath("special://home/addons/plugin.video.banq")
        self.obj_id = None
        self.clean_login  = False
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        #print "REQUESTS %s" % requests.__version__
    
    def get(self, url, **kwargs):
        m = BanqSession.ptn.search(url)
        if m:
            obj_id = m.group(0)
            if obj_id != self.obj_id:
                self.obj_id = obj_id
                self.clean_login = True
        return super(BanqSession, self).get(url, **kwargs)
    
    def cleanup_login_cookies(self):
        print "Cleaning up login cookies"
        #for i in self.cookies:
        #    print i
        if "ezproxy" in self.cookies.keys(): #try:
            self.cookies.clear(".banq.qc.ca","/","ezproxy")
            self.cookies.clear("www.banq.qc.ca","/idp")
            self.cookies.clear("search.alexanderstreet.com.res.banq.qc.ca","/")
        else: #except:
            pass
        #print "After cleanup:"
        #for i in self.cookies:
        #    print i        
    
    @staticmethod
    def getPicklableObjects():
        return BanqSession.__picklableObjects__
    
    def __getstate__(self):
        state = super(BanqSession, self).__getstate__()
        for po in BanqSession.getPicklableObjects():
            state[po] = copy.deepcopy(self.__dict__[po])
        return state

    def __setstate__(self, state):
        super(BanqSession, self).__setstate__(state)
        for po in BanqSession.getPicklableObjects():
            self.__dict__[po] = state[po]
        return
    
    def load_cookies(self, fname):
        try:
            f = open(os.path.join(self.path, fname))
            cookie_dict = pickle.load(f)
            for k,v in cookie_dict.iteritems():
                self.cookies.set(k,v)
            f.close()
            print "Cookies loaded"
        except:
            print "Could not load cookies"
        return
    
    def save_cookies(self, fname):
        try:
            self.cookies.clear_expired_cookies()
            f = open(os.path.join(self.path, fname),"w")
            pickle.dump(self.cookies.get_dict(), f)
            f.close()
            print "Cookies saved"
        except:
            print "Could not save cookies"        
        return
    
    def login(self):        
        print "Logging %s in" % self
        if self.clean_login:
            self.cleanup_login_cookies()
        
        f = open(os.path.join(self.path, "pwd.json"))
        loginForm = json.load(f)
        f.close()

        r=self.get("http://res.banq.qc.ca/login")

        #f = codecs.open(os.path.join(self.path, "log.html"),"w","utf-8")
        #f.write(r.text)
        #f.close()

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

        #for i in self.cookies:
        #    print(i.name,i.value,i.expires)
            
        print "%s LOGIN COMPLETE" % self
        self.clean_login = True
        return

if not 'sesh' in dir():
    path = translatePath("special://home/addons/plugin.video.banq")
    if not os.path.isfile(os.path.join(path,"banq_session.pkl")):
        sesh = BanqSession()
    else:
        print "Opening %s" % os.path.join(path,"banq_session.pkl")
        f = open(os.path.join(path,"banq_session.pkl"))
        sesh = pickle.load(f)
        f.close()
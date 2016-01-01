from banq import SingleSession as sesh
from datetime import datetime,timedelta
from urllib import quote,unquote
from BeautifulSoup import BeautifulSoup
import re

BASE_URL = "http://iris.banq.qc.ca/alswww2.dll/"

def bs_parse(txt):
    '''Parses HTML via BeautifulSoup'''
    return BeautifulSoup(txt, convertEntities=BeautifulSoup.HTML_ENTITIES)

def get_records(txt):
    soup = bs_parse(txt)
    
    recs  = soup.findAll('td', {'class' :"SummaryImageCell"})
    recs += soup.findAll('td', {'class' :"SummaryImageCellStripe"})
    items = []
    for rec in recs:
        lnk = rec.find('a')
        items.append({ 'name'      : lnk["title"].strip(),
                       'url'       : BASE_URL+lnk['href'].replace("View=ISBD","View=Annotated"), # use all info
                       'thumbnail' : BASE_URL+"/Portal3/IMG/MAT/Video_enligne.png"
                      })

    return items

def get_record_info(url):
    r = sesh().get(unquote(url))
    soup = bs_parse(r.text)
    
    # hmmm, unstructured pages...
    link_ptn = re.compile("(http://res.banq.qc.ca/login\?url=http://search.alexanderstreet.com/view/work/[0-9]+)")
    
    item = {"url" : link_ptn.findall(r.text)[0]}
    item['name'] = soup.find('span', {'class' : "BoldTitle"})
    
    return [item]

def get_collection(query_string):
    r=sesh().get(BASE_URL+"APS_ZONES", params={"fn":"AdvancedSearch","Style":"Portal3"})

    obj_id = re.findall('METHOD="?GET"? ACTION="(Obj_[0-9]+)"', r.text)[0]
    
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
                 "q.form.t1.expr" : query_string,
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
    
    Set_Cookie(sesh(), "banq_lang_c", "fr", 24, "/", ".banq.qc.ca" )
    Set_Cookie(sesh(), "banq_from_c", "iris", None, "/", ".banq.qc.ca" )
    
    r = sesh().get(BASE_URL+obj_id, params=queryForm) 
    
    return get_records(r.text)
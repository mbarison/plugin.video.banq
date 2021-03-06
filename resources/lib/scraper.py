from datetime import datetime,timedelta
from urllib import quote,unquote
from BeautifulSoup import BeautifulSoup
import re

BASE_URL = "http://iris.banq.qc.ca/alswww2.dll/"

def bs_parse(txt):
    '''Parses HTML via BeautifulSoup'''
    return BeautifulSoup(txt, convertEntities=BeautifulSoup.HTML_ENTITIES)



def get_results_page(sesh, url, setid, lang="English", results=25):
    #print url
    
    # ok, so now I have to use POST for no reason? FACEPALM
    queryForm = {"Style" : "Portal3",
                 "SubStyle" : "",
                 "Lang" : lang.upper()[:3],
                 "ResponseEncoding" : "utf-8",
                 "BrowseAsHloc" : "",
                 "q.PageSize" : results,
                 "SET"        : setid,
                 }
    
    
    r = sesh.get(url, timeout=None) #post(url, data=queryForm)
    #print r.content
        
    return get_records(r.content,results)

def get_records(txt,results):
    soup = bs_parse(txt)
    
    ptn = re.compile("\s\[ressource.+que\]\s?")
    
    _set  = re.findall('<INPUT TYPE=HIDDEN NAME="Set" VALUE = "(.+?)">', txt)[0]
    _page = int(re.findall('id="SearchResultsPage" name="Query.Page" value="([0-9]+)"', txt)[0])
    _lastno = soup.find("div", {"class":"searchHits"}).contents[0]
    _lastno = int(re.findall("\(([0-9]+)\)", _lastno)[0])
    
    recs  = soup.findAll('td', {'class' :"SummaryImageCell"})
    recs += soup.findAll('td', {'class' :"SummaryImageCellStripe"})
    items = []
    skiplinks = []
    for rec in recs:
        lnk = rec.find('a')
        items.append({ 'name'      : ptn.sub("", lnk["title"]).strip().replace("=",u" \u2014"),
                       'url'       : BASE_URL+lnk['href'].replace("View=ISBD","View=Annotated"), # use all info
                       'thumbnail' : BASE_URL+"/Portal3/IMG/MAT/Video_enligne.png",
                       'startno'   : (_page-1)*results,
                       'lastno'    : _lastno,
                      })

    

    # let's see i there's any records left
    for lnk in soup.findAll('a', {'class' : "pageNavLink"}):
        skiplinks.append({'name' : lnk["title"],
                          'url'       : BASE_URL+lnk['href'],
                          'thumbnail' : "http://iris.banq.qc.ca"+lnk.find("img")["src"],
                          'set'       : _set})

    return items,skiplinks

def get_record_info(sesh, url):
    
    r = sesh.get(unquote(url), timeout=None)
    soup = bs_parse(r.content)
    
    print r.content
    
    # hmmm, unstructured pages...
    link_ptn = re.compile("(http://res.banq.qc.ca/login\?url=http://search.alexanderstreet.com/view/work/[0-9]+)")
    ptn = re.compile("\s\[ressource.+que\]\s?")
    
    item = {"url" : link_ptn.findall(r.content)[0]}
    item['name'] = ptn.sub("",soup.find('span', {'class' : "BoldTitle"}).text).replace("(Film)","").replace("=",u" \u2014").strip()
    
    return [item]

def get_collection(sesh, category, query_string, lang="English", results=25):
    
    r=sesh.get(BASE_URL+"APS_ZONES", params={"fn":"AdvancedSearch","Style":"Portal3"}, timeout=None)

    obj_id = re.findall('METHOD="?GET"? ACTION="(Obj_[0-9]+)"', r.content)[0]
    
    # example:
    # http://iris.banq.qc.ca/alswww2.dll/Obj_564731451675170?Style=Portal3&SubStyle=&Lang=FRE&ResponseEncoding=utf-8&Method=QueryWithLimits&SearchType=AdvancedSearch&TargetSearchType=AdvancedSearch&DB=SearchServer&q.PageSize=10&q.form.t1.term=TitleSeries%3D&q.form.t1.expr=criterion&q.form.t2.logic=+and+&q.form.t2.term=au%3D&q.form.t2.expr=&q.form.t3.logic=+and+&q.form.t3.term=su%3D&q.form.t3.expr=&q.limits.limit=EnLigne.limits.enligne&q.limits.limit=medium.limits.Films&q.dpStart=&q.dpEnd=

    if category == "collection":
        query_term = "TitleSeries="
    elif category == "author":
        query_term = "au="
    elif category == "title":
        query_term = "ti="
    elif category == "subject":
        query_term = "su="

    queryForm = {"Style" : "Portal3",
                 "SubStyle" : "",
                 "Lang" : lang.upper()[:3],
                 "ResponseEncoding" : "utf-8",
                 "Method" : "QueryWithLimits",
                 "SearchType" : "AdvancedSearch",
                 "DB" : "SearchServer",
                 "TargetSearchType" : "AdvancedSearch",
                 "q.PageSize" : results,
                 "q.limits.limit" : ["medium.limits.Films","EnLigne.limits.enligne"],
                 #"q.Query" : "criterion",
                 
                 # advanced terms
                 "q.form.t1.term" : query_term, #"TitleSeries=",
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
    
    Set_Cookie(sesh, "banq_lang_c", lang.lower()[:2], 24, "/", ".banq.qc.ca" )
    Set_Cookie(sesh, "banq_from_c", "iris", None, "/", ".banq.qc.ca" )
    
    r = sesh.get(BASE_URL+obj_id, params=queryForm, timeout=None) 
    
    return get_records(r.content,results)

def get_video_paywall(sesh, url, uname, pwd):
    sesh.login(uname, pwd)
    r = sesh.get(unquote(url), timeout=None)
    ptn = re.compile('source src="(.+?)" type="video/mp4"')
    return ptn.findall(r.content)[0]
import os, pickle

from xbmcswift2 import Plugin
from operator import itemgetter

#from resources.lib.banq import login
from resources.lib.scraper import *
from xbmc import translatePath, Keyboard
from xbmcplugin import setPluginFanart

import subprocess, platform, os


plugin = Plugin()

# get plugin globals
addonID = plugin.addon.getAddonInfo('id')
addonUserdataFolder = translatePath("special://profile/addon_data/"+addonID)
translation = plugin.addon.getLocalizedString
#setPluginFanart(addonID,'special://home/addons/'+addonID+'/fanart.jpg')

if not 'sesh' in dir():
    from resources.lib.banq import loadSession
    sesh = loadSession(addonUserdataFolder)

# intialize the settings if not existing
while not os.path.exists(os.path.join(addonUserdataFolder, "settings.xml")):
    plugin.addon.openSettings()
        
# get parameters
debugMode = plugin.addon.getSetting("debug")
sesh.set_debug_mode(debugMode)

if debugMode:
    from resources.lib.banq import activate_logging
    activate_logging()
        
banqUsername      = plugin.addon.getSetting("username")
banqPassword      = plugin.addon.getSetting("password")
preferredLanguage = plugin.addon.getSetting("lang")
resultsPerPage    = int(plugin.addon.getSetting("max_results"))

if preferredLanguage == "1":
    preferredLanguage = "French"
else:
    preferredLanguage = "English"  

@plugin.route('/')
def main_menu():
    items = [{'label': translation(32102), 'path': plugin.url_for('search_collection',category="collection")},
             {'label': translation(32103), 'path': plugin.url_for('search_collection',category="author")},
             {'label': translation(32104), 'path': plugin.url_for('search_collection',category="title")},
             {'label': translation(32105), 'path': plugin.url_for('search_collection',category="subject")},
             {'label': translation(32101), 'path': plugin.url_for('show_collection',category="collection",query='Criterion')}]
    return items

@plugin.route('/search_collection/<category>')
def search_collection(category):
    kb = Keyboard('', translation(32106))
    kb.doModal()
    if (kb.isConfirmed()):
        text = kb.getText().strip()
    else:
        return
    
    return show_collection(text,category)

@plugin.route('/collection/<category>/<query>')
def show_collection(query,category):
    records,skiplinks = get_collection(sesh, category, query, preferredLanguage, resultsPerPage)

    items = []
 
    for rec in skiplinks[:len(skiplinks)/2]:
        items.append({'label': rec["name"],
                      'path': plugin.url_for('show_results', url=rec["url"], setid=rec["set"]),
                      'thumbnail' : rec["thumbnail"]})

    records.sort(key=lambda x:x["name"])

    for i,rec in enumerate(records):
        items.append({'label': "[%d/%d] %s" % (i+1+rec["startno"],rec["lastno"],rec["name"]),
                      'path': plugin.url_for('show_record_info', url=rec["url"]),
                      'thumbnail' : rec["thumbnail"],
                      #'info' : {"Plot" : girl.description},
                      })

    for rec in skiplinks[len(skiplinks)/2:]:
        items.append({'label': rec["name"],
                      'path': plugin.url_for('show_results', url=rec["url"], setid=rec["set"]),
                      'thumbnail' : rec["thumbnail"]})

    
    
    print "ITEMS %d" % len(items)
   
    return items

@plugin.route('/nextpage/<url>/<setid>')
def show_results(url, setid):
    print url, setid
    records,skiplinks = get_results_page(sesh, url, setid, preferredLanguage, resultsPerPage)

    items = []
 
    for rec in skiplinks[:len(skiplinks)/2]:
        items.append({'label': rec["name"],
                      'path': plugin.url_for('show_results', url=rec["url"], setid=rec["set"]),
                      'thumbnail' : rec["thumbnail"]})

    records.sort(key=lambda x:x["name"])

    for i,rec in enumerate(records):
        items.append({'label': "[%d/%d] %s" % (i+1+rec["startno"],rec["lastno"],rec["name"]),
                      'path': plugin.url_for('show_record_info', url=rec["url"]),
                      'thumbnail' : rec["thumbnail"],
                      #'info' : {"Plot" : girl.description},
                      })

    for rec in skiplinks[len(skiplinks)/2:]:
        items.append({'label': rec["name"],
                      'path': plugin.url_for('show_results', url=rec["url"], setid=rec["set"]),
                      'thumbnail' : rec["thumbnail"]})

    
    
    print "ITEMS %d" % len(items)
    
    return items

@plugin.route('/record/<url>/')
def show_record_info(url):
    records = get_record_info(sesh, url)

    videos = [{
        'label': rec["name"],
        'path': plugin.url_for('play_video', url=rec['url']),
        'is_playable': True,
        #'thumbnail' : girl.thumbnail,
        #'icon'      : girl.thumbnail,
        #'info' : {"Plot" : girl.description},
    } for rec in records]

    by_label = itemgetter('label')
    sorted_items = sorted(videos, key=by_label)
    return sorted_items


@plugin.route('/videos/<url>/')
def play_video(url):
    videourl = get_video_paywall(sesh, url, banqUsername, banqPassword)
    plugin.log.info('Playing url: %s' % videourl)
    plugin.set_resolved_url(videourl)
    if platform.machine() == 'x86_64' and not 'xbmc' in dir():
        subprocess.call(["vlc",videourl])


if __name__ == '__main__':
    print "STARTING SESSION %s" % sesh
    print "PID %s" % (os.getpid())
    print "Plugin instance %s" % plugin
    #sesh.load_cookies("banq_cookies.pkl") 
    print "Addon ID: %s" % addonID 
        
    plugin.run()
    
    print "REACHED END OF PLUGIN, STORING SESSION DATA"
    #sesh.save_cookies("banq_cookies.pkl")
    f = open(os.path.join(addonUserdataFolder,"banq_session.pkl"),"w")
    pickle.dump(sesh, f)
    f.close()
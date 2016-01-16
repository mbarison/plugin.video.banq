import pickle

from xbmcswift2 import Plugin
from operator import itemgetter

#from resources.lib.banq import login
from resources.lib.scraper import *
from xbmc import translatePath

if not 'sesh' in dir():
    from resources.lib.banq import sesh

import subprocess, platform, os, threading

plugin = Plugin()

@plugin.route('/')
def main_menu():
    print dir()
    items = [{'label': 'Show Criterion Collection', 'path': plugin.url_for('show_collection',url='Criterion')},]
          #{'label': 'Show Trailers', 'path': plugin.url_for('show_galleries',url='category/trailers')},
          #{'label': 'Show Tags', 'path': plugin.url_for('show_tags',url='tags')},
          #]
    return items

@plugin.route('/collection/<url>')
def show_collection(url):
    records,skiplinks = get_collection(sesh, url)

    items = []
 
    for rec in skiplinks[:len(skiplinks)/2]:
        items.append({'label': rec["name"],
                      'path': plugin.url_for('show_results', url=rec["url"], set=rec["set"]),
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
                      'path': plugin.url_for('show_results', url=rec["url"], set=rec["set"]),
                      'thumbnail' : rec["thumbnail"]})

    
    
    print "ITEMS", len(items)
   
    return items

@plugin.route('/collection/<url>/<set>')
def show_results(url,set):
    print url, set
    records,skiplinks = get_results_page(sesh, url, set)

    items = []
 
    for rec in skiplinks[:len(skiplinks)/2]:
        items.append({'label': rec["name"],
                      'path': plugin.url_for('show_results', url=rec["url"], set=rec["set"]),
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
                      'path': plugin.url_for('show_results', url=rec["url"], set=rec["set"]),
                      'thumbnail' : rec["thumbnail"]})

    
    
    print "ITEMS", len(items)
    
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
    videourl = get_video_paywall(sesh, url)
    plugin.log.info('Playing url: %s' % videourl)
    plugin.set_resolved_url(videourl)
    if platform.machine() == 'x86_64' and not 'xbmc' in dir():
        subprocess.call(["vlc",videourl])


if __name__ == '__main__':
    print "STARTING SESSION %s" % sesh
    print "PID %s THREAD %s" % (os.getpid(), threading.current_thread())
    print "Plugin instance %s" % plugin
    #sesh.load_cookies("banq_cookies.pkl")
    addonID = plugin.addon.getAddonInfo('id')
    print "Addon ID: %s" % addonID 
    addonUserdataFolder = translatePath("special://profile/addon_data/"+addonID)
    print translatePath("special://profile/addon_data/"+addonID)
    while (not os.path.exists(translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
        plugin.addon.openSettings()

    
    plugin.run()
    print "REACHED END OF PLUGIN, STORING SESSION DATA"
    #sesh.save_cookies("banq_cookies.pkl")
    path = translatePath("special://home/addons/plugin.video.banq")
    f = open(os.path.join(path,"banq_session.pkl"),"w")
    pickle.dump(sesh, f)
    f.close()
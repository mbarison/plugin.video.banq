from xbmcswift2 import Plugin
from operator import itemgetter

#from resources.lib.banq import login
from resources.lib.scraper import *
from resources.lib.banq import BanqSession

import subprocess, platform

plugin = Plugin()


@plugin.route('/')
def main_menu():
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

    for rec in records:
        items.append({'label': rec["name"],
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

@plugin.route('/results/<url>/<set>')
def show_results(url,set):
    print url, set
    records,skiplinks = get_results_page(sesh, url, set)

    items = []
 
    for rec in skiplinks[:len(skiplinks)/2]:
        items.append({'label': rec["name"],
                      'path': plugin.url_for('show_results', url=rec["url"], set=rec["set"]),
                      'thumbnail' : rec["thumbnail"]})

    for rec in records:
        items.append({'label': rec["name"],
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

    print records

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
    videourl = get_video_paywall(url)
    plugin.log.info('Playing url: %s' % videourl)
    plugin.set_resolved_url(videourl)
    if platform.machine() == 'x86_64' and not 'xbmc' in dir():
        subprocess.call(["vlc",videourl])


if __name__ == '__main__':
    global sesh
    sesh = BanqSession()
    print "STARTING SESSION %s" % sesh
    plugin.run()

from xbmcswift2 import Plugin
from operator import itemgetter

#from resources.lib.banq import login
from resources.lib.scraper import *

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
    records = get_collection(url)

    items = [{
        'label': rec["name"],
        'path': plugin.url_for('show_record_info', url=rec["url"]),
        'thumbnail' : rec["thumbnail"],
        #'info' : {"Plot" : girl.description},
    } for rec in records]

    #items.insert(0, {'label' : "Previous Girls",
    #               'path'  : plugin.url_for('show_girls',url=[1,pagecount-1][pagecount>1])})
    #items.insert(1, {'label' : "Next Girls",
    #               'path'  : plugin.url_for('show_girls',url=pagecount+1)})
    
    print "ITEMS", len(items)
   
    return items


@plugin.route('/record/<url>/')
def show_record_info(url):
    records = get_record_info(url)

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

"""
@plugin.route('/videos/<url>/')
def play_video(url):
    video = Video.from_url(url)
    url = video.video_url
    plugin.log.info('Playing url: %s' % url)
    plugin.set_resolved_url(url)
    if platform.machine() == 'x86_64':
        subprocess.call(["vlc",url])
"""

if __name__ == '__main__':
    plugin.run()

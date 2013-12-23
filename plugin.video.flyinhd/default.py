import urllib, urllib2
import xbmcplugin, xbmcgui, xbmc
import re, sys, cgi
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
from BeautifulSoup import BeautifulSoup
from pprint import pprint

try:
    import json
except ImportError:
    import simplejson as json

try:
  import StorageServer
except:
  import storageserverdummy as StorageServer

BASE_URL = "http://www.flyinhd.com"
LANGS = [ 'tamil', 'hindi', 'telugu' ]

addonId = 'plugin.video.flyinhd'
addon = Addon( addonId, sys.argv )
addonPath = addon.get_profile()
cookiePath = os.path.join( addonPath, 'cookies' )
cookieFile = os.path.join( cookiePath, "cookies.txt" )

net = Net()
if not os.path.exists(cookiePath):
   os.makedirs(cookiePath)
else:
   net.set_cookies( cookieFile )

cache = StorageServer.StorageServer( addonId )
cache.dbg = True
cache.dbglevel = 10

def parseMoviePage( lang ):
   print "parseMoviePage, lang:" + lang
   url = BASE_URL + '/?lang=' + lang
   response = net.http_GET( url )
   net.save_cookies( cookieFile )

   movieIndex = {}
   url = BASE_URL + '/movies'
   response = net.http_GET( url )
   net.save_cookies( cookieFile )
   html = response.content
   soup = BeautifulSoup( html )
   div = soup.findAll( 'div', { 'id' : re.compile('_filter$') } )
   for d in div:
      id = d[ 'id' ]
      key = id.split('_')[ 0 ]
      key = key.capitalize()
      href = d.findAll( 'a' )

      if key == 'Activity':
         movieIndex[ key ] = BASE_URL + '/movies?filter=activity&filter_value=recently_posted'
         continue

      result = {}
      for h in href:
         url = BASE_URL + h[ 'href' ]
         title = h.string
         result[ title ] = url
      movieIndex[ key ] = result

   return movieIndex

def Main_Categories():
   print "cookie path:" + cookiePath
   print "cookie file:" + cookieFile
   for lang in LANGS:
      url = BASE_URL + '/?lang=' + lang
      addon.add_directory( { 'mode' : 'movie', 'url' : url, 'lang' : lang },
                           { 'title' : '[B]%s[/B]' % lang.capitalize() } )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))
                       
def Main_Movie( url, lang ):
   print "movie:" + url
   addon.add_directory( { 'mode' : 'movie_recent', 'url' : BASE_URL, 'lang' : lang }, 
                        { 'title' : '[B]Most Recent[/B]' } )

   #movieIndex = cache.cacheFunction( parseMoviePage, lang )
   movieIndex = parseMoviePage( lang )
   for key, value in sorted( movieIndex.items() ):
      if type( value ) != dict:
         mode = 'leaf'
         path = value + '&offset=1'
      else:
         mode = 'tree'
         path = key
      addon.add_directory( { 'mode' : mode, 'url' : path, 'lang' : lang }, 
                           { 'title' : '[B]%s[/B]' % key } )
   
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Main_Tree( url, lang ):
   print "tree " + url
   #movieIndex = cache.cacheFunction( parseMoviePage, lang )
   movieIndex = parseMoviePage( lang )
   path = url.split( '&' )
   for key in path:
      movieIndex = movieIndex[ key ]

   for key, value in sorted( movieIndex.items() ):
      if type( value ) != dict:
         mode = 'leaf'
         path = value + '&offset=1'
      else:
         mode = 'tree'
         path = url + '&' + key
      addon.add_directory( { 'mode' : mode, 'url' : path, 'lang' : lang}, 
                           { 'title' : '[B]%s[/B]' % key } )
      
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Main_Leaf( url, lang ):
   print "leaf:" + url
   path = url.split( '&' )[ -1 ]
   offset = path.split( '=' )[ 1 ]
   response = net.http_GET( url )
   net.save_cookies( cookieFile )
   html = response.content
   soup = BeautifulSoup( html )
   div = soup.findAll( 'div', { 'class' : 'cat-thumb' } )
   for d in div:
      video = d.find( 'div', { 'class' : 'play-cat' } )
      url = BASE_URL + video.a[ 'href' ]
      title = video.img[ 'alt' ]
      img = video.img[ 'src' ]

      addon.add_directory( { 'mode' : 'load_video', 'url' : url, 'lang' : lang, 'name' : title }, 
                           { 'title' : title.encode('utf-8')}, 
                           img=img, total_items=len(div) )

   nextPage = int( offset ) + 1
   pages = soup.find( 'div', { 'class' : 'pagination pagination-centered' } )
   for li in pages.ul.findAll( 'li' ):
      offset = int( li.span.text )
      if offset == nextPage:
         nextPageUrl = BASE_URL + li.a[ 'href' ]
         addon.add_directory( { 'mode' : 'leaf', 'url' : nextPageUrl, 'lang' : lang }, 
                              { 'title' : '[B]Next Page...[/B]' } )
         break

   xbmcplugin.endOfDirectory(int(sys.argv[1]))
       
def Movie_Recent( url, lang ):
   print "recent:" + url
   response = net.http_GET( url )
   net.save_cookies( cookieFile )
   html = response.content
   soup = BeautifulSoup( html )
   div = soup.findAll( 'div', { 'class' : 'play' } )
   for d in div:
      url = BASE_URL + d.a[ 'href' ]
      title = d.img[ 'alt' ]
      img = d.img[ 'src' ]

      addon.add_directory( { 'mode' : 'load_video', 'url' : url, 'name' : title, 'lang' : lang }, 
                           { 'title' : title.encode('utf-8')}, 
                           img=img, total_items=len(div) )

   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Load_Video( name, url ):
   print "load_video:" + name + ":" + url
   response = net.http_GET( url )
   net.save_cookies( cookieFile )
   html = response.content
   stream_url = re.compile( "file: \"(.+?)\"" ).findall( html )[ 0 ]
   print "url:" + stream_url

   pDialog = xbmcgui.DialogProgress()
   pDialog.create('Streaming ' + name )

   playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
   playlist.clear()
   listitem = xbmcgui.ListItem( name )
   playlist.add(stream_url, listitem)
   xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(playlist)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
lang = addon.queries.get('lang', None)
name = addon.queries.get('name', None)
play = addon.queries.get('play', None)

print "MODE: "+str(mode)
print "URL: "+str(url)
print "LANG: "+str(lang)
print "Name: "+str(name)
print "play: "+str(play)
print "arg1: "+sys.argv[1]
print "arg2: "+sys.argv[2]

if play:
   stream_url = None
   if 'dailymotion' in url:
      stream_url = url
   else:
      hosted_media = urlresolver.HostedMediaFile( url=url, title=name )
      print "hosted_media"
      print hosted_media
      if hosted_media:
         stream_url = hosted_media.resolve()
         print stream_url

   if stream_url:
      addon.resolve_url(stream_url)
   else:
      print "unable to resolve"
      addon.show_ok_dialog( [ 'Unknown hosted video' ], title='Playback' )
else:
   if mode == 'main':
      Main_Categories()
          
   elif mode == 'movie':
      Main_Movie( url, lang )

   elif mode == 'tree':
      Main_Tree( url, lang )

   elif mode == 'leaf':
      Main_Leaf( url, lang )

   elif mode == 'movie_recent':
      Movie_Recent( url, lang )

   elif mode == 'load_video':
      Load_Video( name, url )


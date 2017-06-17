import urllib, urllib2
import xbmcplugin, xbmcgui, xbmc
import re, sys, cgi, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
from BeautifulSoup import BeautifulSoup
import unicodedata
import jsunpack
#from pprint import pprint

try:
    import json
except ImportError:
    import simplejson as json

try:
  import StorageServer
except:
  import storageserverdummy as StorageServer

MOVIE_URL = "http://tamilgun.pro/categories/new-movies/"
HD_MOVIE_URL = "http://tamilgun.pro/categories/hd-movies/"
net = Net()
addonId = 'plugin.video.oliyumoliyum'
addon = Addon( addonId, sys.argv )
addonPath = xbmc.translatePath( addon.get_path() )
resPath = os.path.join( addonPath, 'resources' )
tvxmlFile = os.path.join( resPath, 'livetv.xml' )
radioxmlFile = os.path.join( resPath, 'liveradio.xml' )
iconPath = os.path.join( resPath, 'images' )

cache = StorageServer.StorageServer( addonId )
cache.dbg = True

def getImgPath( icon ):
   icon = icon + '.png'
   imgPath = os.path.join( iconPath, icon )
   if os.path.exists( imgPath ):
      return imgPath
   else:
      return ''

def parseMainPage():
   def parseUl( ul ):
      result = {}
      for li in ul.findAll( 'li', recursive=False ):
         key = li.span.text
         url = li.a[ 'href' ]
         u = li.find( 'ul' )
         if key == 'Comedy':
            result[ key ] = url
         elif u:
            result[ key ] = parseUl( u )
         else:
            result[ key ] = url
      return result

   url = "http://www.tubetamil.com"
   response = net.http_GET( url )
   html = response.content
   soup = BeautifulSoup( html )
   div = soup.find( 'div', { 'id' : 'mainmenu' } )
   tubeIndex = parseUl( div.ul )
   return tubeIndex

def parseTvPage():
   tvChannel = {}
   xfile = open(tvxmlFile, 'r').read()
   soup = BeautifulSoup( xfile )
   for category in soup.categories.findAll( 'category' ):
      key = category[ 'name' ]
      result = {}
      for channel in category.findAll( 'channel' ):
         name = channel[ 'name' ]
         url = channel.url.text
         img = channel.thumb.text
         result[ name ] = ( url, img )
      tvChannel[ key ] = result
   return tvChannel

def parseRadioPage():
   radioChannel = []
   xfile = open(radioxmlFile, 'r').read()
   soup = BeautifulSoup( xfile )
   for channel in soup.findAll( 'channel' ):
      name = channel[ 'name' ]
      url = channel.url.text
      img = channel.thumb.text
      radioChannel.append( ( name, url, img ) )
   return radioChannel

def parseMoviePage( url ):
   print "movie:" + url
   try:
      req = urllib2.Request(url)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
      response = urllib2.urlopen(req)
      html = response.read()
   except urllib2.HTTPError, e:
      html = e.fp.read()
      pass

   srcRegex = '<a href="(.+?)".*><i class="icon-play"></i></a>'
   imgRegex = '<img.*src="\s*(.+?)\s*" alt="(.+?)" />'
   navRegex = '<li><a class="next page-numbers" href="(.+?)">'

   src = re.compile( srcRegex ).findall( html )
   img = re.compile( imgRegex ).findall( html )
   nav = re.compile( navRegex ).findall( html )

   return nav, zip( src, img )

def parseYoutube( url ):
   videos = []
   link = urllib2.urlparse.urlsplit( url )
   query = link.query
   netloc = link.netloc
   path = link.path

   print "youtube url : " + url

   def parseYoutubePlaylist( playlistId ):
      videos = []
      yturl = 'http://gdata.youtube.com/feeds/api/playlists/' + playlistId
      try:
         response = net.http_GET( yturl )
         html = response.content
      except urllib2.HTTPError, e:
         print "HTTPError : " + str( e )
         return videos

      soup = BeautifulSoup( html )

      for video in soup.findChildren( 'media:player' ):
         videoUrl = str( video[ 'url' ] )
         print "youtube video : " + videoUrl
         videos += parseYoutube( videoUrl )
      return videos

   # Find v=xxx in query if present
   qv = ''
   if query:
      qs = cgi.parse_qs( query )
      qv = qs.get( 'v', [''] )[ 0 ]
      if qv:
         qv = '?v=' + qv
   
   # Handle youtube gdata links
   playlistId = ''
   if re.search( '\?list=PL', url ):
      playlistId = re.compile("\?list=PL(.+?)&").findall( url )[ 0 ]
   elif re.search( '\?list=', url ):
      playlistId = re.compile("\?list=(.+?)&").findall( url )[ 0 ]
   elif re.search( '/p/', url ):
      playlistId = re.compile("/p/(.+?)(?:/|\?|&)").findall( url )[ 0 ]
   elif re.search( 'view_play_list', url ):
      plyalistId = re.compile("view_play_list\?.*?&amp;p=(.+?)&").findall( url)[ 0 ]

   if playlistId:
      print "playlistId : " + playlistId
      videos += parseYoutubePlaylist( playlistId )
   else:
      videos += [ 'http://' + netloc + path + qv ]
   return videos

def parseToolstube( url ):
   html = net.http_GET(url).content
   src = re.search('var files = \'{".*":"(.+?)"}', html)
   return urllib.unquote(src.group(1)).replace('\\/', '/')+'|Referer=http://toolstube.com/'
    
def parsePlayhd( url ):
   if url.endswith('.mp4'):
      return url
   pattern = '(?://|\.)(playhd\.(?:video|fo))/embed\.php?.*?vid=([0-9]+)[\?&]*'
   r = re.search(pattern, url)
   if not r:
      return None

   host, media_id = r.groups()
   wurl = 'http://www.playhd.video/embed.php?vid=%s' % media_id
   html = net.http_GET(wurl).content
   r = re.search('"content_video".*\n.*?src="(.*?)"', html)
   if r:
      stream_url = r.group(1) + '|Referer=http://www.playhd.video/embed.php'
   else:
      stream_url = None
        
   print "stream_url", stream_url
   return stream_url

def resolvable( hmf, url ):
   if 'youtube' in url:
      print "Skipping youtube video"
      return False

   if 'facebook' in url:
      print "Skipping facebook video"
      return False

   if not hmf:
      return False

   if not hmf.valid_url():
      return False

   resolvers = hmf._HostedMediaFile__resolvers
   for resolver in resolvers:
      if resolver.get_host_and_id( url ):
         return True
   return False

def Load_Video( url ):
   print "Load_Video=" + url
   try:
      req = urllib2.Request(url)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
      response = urllib2.urlopen(req)
      html = response.read()
   except urllib2.HTTPError, e:
      html = e.fp.read()
      pass

   soup = BeautifulSoup( html )
   sourceVideos = []

   try:
      jsun = jsunpack.unpack(html).replace('\\','')
      sources = json.loads( re.findall('sources:(.*?)\}\)', jsun)[0] )
      for source in sources:
         url = source['file']
         url = urllib.quote_plus(url)
         sourceVideos += [ 'src="%s" data-res="%s"' % (url, source['label']) ]
   except:
      pass

   # Handle href tags
   for a in soup.findAll('a', href=True):
      if a['href'].find("youtu.be") != -1:
         sourceVideos.append( a['href'].split()[0] )
         
      if a['href'].find("youtube") != -1:
         sourceVideos.append( a['href'].split()[0] )
         
      if a['href'].find("tamildbox") != -1:
         src = a['href'].split()[0]
         if 'watch' not in src:
            continue
         print "tamildbox", src
         resp = net.http_GET( src )
         dbox = resp.content
         sourceVideos += re.compile( '<iframe(.+?)>').findall( dbox )

         codes = re.findall('"return loadEP.([^,]*),(\d*)', dbox)
         for ep_id, server_id in codes:
            durl = 'http://www.tamildbox.com/actions.php?case=loadEP&ep_id=%s&server_id=%s'%(ep_id,server_id)
            dhtml = net.http_GET(durl).content
            source = re.compile( '(?i)<iframe(.+?)>').findall( dhtml )[0]
            if 'googleapis' in source:
               docid = re.findall('docid=([^&]*)',source)[0]
               source = [ 'src="https://drive.google.com/open?id=' + docid + '"']
               sourceVideos += source
            sourceVideos += re.compile( '(?i)<iframe(.+?)>').findall( dhtml )
            

   # Handle 'file':'src' tags in jwplayer
   src = re.compile('sources: (\[.+\])').findall( html )
   if src:
      links = json.loads( src[ 0 ] )
      for link in links:
         if 'label' in link:
            res = link[ 'label' ]
         else:
            res = '720p'
         s = link[ 'file' ].replace('\\', '')
         sourceVideos += [ 'src="%s" data-res="%s"' % ( s, res ) ]

   # Handle iframe tags
   sourceVideos += re.compile( '(?i)<iframe(.+?)>').findall( html )
   sourceVideos += re.compile( '<source(.+?)>').findall( html )

   # Handle Youtube new window
   src = re.compile( 'onclick="window.open\((.+?),' ).findall( html )
   if src:
      sourceVideos += src[ 0 ]

   if len( sourceVideos ) == 0:
      print "No video sources found!!!!"
      addon.show_ok_dialog( [ 'Page has unsupported video' ], title='Playback' )
      return
      
   print 'source videos', sourceVideos
   videoItem = []
   for sourceVideo in sourceVideos:
      print "sourceVideo=" + sourceVideo
      sourceVideoOrig = sourceVideo

      if 'src=' in sourceVideo:
         sourceVideo = re.compile( 'src=(?:\"|\')(.+?)(?:\"|\')' ).findall( sourceVideo )[0]

      if 'SRC=' in sourceVideo:
         sourceVideo = re.compile( 'SRC=(?:\"|\')(.+?)(?:\"|\')' ).findall( sourceVideo )[0]

      sourceVideo = urllib.unquote( sourceVideo )
      print "sourceVideo=" + sourceVideo
      link = urllib2.urlparse.urlsplit( sourceVideo )
      if link.path == sourceVideo:
         print "Skipping unknown path"
         continue

      host = link.hostname
      host = host.replace( 'www.', '' )
      host = host.replace( '.com', '' )
      sourceName = host.capitalize()
      print "sourceName = " + sourceName
      
      if '.mp4' in sourceVideo:
         videoItem.append( (sourceVideo, sourceName ) )
         
      elif 'playhd.video' in host or 'playhd.fo' in host:
         sourceVideo = parsePlayhd( sourceVideo )
         if sourceVideo:
            videoItem.append( (sourceVideo, sourceName ) )
         else:
            print "Skipping playhd.video"
            continue
         
      elif 'tamilgun' in host:
         if 'data-res' in sourceVideoOrig:
            res = re.findall( 'data-res="(.+?)"', sourceVideoOrig )[0]
            sourceName = '%s %s' % ( sourceName, res )
         videoItem.append( (sourceVideo+'|Referer='+url, sourceName ) )

      elif 'toolstube' in host:
         sourceVideo = parseToolstube( sourceVideo )
         videoItem.append( (sourceVideo, sourceName ) )

      elif 'youtube' in host:
         print "Skipping youtube video"
         continue
         #sourceVideo = parseYoutube( sourceVideo )
         #for video in sourceVideo:
         #   print "sourceVideo : " + video
         #   hosted_media = urlresolver.HostedMediaFile( url=video, title=sourceName )
         #   if not hosted_media:
         #      print "Skipping video " + sourceName
         #      continue
         #   video = hosted_media.resolve()
         #   videoItem.append( (video, sourceName ) )

      else:
         print "Resolve sourceVideo : " + sourceVideo
         if 'vimeo' in sourceVideo:
            sourceVideo = sourceVideo.replace('https', 'http')
         hosted_media = urlresolver.HostedMediaFile( url=sourceVideo, title=sourceName )
         print "hosted_media", hosted_media
         if not resolvable( hosted_media, sourceVideo ):
            print "Skipping video " + sourceName
            continue
         print "URL works", hosted_media
         video = hosted_media.resolve()
         print "stream url", video
         videoItem.append( (video, sourceName ) )

   if len( videoItem ) == 0:
      addon.show_ok_dialog( [ 'Video does not exist' ], title='Playback' )
   elif len(videoItem) == 1:
      url, title = videoItem[ 0 ]
      print "stream_url ", url

      pDialog = xbmcgui.DialogProgress()
      pDialog.create('Opening stream ' + title)

      playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
      playlist.clear()
      listitem = xbmcgui.ListItem(title)
      playlist.add(url, listitem)
      xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(playlist)
   else:
      partNo = 1
      prevSource = ''
      for sourceVideo, sourceName in videoItem:
         if sourceName != prevSource:
            partNo = 1
            prevSource = sourceName

         title = sourceName
         if partNo > 1:
            title += ' Part# ' + str( partNo )

         addon.add_video_item( { 'url' : sourceVideo }, { 'title' : title } )
         partNo += 1

      xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Main_Categories():
   addon.add_directory( { 'mode' : 'tv' }, { 'title' : '[B]Live TV[/B]' }, 
                        img=getImgPath('Live TV') )
   addon.add_directory( { 'mode' : 'radio' }, { 'title' : '[B]Live Radio[/B]' }, 
                        img=getImgPath('Live Radio') )
   addon.add_directory( { 'mode' : 'vod' }, { 'title' : '[B]On Demand[/B]' }, 
                        img=getImgPath('On Demand') )
   addon.add_directory( { 'mode' : 'movie', 'url' : MOVIE_URL }, { 'title' : '[B]New Movies[/B]' }, 
                        img=getImgPath('Movies') )
   addon.add_directory( { 'mode' : 'movie', 'url' : HD_MOVIE_URL }, { 'title' : '[B]HD Movies[/B]' }, 
                        img=getImgPath('Movies') )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Vod_Main():
   print "main_vod"
   tubeIndex = cache.cacheFunction( parseMainPage )
   print "size = ", len(repr(tubeIndex))
   #print 'TubeIndex:'
   #pprint(tubeIndex, width=1)

   for key, value in sorted( tubeIndex.items() ):
      if key == 'Comedy':
         mode = 'leaf'
         path = value
      elif type( value ) != dict:
         continue
      else:
         mode = 'tree'
         path = key
      addon.add_directory( { 'mode' : mode, 'url' : path }, { 'title' : '[B]%s[/B]' % key },
                           img=getImgPath(key) )

   xbmcplugin.endOfDirectory(int(sys.argv[1]))
                       
def Movie_Main( url ):
   print "main_movie:" + url
   nav, link = parseMoviePage( url )

   for page, (img, title) in link:
      img = img.lstrip()
      img = img.rstrip()
      title =  addon.unescape(title)
      title = unicodedata.normalize('NFKD', unicode(title)).encode('ascii', 'ignore')
      addon.add_directory( { 'mode' : 'load_videos', 'url' : page }, { 'title' : title },
                           img=img, total_items=len(link) )
   if nav:
      addon.add_directory( { 'mode' : 'movie', 'url' : nav[0] }, { 'title' : '[B]Next Page...[/B]' } )

   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Main_Tree( url ):
   print "tree:" + url + ":"
   tubeIndex = cache.cacheFunction( parseMainPage )
   path = url.split( '&' )
   for key in path:
      tubeIndex = tubeIndex[ key ]

   for key, value in sorted( tubeIndex.items() ):
      if type( value ) != dict:
         mode = 'leaf'
         path = value
      else:
         mode = 'tree'
         path = url + '&' + key
      addon.add_directory( { 'mode' : mode, 'url' : path }, { 'title' : '[B]%s[/B]' % key },
                           img=getImgPath( key ) )
      
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Main_Leaf( url ):
   print "leaf:" + url
   response = net.http_GET( url )
   html = response.content
   soup = BeautifulSoup( html )
   div = soup.findAll( 'div', { 'class' : 'video' } )
   for d in div:
      video = d.find( 'div', { 'class' : 'thumb' } )
      url = video.a[ 'href' ]
      title = video.a[ 'title' ]
      img = video.img[ 'src' ]

      addon.add_directory( { 'mode' : 'load_videos', 'url' : url }, { 'title' : title.encode('utf-8')}, 
                           img=img, total_items=len(div) )

   pages = soup.find( 'ul', { 'class' : 'page_navi' } )
   nextPage = pages.find( 'li', { 'class' : 'next' } )
   if nextPage:
      nextPageUrl = nextPage.a[ 'href' ]
      addon.add_directory( { 'mode' : 'leaf', 'url' : nextPageUrl }, { 'title' : '[B]Next Page...[/B]' } )

   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TV_Main():
   print "tv_main"
   tvIndex = parseTvPage()

   for key, value in sorted( tvIndex.items() ):
      if type( value ) != dict:
         continue
      else:
         mode = 'tv_tree'
         path = key
      addon.add_directory( { 'mode' : mode, 'url' : path }, { 'title' : '[B]%s[/B]' % key },
                           img=getImgPath(key) )

   xbmcplugin.endOfDirectory(int(sys.argv[1]))
                       
def Radio_Main():
   print "radio_main"
   radioIndex = parseRadioPage()

   for (name, url, img) in radioIndex:
      url = name + '|' + url
      addon.add_directory( { 'mode' : 'tv_leaf', 'url' : url }, { 'title' : '[B]%s[/B]' % name },
                           img=img, total_items=len(radioIndex) )

   xbmcplugin.endOfDirectory(int(sys.argv[1]))
      
def TV_Tree( url ):
   print "TV_Tree" + url
   tvIndex = parseTvPage()
   path = url.split( '&' )
   for key in path:
      tvIndex = tvIndex[ key ]

   for key, value in sorted( tvIndex.items() ):
      if type( value ) != dict:
         mode = 'tv_leaf'
         (path,img) = value
         path = key + '|' + path
      else:
         mode = 'tv_tree'
         path = url + '&' + key
      addon.add_directory( { 'mode' : mode, 'url' : path }, 
                           { 'title' : '[B]%s[/B]' % key },
                           img=img )
      
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TV_Leaf( url ):
   print "TV_Leaf:" + url
   sep = url.split( '|' )
   title = sep[ 0 ]
   stream_url = sep[ 1 ]
   pDialog = xbmcgui.DialogProgress()
   pDialog.create('Streaming ' + title )

   playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
   playlist.clear()
   listitem = xbmcgui.ListItem( title )
   playlist.add(stream_url, listitem)
   xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(playlist)
       
##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
name = addon.queries.get('name', None)
play = addon.queries.get('play', None)

print "MODE: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "play: "+str(play)
print "arg1: "+sys.argv[1]
print "arg2: "+sys.argv[2]

if play:
   addon.resolve_url(url)
else:
   if mode == 'main':
      Main_Categories()

   elif mode == 'radio':
      Radio_Main()

   elif mode == 'vod':
      Vod_Main()
          
   elif mode == 'movie':
      Movie_Main(url)
          
   elif mode == 'tree':
      Main_Tree( url )

   elif mode == 'leaf':
      Main_Leaf( url )

   elif mode == 'load_videos':
      Load_Video( url )

   elif mode == 'tv':
      TV_Main()

   elif mode == 'tv_tree':
      TV_Tree( url )

   elif mode == 'tv_leaf':
      TV_Leaf( url )


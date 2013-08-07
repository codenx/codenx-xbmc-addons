import urllib, urllib2
import xbmcplugin, xbmcgui
import re, sys, cgi
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
from BeautifulSoup import BeautifulSoup
#from pprint import pprint

BASE_URL = "http://www.tubetamil.com/"
net = Net()
addon = Addon( 'plugin.video.oliyumoliyum', sys.argv )

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

def parseDailymotion( url ):
   link = urllib2.urlparse.urlsplit( url )
   nloc = link.netloc
   path = link.path
   path = path.replace( 'embed/', '' )
   video = [ 'http://' + nloc + path ]
   return video

def parseYoutube( url ):
   videos = []
   link = urllib2.urlparse.urlsplit( url )
   query = link.query
   netloc = link.netloc
   path = link.path

   print "PT url : " + url

   def parseYoutubePlaylist( playlistId ):
      videos = []
      yturl = 'http://gdata.youtube.com/feeds/api/playlists/' + playlistId
      response = net.http_GET( yturl )
      html = response.content
      soup = BeautifulSoup( html )

      for video in soup.findChildren( 'media:player' ):
         videoUrl = str( video[ 'url' ] )
         print "PTL video : " + videoUrl
         videos += parseYoutube( videoUrl )
      print videos
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

def Load_Video( url ):
   print "Load_Video=" + url
   html = net.http_GET( url ).content
   sourceVideos = []

   # Handle embed tags
   sourceVideos += re.compile( '<embed(.+?)>', flags=re.DOTALL).findall( html )

   # Handle iframe tags
   sourceVideos += re.compile( '<iframe(.+?)>').findall( html )

   # Handle Youtube new window
   src = re.compile( 'onclick="window.open\((.+?),' ).findall( html )
   if src:
      sourceVideos += [ 'src=' + src[ 0 ] ]

   if len( sourceVideos ) == 0:
      print "No video sources found!!!!"
      return
      
   videoItem = []
   for sourceVideo in sourceVideos:
      print "sourceVideo=" + sourceVideo
      sourceVideo = re.compile( 'src=(?:\"|\')(.+?)(?:\"|\')' ).findall( sourceVideo )[0]
      sourceVideo = urllib.unquote( sourceVideo )
      print "sourceVideo=" + sourceVideo
      link = urllib2.urlparse.urlsplit( sourceVideo )
      host = link.hostname
      host = host.replace( 'www.', '' )
      host = host.replace( '.com', '' )
      sourceName = host.capitalize()

      if 'dailymotion' in host:
         sourceVideo = parseDailymotion( sourceVideo )

      elif 'youtube' in host:
         sourceVideo = parseYoutube( sourceVideo )

      else:
         sourceVideo = [ sourceVideo ]

      for video in sourceVideo:
         print "sourceName = " + sourceName
         print "sourceVideo : " + video
         hosted_media = urlresolver.HostedMediaFile( url=video, title=sourceName )
         if not hosted_media:
            print "Skipping video " + sourceName
            continue
         videoItem.append( (video, sourceName, hosted_media ) )

   if len( videoItem ) == 0:
      addon.show_ok_dialog( [ 'No video source found!' ], title='Playback' )
   elif len(videoItem) == 1:
      url, title, hosted_media = videoItem[ 0 ]
      stream_url = hosted_media.resolve()
      print "stream_url " + stream_url

      pDialog = xbmcgui.DialogProgress()
      pDialog.create('Opening stream ' + title)

      playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
      playlist.clear()
      listitem = xbmcgui.ListItem(title)
      playlist.add(stream_url, listitem)
      xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(playlist)
   else:
      partNo = 1
      prevSource = ''
      for sourceVideo, sourceName, _ in videoItem:
         if sourceName != prevSource:
            partNo = 1
            prevSource = sourceName

         title = sourceName + ' Part# ' + str( partNo )
         addon.add_video_item( { 'url' : sourceVideo }, { 'title' : title } )
         partNo += 1

      xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Main_Categories():
   response = net.http_GET( BASE_URL )
   html = response.content
   url = response.get_url()
   
   soup = BeautifulSoup( html )
   div = soup.find( 'div', { 'id' : 'mainmenu' } )
   tubeIndex = parseUl( div.ul )
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
      addon.add_directory( { 'mode' : mode, 'url' : path }, { 'title' : '[B]%s[/B]' % key } )

   xbmcplugin.endOfDirectory(int(sys.argv[1]))
                       
def Main_Tree( url ):
   print "tree:" + url
   response = net.http_GET( BASE_URL )
   html = response.content
   soup = BeautifulSoup( html )
   div = soup.find( 'div', { 'id' : 'mainmenu' } )
   li = div.ul.find( 'span', text=url ).parent.parent.parent
   tubeIndex = parseUl( li.ul )

   for key, value in sorted( tubeIndex.items() ):
      if type( value ) != dict:
         mode = 'leaf'
         path = value
      else:
         mode = 'tree'
         path = key
      addon.add_directory( { 'mode' : mode, 'url' : path }, { 'title' : '[B]%s[/B]' % key } )
      
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Main_Leaf( url ):
   print "leaf:" + url
   response = net.http_GET( url )
   html = response.content
   baseUrl = response.get_url()
   print "baseUrl=" + baseUrl

   baseUrl = urllib2.urlparse.urlsplit(baseUrl).netloc
   baseUrl = 'http://' + baseUrl + '/'
   print "baseUrl=" + baseUrl

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
   hosted_media = urlresolver.HostedMediaFile( url=url, title=name )
   print "hosted_media"
   print hosted_media
   if hosted_media:
      stream_url = hosted_media.resolve()
      print stream_url
      addon.resolve_url(stream_url)
   else:
      print "unable to resolve"
else:
   if mode == 'main':
      Main_Categories()
          
   elif mode == 'tree':
      Main_Tree( url )

   elif mode == 'leaf':
      Main_Leaf( url )

   elif mode == 'load_videos':
      Load_Video( url )


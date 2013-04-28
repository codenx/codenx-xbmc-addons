import urllib, urllib2
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, sys
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

BASE_URL = "http://www.dishtamilonline.com/"

net = Net()
addon = Addon( 'plugin.video.oliyumoliyum', sys.argv )

def Load_Video( url ):
   print "Load_Video=" + url
   html = net.http_GET( url ).content
   sources = []

   # Handle youtube gdata links
   if re.search( 'http://gdata.youtube.com', html ):
      print "gdata"
      playListID = re.compile( 'http://gdata.youtube.com/feeds/api/playlists/(.+?)\'' ).findall( html )[0]
      #youTubeGetPlayList( playListID, '', 'Source #1 Youtube', 'Part' )
      return

   # Handle embed tags
   sourceVideos = re.compile( '<embed(.+?)>').findall( html )

   # Handle iframe tags
   sourceVideos = sourceVideos + re.compile( '<iframe(.+?)>').findall( html )

   if len( sourceVideos ) == 0:
      print "No video sources found!!!!"
      return
      
   partNo = 1
   prevSource = ''
   for sourceVideo in sourceVideos:
      print "sourceVideo=" + sourceVideo
      sourceVideo = re.compile( 'src=(?:\"|\')(.+?)(?:\"|\')' ).findall( sourceVideo )[0]
      sourceVideo = urllib.unquote( sourceVideo )
      link = urllib2.urlparse.urlsplit( sourceVideo )
      host = link.hostname
      nloc = link.netloc
      path = link.path

      if 'dailymotion' in host:
         path = path.replace( 'embed/', '' )

      host = host.replace( 'www.', '' )
      host = host.replace( '.com', '' )
      sourceName = host.capitalize()

      if sourceName != prevSource:
         partNo = 1
         prevSource = sourceName

      sourceVideo = 'http://' + nloc + path
      title = sourceName + ' Part# ' + str( partNo )

      print "sourceName = " + sourceName
      print "sourceVideo = " + sourceVideo

      hosted_media = urlresolver.HostedMediaFile( url=sourceVideo, title=sourceName )
      if not hosted_media:
         print "Skipping video " + sourceName
         continue

      addon.add_video_item( { 'url' : sourceVideo }, { 'title' : title } )
      partNo += 1

   if partNo == 1:
      addon.show_ok_dialog( [ 'No video source found!' ], title='Playback' )
   else:
      xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Load_and_Play_Video(url,name):
   ok=True
   print "Load_and_Play_Video:" + url
   videoUrl = Play_Video(url,name,True,False)
   if videoUrl == None:
     d = xbmcgui.Dialog()
     d.ok('NO VIDEO FOUND', 'This video was removed due to copyright issue.','Check other links.')
     return False
   xbmcPlayer = xbmc.Player()
   xbmcPlayer.play(videoUrl)
   return ok

def Load_and_Play_Video_Links(url,name):
   #xbmc.executebuiltin("XBMC.Notification(PLease Wait!,Loading video links into XBMC Media Player,5000)")
   print "mode 3"
   ok=True
   playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
   playList.clear()
   #time.sleep(2)
   links = url.split(':;')
   print links

   pDialog = xbmcgui.DialogProgress()
   ret = pDialog.create('Loading playlist...')
   totalLinks = len(links)
   loadedLinks = 0
   remaining_display = 'Videos loaded :: [B]'+str(loadedLinks)+' / '+str(totalLinks)+'[/B] into XBMC player playlist.'
   pDialog.update(0,'Please wait for the process to retrieve video link.',remaining_display)

   for videoLink in links:
       print "loading " + videoLink
       Play_Video(videoLink,name,True,True)

       loadedLinks = loadedLinks + 1
       percent = (loadedLinks * 100)/totalLinks
       #print percent
       remaining_display = 'Videos loaded :: [B]'+str(loadedLinks)+' / '+str(totalLinks)+'[/B] into XBMC player playlist.'
       pDialog.update(percent,'Please wait for the process to retrieve video link.',remaining_display)
       if (pDialog.iscanceled()):
          return False
   xbmcPlayer = xbmc.Player()
   xbmcPlayer.play(playList)
   if not xbmcPlayer.isPlayingVideo():
       d = xbmcgui.Dialog()
       d.ok('INVALID VIDEO PLAYLIST', 'The playlist videos were removed due to copyright issue.','Check other links.')
   return ok

def Main_Categories():
   response = net.http_GET( BASE_URL )
   html = response.content
   url = response.get_url()
   
   path = re.compile('<a href="(.+)"><b>Movies</b>').findall(html)[ 0 ]
   if 'www' not in path:
      path = url + path
   print "Movies=" + path
   addon.add_directory( { 'mode' : 'movies', 'url' : path }, { 'title' : '[B]Movies[/B]' } )

   path = re.compile('<a href="(.+)"><b>TV Shows</b>').findall(html)[ 0 ]
   if 'www' not in path:
      path = url + path
   print "Tv Shows=" + path
   addon.add_directory( { 'mode' : 'tv', 'url' : path }, { 'title' : '[B]TV Shows[/B]' } )

   path = re.compile('<a href="(.+)"><b>TV Serials</b>').findall(html)[ 0 ]
   if 'www' not in path:
      path = url + path
   print "Tv Serials=" + path
   addon.add_directory( { 'mode' : 'tv', 'url' : path }, { 'title' : '[B]TV Serials[/B]' } )

   path = re.compile('<a href="(.+)"><b>Comedy</b>').findall(html)[ 0 ]
   if 'www' not in path:
      path = url + path
   print "Comedy=" + path
   addon.add_directory( { 'mode' : 'comedy', 'url' : path }, { 'title' : '[B]Comedy[/B]' } )

   path = re.compile('<a href="(.+)"><b>Video Songs</b>').findall(html)[ 0 ]
   if 'www' not in path:
      path = url + path
   print "Video Songs=" + path
   addon.add_directory( { 'mode' : 'songs', 'url' : path }, { 'title' : '[B]Video Songs[/B]' } )

   path = re.compile('<a href="(.+)"><b>Wallpaper</b>').findall(html)[ 0 ]
   if 'www' not in path:
      path = url + path
   print "Wallpaper=" + path
   addon.add_directory( { 'mode' : 'wallpaper', 'url' : path }, { 'title' : '[B]Wallpaper[/B]' } )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))
                       
def Movie_Categories( url ):
   print "Movie url = " + url
   response = net.http_GET( url )
   html = response.content
   baseUrl = response.get_url()
   print "baseUrl=" + baseUrl

   baseUrl = urllib2.urlparse.urlsplit(baseUrl).netloc
   baseUrl = 'http://' + baseUrl + '/'
   print "baseUrl=" + baseUrl

   path = re.compile('<a href="(.+)">New Movies</a>').findall(html)[ 0 ]
   if 'www' not in path:
      path = baseUrl + path
   addon.add_directory( { 'mode' : 'movies_sort', 'url' : path }, 
                        { 'title' : ' [B]New Movies[/B]' } )

   path = re.compile('<a href="(.+)">DvD Movies</a>').findall(html)[ 0 ]
   if 'www' not in path:
      path = baseUrl + path
   addon.add_directory( { 'mode' : 'movies_sort', 'url' : path }, 
                        { 'title' : ' [B]DVD Movies[/B]' } )

   path = re.compile('<a href="(.+)">Classic Movies</a>').findall(html)[ 0 ]
   if 'www' not in path:
      path = baseUrl + path
   addon.add_directory( { 'mode' : 'movies_sort', 'url' : path }, 
                        { 'title' : ' [B]Classic Movies[/B]' } )

   path = re.compile('<a href="(.+)">Mid Movies</a>').findall(html)[ 0 ]
   if 'www' not in path:
      path = baseUrl + path
   addon.add_directory( { 'mode' : 'movies_sort', 'url' : path }, 
                        { 'title' : ' [B]Mid Movies[/B]',  } )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Movie_Sort_Order( url ):
   print "Movie sort url = " + url
   url = url.replace( "&alp=all", "" )
   print "Sort Order:" + url

   addon.add_directory( { 'mode' : 'movies_list', 'url' : url + '&sort=date&page=1' },
                        { 'title' : ' [B]Recently Added[/B]',  } )
   addon.add_directory( { 'mode' : 'movies_list', 'url' : url + '&sort=views&page=1' },
                        { 'title' : ' [B]Most Viewed[/B]',  } )
   addon.add_directory( { 'mode' : 'movies_az', 'url' : url },
                        { 'title' : ' [B]Sort Alphabetically[/B]',  } )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Movie_List( url ):
   print "Movie list url = " + url
   response = net.http_GET( url )
   html = response.content
   baseUrl = response.get_url()
   print "baseUrl=" + baseUrl

   baseUrl = urllib2.urlparse.urlsplit(baseUrl).netloc
   baseUrl = 'http://' + baseUrl + '/'
   print "baseUrl=" + baseUrl

   # Find the #pages in the current category
   pages=re.compile( '<span class="page"> <a href=".+">(\d{1,2})<' ).findall( html )

   # Find the movies in the current category
   match=re.compile('<img src="(.+)" alt=".*" width=".*" height=".*" style=".*" title=".*" onMouseOver=".+"\nonmouseout=".*"></a><br />\n\s+<a href="(.+)">(.+)</a><br />').findall(html)
   total_items = len( match ) + len( pages ) * len( match )
   for thumbnail, movieUrl, name in match:
      addon.add_directory( { 'mode' : 'movies_videos', 'url' : baseUrl + "/" + movieUrl },
                           { 'title' : name },
                           img=baseUrl + thumbnail, total_items=total_items )

   url = url.replace( "&page=1", "&page=" )
   print "List url:" + url, "#pages=" + str( len( pages ) )
   # Scrape pages 1-->5, there's about 50 movies in 5 pages
   for page in pages:
      rurl = url + page
      print "Access URL=" + rurl
      html = net.http_GET( rurl ).content
      match=re.compile('<img src="(.+)" alt=".*" width=".*" height=".*" style=".*" title=".*" onMouseOver=".+"\nonmouseout=".*"></a><br />\n\s+<a href="(.+)">(.+)</a><br />').findall(html)
      for thumbnail, movieUrl, name in match:
         addon.add_directory( { 'mode' : 'movies_videos', 'url' : baseUrl + "/" + movieUrl },
                              { 'title' : name },
                              img=baseUrl + thumbnail )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Movie_A_Z( url ):
   print "A-Z Viewed:" + url
   sortPages = []
   sortPages.append('#')
   for c in range( ord('A'), ord('Z')+1 ):
      sortPages.append( chr(c) )
   sortPages.append('all')
   print "pages:" 
   print sortPages

   # Scrape pages 1-->5, there's about 50 movies in 5 pages
   for page in sortPages:
      rurl = url + '&alp=' + page + '&page=1'
      Add_Dir( page, rurl, 12, '' )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Movies_Video_Link( url ):
   print "Video Link=" + url
   response = net.http_GET( url )
   html = response.content
   baseUrl = response.get_url()
   print "baseUrl=" + baseUrl

   baseUrl = urllib2.urlparse.urlsplit(baseUrl).netloc
   baseUrl = 'http://' + baseUrl + '/'
   print "baseUrl=" + baseUrl

   match=re.compile('<img src=".*" alt=".*" /> <a href="(.*)">Full Movie.*</a> <br />').findall(html)
   print match
   videoUrl = baseUrl + match[0]
   print "Video URL=" + videoUrl

   Load_Video( videoUrl )

def TV_Show_Sort_Order( url ):
   print "TV url = " + url
   url = url.replace( "&alp=all", "" )
   print "Sort Order:" + url

   addon.add_directory( { 'mode' : 'tv_list', 'url' : url + '&sort=date&page=1' },
                        { 'title' : ' [B]Recently Added[/B]',  } )
   addon.add_directory( { 'mode' : 'tv_list', 'url' : url + '&sort=views&page=1' },
                        { 'title' : ' [B]Most Viewed[/B]',  } )
   addon.add_directory( { 'mode' : 'tv_az', 'url' : url },
                        { 'title' : ' [B]Sort Alphabetically[/B]',  } )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TV_Show_List( url ):
   print "TV list url = " + url
   response = net.http_GET( url )
   html = response.content
   baseUrl = response.get_url()
   print "baseUrl=" + baseUrl

   baseUrl = urllib2.urlparse.urlsplit(baseUrl).netloc
   baseUrl = 'http://' + baseUrl + '/'
   print "baseUrl=" + baseUrl

   # Find the #pages in the current category
   pages=re.compile( '<span class="page"> <a href=".+">(\d{1,2})<' ).findall( html )

   # Find the movies in the current category
   match=re.compile('<a href="(.+)">(.+)</a> <br />\n\s+<a href=".+"><img src="(.+)" width').findall( html )
   total_items = len( match ) + len( pages ) * len( match )
   for tvUrl, name, thumbnail in match:
      addon.add_directory( { 'mode' : 'tv_videos', 'url' : baseUrl + "/" + tvUrl },
                           { 'title' : name },
                           img=baseUrl + thumbnail, total_items=total_items )

   url = url.replace( "&page=1", "&page=" )
   print "List url:" + url, "#pages=" + str( len( pages ) )
   # Scrape pages 1-->5, there's about 50 movies in 5 pages
   for page in pages:
      rurl = url + page
      print "Access URL=" + rurl
      html = net.http_GET( rurl ).content

      match=re.compile('<a href="(.+)">(.+)</a> <br />\n\s+<a href=".+"><img src="(.+)" width').findall( html )
      for tvUrl, name, thumbnail in match:
         addon.add_directory( { 'mode' : 'tv_videos', 'url' : baseUrl + "/" + tvUrl },
                              { 'title' : name },
                              img=baseUrl + thumbnail, total_items=total_items )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TV_Show_A_Z( url ):
   print "A-Z Viewed:" + url
   sortPages = []
   sortPages.append('0')
   for c in range( ord('A'), ord('Z')+1 ):
      sortPages.append( chr(c) )
   sortPages.append('all')
   print "pages:"
   print sortPages

   # Scrape pages 1-->5, there's about 50 movies in 5 pages
   for page in sortPages:
      rurl = url + '&alp=' + page + '&page=1'
      Add_Dir( page, rurl, 22, '' )
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def TV_Show_Episode_List( url ):
   print "Tv Episode url = " + url
   response = net.http_GET( url )
   html = response.content
   baseUrl = response.get_url()
   print "baseUrl=" + baseUrl

   baseUrl = urllib2.urlparse.urlsplit(baseUrl).netloc
   baseUrl = 'http://' + baseUrl + '/'
   print "baseUrl=" + baseUrl

   match=re.compile('<img src=".+" alt=".+" /> <a href="(.+)">(.+)</a> <br />').findall( html )
   for tvUrl, title in match:
      addon.add_directory( { 'mode' : 'load_videos', 'url' : baseUrl + "/" + tvUrl },
                           { 'title' : title } )
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
          
   elif mode == 'movies':
      Movie_Categories( url )

   elif mode == 'movies_sort':
      Movie_Sort_Order( url )

   elif mode == 'movies_list':
      Movie_List( url )

   elif mode == 'movies_az':
      Movie_A_Z( url )

   elif mode == 'movies_videos':
      Movies_Video_Link( url )

   elif mode == 'tv':
      TV_Show_Sort_Order( url )

   elif mode == 'tv_list':
      TV_Show_List( url )

   elif mode == 'tv_videos':
      TV_Show_Episode_List( url )

   elif mode == 'load_videos':
      Load_Video( url )

   elif mode == 2:
      Load_and_Play_Video( url, name )

   elif mode == 3:
      Load_and_Play_Video_Links( url, name )

   elif mode == 23:
      TV_Show_A_Z( url )


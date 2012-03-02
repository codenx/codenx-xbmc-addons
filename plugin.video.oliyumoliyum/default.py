import urllib,urllib2,re,sys,xbmcplugin,xbmcgui
import cookielib,os,string,cookielib,StringIO
import os,time,base64,logging,calendar
import xbmcaddon
from xml.dom.minidom import parse, parseString
from datetime import datetime
try:
    import json
except ImportError:
    import simplejson as json

def unescape(url):
      htmlCodes = [ 
            ['&', '&amp;'],
            ['<', '&lt;'],
            ['>', '&gt;'],
            ['"', '&quot;'],
        ]
      for code in htmlCodes:
           url = url.replace(code[1], code[0]) 
      return url

def get_params():
   param=[]
   paramstring=sys.argv[2]
   if len(paramstring)>=2:
      params=sys.argv[2]
      cleanedparams=params.replace('?','')
      if (params[len(params)-1]=='/'):
         params=params[0:len(params)-2]
      pairsofparams=cleanedparams.split('&')
      param={}
      for i in range(len(pairsofparams)):
         splitparams={}
         splitparams=pairsofparams[i].split('=')
         if (len(splitparams))==2:
            param[splitparams[0]]=splitparams[1]
                               
      return param

def Add_Link( name, url, iconimage):
   print "Add_Link url=" + url
   ok=True
   liz=xbmcgui.ListItem( name, iconImage="DefaultVideo.png", thumbnailImage=iconimage )
   liz.setInfo( type="Video", infoLabels={ "Title": name } )
   ok=xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=url, listitem=liz )
   return ok


def Add_Dir( name, url, mode, iconimage ):
   print "Add_Dir url=" + url
   u = sys.argv[0] + "?url=" + urllib.quote_plus( url )+ "&mode=" + str( mode ) + "&name=" + urllib.quote_plus( name )
   ok=True
   liz=xbmcgui.ListItem( name, iconImage="DefaultFolder.png", thumbnailImage=iconimage )
   liz.setInfo( type="Video", infoLabels={ "Title": name } )
   ok=xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True )
   return ok

def Add_Playable_Movie_Link(name,url,mode,iconimage):
   print "Add_Playable_Movie_Link url=" + url
   u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
   ok=True
   liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
   liz.setInfo( type="Video", infoLabels={ "Title": name } )
   # adding context menus
   ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
   return ok


def Add_Play_List_Link(name,url,mode,iconimage):
   print "Add_Play_List_Link url=" + url
   u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
   ok=True
   liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
   liz.setInfo( type="Video", infoLabels={ "Title": name } )
   ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
   return ok

#YOUTUBE        
def youTubeGetText(nodelist):
   rc = []
   for node in nodelist:
      if node.nodeType == node.TEXT_NODE:
         rc.append(node.data)
   return ''.join(rc)

def youTubeGetVideoTitle(video):
   return youTubeGetText(video.getElementsByTagName("title")[0].childNodes)

def youTubeGetVideoID(video):
   return youTubeGetText(video.getElementsByTagName("yt:videoid")[0].childNodes)

def youTubeGetPlayList(playlistID, imgUrl, sourceName, videoType='Part'):
   print "ut test1"
   url='http://gdata.youtube.com/feeds/api/playlists/'+playlistID+'?v=2'
   print "YT_PlayList url=" + url
   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()
   domObj = parseString(link)
   print "XML:\n", domObj.toprettyxml()
   videos=domObj.getElementsByTagName("entry")
   i = 1
   playList = ''
   matchCount = len(videos)
   if(matchCount == 1):
      videoLink = 'http://www.youtube.com/v/'+youTubeGetVideoID(videos[0])
      Add_Playable_Movie_Link('[B]SINGLE LINK [/B]'+sourceName,videoLink,2,imgUrl)
   elif(matchCount > 1):
      for video in videos:
          #print "video=" + video
          videoID = youTubeGetVideoID(video)
          videoTitle = youTubeGetVideoTitle(video)
          print '\tvideoID = '+videoID
          videoLink = 'http://www.youtube.com/v/'+videoID
          if videoType == 'Song':
             Add_Playable_Movie_Link(sourceName +' - '+videoTitle,videoLink,2,imgUrl)
          else:
             Add_Playable_Movie_Link(sourceName +' - '+videoType+': '+str(i),videoLink,2,imgUrl)
          playList = playList + videoLink
          if(i < matchCount):
                  playList = playList + ':;'
          i = i + 1
      if(i > matchCount and matchCount > 0):
          Add_Play_List_Link('[B]Direct PLAY - ' + sourceName + '[/B] [I]Playlist of above ' + str(matchCount) + ' videos[/I]',playList, 3, imgUrl)

# Scrape a video link for info and load the video into XBMC player
def Play_Video(url,name,isRequestForURL,isRequestForPlaylist):
   url = url + '&TTV;'
   print 'Play_Video VIDEO URL = '+ url

   #YOUTUBE
   try:
       match=re.compile('http://www.youtube.com/v/(.+?)&').findall(url)
       code = match[0]
       print "code=" + code

       linkImage = 'http://i.ytimg.com/vi/'+code+'/default.jpg'
       req = urllib2.Request('http://www.youtube.com/watch?v='+code+'&fmt=18')
       req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
       response = urllib2.urlopen(req)
       link=response.read()
       response.close()

       if len(re.compile('shortlink" href="http://youtu.be/(.+?)"').findall(link)) == 0:
            if len(re.compile('\'VIDEO_ID\': "(.+?)"').findall(link)) == 0:
                 req = urllib2.Request('http://www.youtube.com/get_video_info?video_id='+code+'&asv=3&el=detailpage&hl=en_US')
                 req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                 response = urllib2.urlopen(req)
                 link=response.read()
                 response.close()
       map = None
       link = link.replace('\\u0026', '&')
       match=re.compile('url_encoded_fmt_stream_map=(.+?)&').findall(link)
       if len(match) == 0:
            map=(re.compile('url_encoded_fmt_stream_map": "(.+?)"').findall(link)[0]).replace('\\/', '/').split('url=')
       else:
            map=urllib.unquote(match[0]).decode('utf8').split('url=')
       if re.search('status=fail', link):
            return
       if map == None:
            return
       print "map:"
       print map

       highResoVid = ''
       youtubeVideoQual = 1 #fbn.getSetting('videoQual')
       for attr in map:
               if attr == '':
                       continue
               parts = attr.split('&quality')
               url = urllib.unquote(parts[0]).decode('utf8')
               qual = re.compile('&itag=(\d*)').findall(url)[0]
               print "qual=" , qual
               if(qual == '13'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY 3GP Low Quality - 176x144',url,linkImage)
                       elif(highResoVid == ''):
                               highResoVid = url
               if(qual == '17'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY 3GP Medium Quality - 176x144',url,linkImage)
                       elif(highResoVid == ''):
                               highResoVid = url
               if(qual == '36'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY 3GP High Quality - 320x240',url,linkImage)
                       elif(highResoVid == ''):
                               highResoVid = url
               if(qual == '5'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY FLV Low Quality - 400\\327226',url,linkImage)
                       elif(highResoVid == ''):
                               highResoVid = url
               if(qual == '34'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY FLV Medium Quality - 480x360',url,linkImage)
                       elif(highResoVid == ''):
                               highResoVid = url
               if(qual == '6'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY FLV Medium Quality - 640\\327360',url,linkImage)
                       elif(highResoVid == ''):
                               highResoVid = url
               if(qual == '35'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY FLV High Quality - 854\\327480',url,linkImage)
                       else:
                               highResoVid = url
               if(qual == '18'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY MP4 High Quality - 480x360',url,linkImage)
                       else:
                               highResoVid = url
                               
               if(qual == '22'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY MP4 High Quality - 1280x720',url,linkImage)
                       else:
                               highResoVid = url
                               if youtubeVideoQual == '1' or youtubeVideoQual == '2':
                                       break
               if(qual == '37'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY MP4 High-2 Quality - 1920x1080',url,linkImage)
                       else:
                               highResoVid = url
                               if youtubeVideoQual == '2':
                                       break
               if(qual == '38'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY MP4 Epic Quality - 4096\\3272304',url,linkImage)
                       else:
                               highResoVid = url
                               if youtubeVideoQual == '2':
                                       break
               if(qual == '43'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY WEBM Medium Quality - 4096\\3272304',url,linkImage)
                       else:
                               highResoVid = url
               if(qual == '44'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY WEBM High Quality - 4096\\3272304',url,linkImage)
                       else:
                               highResoVid = url
                               if youtubeVideoQual == '1' or youtubeVideoQual == '2':
                                       break
               if(qual == '45'):
                       if(not(isRequestForURL)):
                               addLink ('PLAY WEBM High-2 Quality - 4096\\3272304',url,linkImage)
                       else:
                               highResoVid = url
                               if youtubeVideoQual == '2':
                                       break
       print highResoVid

       if(isRequestForURL):
          if(isRequestForPlaylist):
            liz = xbmcgui.ListItem('VIDEO PART', thumbnailImage=linkImage)
            xbmc.PlayList(xbmc.PLAYLIST_VIDEO).add(url = highResoVid, listitem=liz)
            return highResoVid
          else:
            return highResoVid

   except: pass

   #DAILYMOTION
   try:
     match=re.compile('http://www.dailymotion.com/(.+?)&').findall(url)
     if len(match) == 0:
         match = re.compile( 'http://www.dailymotion.com/embed/video/(.+?)').findall( url )
         print "embed match:"
         print match
     elif(len(match) > 0):
         newUrl = url.replace('?','&')
         match=re.compile('video/(.+?)&').findall(newUrl)
         if len(match) == 0:
              match=re.compile('swf/(.+?)&').findall(newUrl)
              print match
     link = 'http://www.dailymotion.com/video/'+str(match[0])
     print link
     req = urllib2.Request(link)
     req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
     response = urllib2.urlopen(req)
     link=response.read()
     response.close()
     sequence=re.compile('"sequence",  "(.+?)"').findall(link)
     newseqeunce = urllib.unquote(sequence[0]).decode('utf8').replace('\\/','/')
     imgSrc=re.compile('og:image" content="(.+?)"').findall(link)
     if(len(imgSrc) == 0):
         imgSrc=re.compile('/jpeg" href="(.+?)"').findall(link)
     dm_low=re.compile('"sdURL":"(.+?)"').findall(newseqeunce)
     dm_high=re.compile('"hqURL":"(.+?)"').findall(newseqeunce)
     if(isRequestForURL):
         videoUrl = ''
         if(len(dm_high) == 0):
            videoUrl = dm_low[0]
         else:
            videoUrl = dm_high[0]
         if(isRequestForPlaylist):
            liz = xbmcgui.ListItem('EPISODE', thumbnailImage=imgSrc[0])
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.add(url=videoUrl, listitem=liz)
            return videoUrl
         else:
            return videoUrl

     else:
         if(len(dm_low) > 0):
            Add_Link ('PLAY Standard Quality ',dm_low[0],imgSrc[0])
         if(len(dm_high) > 0):
            Add_Link ('PLAY High Quality ',dm_high[0],imgSrc[0])
   except: pass


   #VIMEO
   try:
      if not re.search('vimeo.com', url):
         raise
      id=re.compile('clip_id=(.+?)&').findall(url)
      videoID = str(id[0])
      link = 'http://www.vimeo.com/moogaloop/load/clip:'+videoID
      req = urllib2.Request(link)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      domObj = parseString(link)
      rs = vimeo_getReqSignature(domObj)
      rse = vimeo_getReqSignatureExpires(domObj)
      qual = vimeo_getQuality(domObj)
      videoUrl = vimeo_getVideoUrl(videoID, rs, rse, qual)
   
      print videoUrl
      imgUrl = vimeo_getVidThumb(domObj)
      print imgUrl
   
      if(isRequestForURL):
         if(isRequestForPlaylist):
            liz = xbmcgui.ListItem('EPISODE', thumbnailImage=imgUrl)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.add(url=videoUrl, listitem=liz)
            return videoUrl
         else:
            return videoUrl

      else:
            Add_Link ('[B]PLAY VIDEO[/B]: '+name,videoUrl,imgUrl)
   except: pass

  #HOSTING CUP
   try:
      id=re.compile('http://www.hostingcup.com/(.+?)&TTV;').findall(url)[0]
      hostingUrl = 'http://www.hostingcup.com/'+id
      req = urllib2.Request(hostingUrl)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      webLink = ''.join(link.splitlines()).replace('\t','')
      #Trying to find out easy way out :)
      paramSet = re.compile("return p\}\(\'(.+?)\',36,(.+?),\'(.+?)\'").findall(webLink)

      result = parseValue(paramSet[0][0],36,int(paramSet[0][1]),paramSet[0][2].split('|'))
      result = result.replace('\\','').replace('"','\'')
      print result

      imgUrl = re.compile("s1.addVariable\(\'image\',\'(.+?)\'\);").findall(result)[0]
      videoUrl = re.compile("s1.addVariable\(\'file\',\'(.+?)\'\);").findall(result)[0]

      print 'HOSTING CUP url = '
      print videoUrl
      if(isRequestForURL):
         if(isRequestForPlaylist):
            liz = xbmcgui.ListItem(name, thumbnailImage=imgUrl)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.add(url=videoUrl, listitem=liz)
            return videoUrl
         else:
            return videoUrl
      else:
            Add_Link ('[B]PLAY VIDEO[/B]: '+name,videoUrl,imgUrl)
   except: pass

   #HOSTING BULK
   try:
      id=re.compile('http://hostingbulk.com/(.+?)&TTV;').findall(url)[0]
      if re.search('embed', id):
         id = re.compile('embed\-(.+?)\-').findall(id)[0] + '.html'
      hostingUrl = 'http://hostingbulk.com/'+id
      req = urllib2.Request(hostingUrl)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      webLink = ''.join(link.splitlines()).replace('\t','')
      #Trying to find out easy way out :)
      paramSet = re.compile("return p\}\(\'(.+?)\',36,(.+?),\'(.+?)\'").findall(webLink)
   
      result = parseValue(paramSet[0][0],36,int(paramSet[0][1]),paramSet[0][2].split('|'))
      result = result.replace('\\','').replace('"','\'')
      print result
   
      imgUrl = re.compile("s1.addVariable\(\'image\',\'(.+?)\'\);").findall(result)[0]
      videoUrl = re.compile("s1.addVariable\(\'file\',\'(.+?)\'\);").findall(result)[0]
   
      print 'HOSTING BULK url = '
      print videoUrl
      if(isRequestForURL):
         if(isRequestForPlaylist):
            liz = xbmcgui.ListItem(name, thumbnailImage=imgUrl)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.add(url=videoUrl, listitem=liz)
            return videoUrl
         else:
            return videoUrl
      else:
          Add_Link ('[B]PLAY VIDEO[/B]: '+name,videoUrl,imgUrl)
   except: pass

   #NOVAMOV
   try:
      p=re.compile('http://www.novamov.com/video/(.+?)&TTV;')
      match=p.findall(url)
      link = 'http://www.novamov.com/video/'+ match[0]
      req = urllib2.Request(link)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      link = ''.join(link.splitlines()).replace('\'','"')
      match=re.compile('flashvars.file="(.+?)";').findall(link)
      imgUrl = ''
      videoUrl=match[0]
      videoTitle = name
      if(isRequestForURL):
         if(isRequestForPlaylist):
            liz = xbmcgui.ListItem(videoTitle, thumbnailImage=imgUrl)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.add(url=videoUrl, listitem=liz)
            return videoUrl
         else:
            return videoUrl
      else:
            Add_Link ('[B]PLAY VIDEO[/B]: '+videoTitle,videoUrl,imgUrl)
   except: pass


   #MOVSHARE
   try:
      match=re.compile('http://www.movshare.net/video/(.+?)&TTV;').findall(url)
      if(len(match) == 0):
            match=re.compile('http://www.movshare.net/embed/(.+?)/').findall(url)
      movUrl = 'http://www.movshare.net/video/'+match[0]
      req = urllib2.Request(movUrl)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      link = ''.join(link.splitlines()).replace('\t','').replace('\'','"')
      if re.search('Video hosting is expensive. We need you to prove you"re human.',link):
         values = {'wm': '1'}
         headers = { 'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3' }
         data = urllib.urlencode(values)
         req = urllib2.Request(movUrl, data, headers)
         response = urllib2.urlopen(req)
         link=response.read()
         response.close()
         link = ''.join(link.splitlines()).replace('\t','').replace('\'','"')

      match=re.compile('<param name="src" value="(.+?)" />').findall(link)
      if(len(match) == 0):
         match=re.compile('flashvars.file="(.+?)"').findall(link)
      imgUrl = ''
      videoUrl=match[0]
      videoTitle = name
      if(isRequestForURL):
         if(isRequestForPlaylist):
            liz = xbmcgui.ListItem(videoTitle, thumbnailImage=imgUrl)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.add(url=videoUrl, listitem=liz)
            return videoUrl
         else:
            return videoUrl
      else:
            Add_Link ('[B]PLAY VIDEO[/B]: '+videoTitle,videoUrl,imgUrl)
   except: pass

   #MEGAVIDEO
   try:
      if not re.search('megavideo.com', url):
         raise
      id=re.compile('http://www.megavideo.com/v/(.+?)&').findall(url)
      if len(id) > 0:
         url = get_redirected_url('http://www.megavideo.com/v/'+id[0], None) + '&TTV;'
      id=re.compile('v=(.+?)&').findall(url)
      video_id = id[0]
      req = urllib2.Request('http://www.megavideo.com/xml/videolink.php?v=' + video_id)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      link = ''.join(link.splitlines()).replace('\t','').replace('\'','"')
   
      un=re.compile(' un="(.+?)"').findall(link)
      k1=re.compile(' k1="(.+?)"').findall(link)
      k2=re.compile(' k2="(.+?)"').findall(link)
      hashresult = decrypt(un[0], k1[0], k2[0])
   
      s=re.compile(' s="(.+?)"').findall(link)
   
      title=re.compile(' title="(.+?)"').findall(link)
      videoTitle = urllib.unquote_plus(title[0].replace('+',' ').replace('.',' '))
   
      imgUrl = ''
      videoUrl = "http://www" + s[0] + ".megavideo.com/files/" + hashresult + "/" + videoTitle.replace('www.apnajoy.com', '') +".flv";
      print 'MEGA VIDEO url = '
      print videoUrl
      if(isRequestForURL):
         if(isRequestForPlaylist):
             liz = xbmcgui.ListItem(videoTitle, thumbnailImage=imgUrl)
             playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
             playlist.add(url=videoUrl, listitem=liz)
             return videoUrl
         else:
             return videoUrl
      else:
            Add_Link ('[B]PLAY VIDEO[/B]: '+videoTitle,videoUrl,imgUrl)
   except: pass


   #VIDEOBB
   try:
      p=re.compile('videobb.com/e/(.+?)&TTV;')
      match=p.findall(url)
      url='http://www.videobb.com/player_control/settings.php?v='+match[0]
      print 
      settingsObj = json.load(urllib.urlopen(url))['settings']
   
      imgUrl = str(settingsObj['config']['thumbnail'])
      videoUrl = str(base64.b64decode(settingsObj['config']['token1']))
      videoTitle = name
      if(isRequestForURL):
         if(isRequestForPlaylist):
             liz = xbmcgui.ListItem(videoTitle, thumbnailImage=imgUrl)
             playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
             playlist.add(url=videoUrl, listitem=liz)
             return videoUrl
         else:
             return videoUrl
      else:
         Add_Link ('[B]PLAY VIDEO[/B]: '+videoTitle,videoUrl,imgUrl)
   except: pass


   #VEOH
   try:
      if not re.search('veoh.com', url):
         raise
      id=re.compile('permalinkId=v(.+?)&').findall(url)
      if len(id) == 0:
         id=re.compile('http://www.veoh.com/v(.+?)&').findall(url)

      url='http://www.veoh.com/rest/v2/execute.xml?method=veoh.video.findByPermalink&permalink=v'+id[0]+'&apiKey=E97FCECD-875D-D5EB-035C-8EF241F184E2'
      req = urllib2.Request(url)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      domObj = parseString(link)
      #print domObj.toprettyxml()
      if len(domObj.getElementsByTagName("error")) > 0:
         print domObj.getElementsByTagName("error")[0].getAttribute('errorMessage')
         return
      videoUrl = get_redirected_url(domObj.getElementsByTagName("video")[0].getAttribute('ipodUrl'), None)
      imgUrl = domObj.getElementsByTagName("video")[0].getAttribute('fullHighResImagePath')
      videoTitle = name
      if(isRequestForURL):
         if(isRequestForPlaylist):
             liz = xbmcgui.ListItem(videoTitle, thumbnailImage=imgUrl)
             playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
             playlist.add(url=videoUrl, listitem=liz)
             return videoUrl
         else:
             return videoUrl
      else:
         Add_Link ('[B]PLAY VIDEO[/B]: '+videoTitle,videoUrl,imgUrl)
   except: pass

def Load_Video( url ):
   req = urllib2.Request( url )
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen( req )
   link=response.read()
   response.close()

   # Handle youtube gdata links
   if re.search( 'http://gdata.youtube.com', link ):
      print "gdata"
      playListID = re.compile( 'http://gdata.youtube.com/feeds/api/playlists/(.+?)\'' ).findall( link )[0]
      youTubeGetPlayList( playListID, '', 'Source #1 Youtube', 'Part' )
      return

   # Handle embed tags
   sourceVideos = re.compile( '<embed(.+?)>').findall( link )

   # Handle iframe tags
   sourceVideos = sourceVideos + re.compile( '<iframe(.+?)>').findall( link )

   if len( sourceVideos ) == 0:
      print "No video sources found!!!!"
      return
      
   srcNbr = 1
   partNbr = 1
   playList = ''
   nPlayList = 0
   for sourceVideo in sourceVideos:
      print "sourceVideo=" + sourceVideo + ":"
      if re.search( 'http://www.youtube.com/p/', sourceVideo ):
         print "found youtube playlist"
         playListID = re.compile( 'http://www.youtube.com/p/(.+?)[&,\?]').findall( sourceVideo )[0]
         youTubeGetPlayList( playListID, '', 'Source #' + str( srcNbr ) + ' Youtube', 'Part' )
         srcNbr = srcNbr + 1
      elif re.search( 'http://www.youtube.com/v/', sourceVideo ):
         print "found youtube video"
         videoID = re.compile( 'http://www.youtube.com/v/(.+?)\?' ).findall( sourceVideo )[0]
         videoLink = 'http://www.youtube.com/v/' + videoID
         Add_Playable_Movie_Link('Source #' + str( srcNbr ) + ' Youtube - Part' + str( partNbr ), videoLink, 2, '')
         playList = playList + videoLink + ':;'
         nPlayList = nPlayList + 1
         partNbr = partNbr + 1
      elif re.search( 'http://www.youtube.com/embed/', sourceVideo ):
         print "found embeded youtube video"
         videoID = re.compile( 'http://www.youtube.com/embed/(.+?)[\?\"]' ).findall( sourceVideo )[0]
         videoLink = 'http://www.youtube.com/v/' + videoID
         Add_Playable_Movie_Link('Source #' + str( srcNbr ) + ' Youtube - Part' + str( partNbr ), videoLink, 2, '')
         playList = playList + videoLink + ':;'
         nPlayList = nPlayList + 1
         partNbr = partNbr + 1
      else:
         print "all other videos"
         # All other video sources
         sourceName = ''
         sourceVideo = re.compile(' src=(.+?) ').findall( ' ' + sourceVideo + ' ' )[0].replace( '\'', '').replace( '"','')
         try:
            if re.search( 'http://www', sourceVideo ):
               sourceName = re.compile( 'www\.(.+?)\.com' ).findall( sourceVideo)[0]
            else:
               sourceName = re.compile( 'http://(.+?)\.com' ).findall( sourceVideo)[0]
         except:
            pass
         if sourceName == '':
            print "Skipping source: " + sourceVideo
            continue
         srouceName = sourceName.capitalize()
         Add_Playable_Movie_Link('[B]Full Video[/B] Source #' + str( srcNbr ) + ' ' + sourceName, unescape( sourceVideo ), 2, '' )
         srcNbr = srcNbr + 1

   if nPlayList > 1 :
      playList = playList.rstrip( ':;' )
      print "playList=" + playList
      Add_Play_List_Link('[B]Direct PLAY - Youtube[/B] [I]Playlist of above ' + str( nPlayList ) + ' videos[/I]', playList, 3, '')

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
   url = "http://www.dishtamilonline.com/"
   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()
   
   path = re.compile('<a href="(.+)"><b>Movies</b>').findall(link)
   if 'www' not in path[0]:
      path[0] = url + path[0]
   print "Movies=" + path[0]
   Add_Dir( '[B]Movies[/B]', path[0], 10, '')

   path = re.compile('<a href="(.+)"><b>TV Shows</b>').findall(link)
   if 'www' not in path:
      path[0] = url + path[0]
   print "Tv Shows=" + path[0]
   Add_Dir( '[B]TV Shows[/B]', path[0], 20, '')

   path = re.compile('<a href="(.+)"><b>TV Serials</b>').findall(link)
   if 'www' not in path:
      path[0] = url + path[0]
   print "Tv Serials=" + path[0]
   Add_Dir( '[B]TV Serials[/B]', path[0], 20, '')

   path = re.compile('<a href="(.+)"><b>Comedy</b>').findall(link)
   if 'www' not in path:
      path[0] = url + path[0]
   print "Comedy=" + path[0]
   Add_Dir( '[B]Comedy[/B]', path[0], 30, '')

   path = re.compile('<a href="(.+)"><b>Video Songs</b>').findall(link)
   if 'www' not in path:
      path[0] = url + path[0]
   print "Video Songs=" + path[0]
   Add_Dir( '[B]Video Songs[/B]', path[0], 40, '')

   path = re.compile('<a href="(.+)"><b>Wallpaper</b>').findall(link)
   if 'www' not in path:
      path[0] = url + path[0]
   print "Wallpaper=" + path[0]
   Add_Dir( '[B]Wallpaper[/B]', path[0], 60, '')
                       
def Movie_Categories( url ):
   print "Movie url = " + url
   baseUrl = re.compile('www\.(.+)\.com').findall(url)[0]
   baseUrl = 'http://www.'+baseUrl+'.com/'
   print "baseUrl=" + baseUrl

   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()

   path = re.compile('<a href="(.+)">New Movies</a>').findall(link)
   if 'www' not in path:
      path[0] = baseUrl + path[0]
   Add_Dir(' [B]New Movies[/B]', path[0], 11, '' )

   path = re.compile('<a href="(.+)">DvD Movies</a>').findall(link)
   if 'www' not in path:
      path[0] = baseUrl + path[0]
   Add_Dir(' [B]DVD Movies[/B]', path[0], 11, '' )

   path = re.compile('<a href="(.+)">Classic Movies</a>').findall(link)
   if 'www' not in path:
      path[0] = baseUrl + path[0]
   Add_Dir(' [B]Classic Movies[/B]', path[0], 11, '' )

   path = re.compile('<a href="(.+)">Mid Movies</a>').findall(link)
   if 'www' not in path:
      path[0] = baseUrl + path[0]
   Add_Dir(' [B]Mid Movies[/B]', path[0], 11, '' )

def Movie_Sort_Order( url ):
   print "Movie sort url = " + url
   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()

   url = url.replace( "&alp=all", "" )
   print "Sort Order:" + url

   Add_Dir(' [B]Recently Added[/B]', url + '&sort=date&page=1', 12, '' )
   Add_Dir(' [B]Most Viewed[/B]', url + '&sort=views&page=1', 12, '' )
   Add_Dir(' [B]Sort Alphabetically[/B]', url, 13, '' )

def Movie_List( url ):
   print "Movie list url = " + url
   baseUrl = re.compile('www\.(.+)\.com').findall(url)[0]
   baseUrl = 'http://www.'+baseUrl+'.com'
   print "baseUrl=" + baseUrl

   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()
   
   # Find the #pages in the current category
   pages=re.compile( '<span class="page"> <a href=".+">(\d{1,2})<' ).findall( link)

   # Find the movies in the current category
   match=re.compile('<img src="(.+)" alt=".*" width=".*" height=".*" style=".*" title=".*" onMouseOver=".+"\nonmouseout=".*"></a><br />\n\s+<a href="(.+)">(.+)</a><br />').findall(link)
   for thumbnail, movieUrl, name in match:
      Add_Dir( name, baseUrl + "/" + movieUrl, 14, baseUrl + thumbnail )

   url = url.replace( "&page=1", "&page=" )
   print "List url:" + url, "#pages=" + str( len( pages ) )
   # Scrape pages 1-->5, there's about 50 movies in 5 pages
   for page in pages:
      rurl = url + page
      print "Access URL=" + rurl
      req = urllib2.Request(rurl)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      match=re.compile('<img src="(.+)" alt=".*" width=".*" height=".*" style=".*" title=".*" onMouseOver=".+"\nonmouseout=".*"></a><br />\n\s+<a href="(.+)">(.+)</a><br />').findall(link)
      for thumbnail, movieUrl, name in match:
         Add_Dir( name, baseUrl + "/" + movieUrl, 14, baseUrl + thumbnail )

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

def Movies_Video_Link( url ):
   print "Video Link=" + url
   baseUrl = re.compile('www\.(.+)\.com').findall(url)[0]
   baseUrl = 'http://www.'+baseUrl+'.com/'
   print "baseUrl=" + baseUrl
   req = urllib2.Request( url )
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen( req )
   link=response.read()
   response.close()
   match=re.compile('<img src=".*" alt=".*" /> <a href="(.*)">Full Movie.*</a> <br />').findall(link)
   print match
   videoUrl = baseUrl + match[0]
   print "Video URL=" + videoUrl

   Load_Video( videoUrl )

def TV_Show_Sort_Order( url ):
   print "TV url = " + url

   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()

   url = url.replace( "&alp=all", "" )
   print "Sort Order:" + url

   Add_Dir(' [B]Recently Added[/B]', url + '&sort=date&page=1', 22, '' )
   Add_Dir(' [B]Most Viewed[/B]', url + '&sort=views&page=1', 22, '' )
   Add_Dir(' [B]Sort Alphabetically[/B]', url, 23, '' )

def TV_Show_List( url ):
   print "Tv show list url = " + url
   baseUrl = re.compile('www\.(.+)\.com').findall(url)[0]
   baseUrl = 'http://www.'+baseUrl+'.com'
   print "baseUrl=" + baseUrl
   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()
   
   # Find the #pages in the current category
   pages=re.compile( '<span class="page"> <a href=".+">(\d{1,2})<' ).findall( link)

   # Find the movies in the current category
   match=re.compile('<a href="(.+)">(.+)</a> <br />\n\s+<a href=".+"><img src="(.+)" width').findall( link )
   for movieUrl, name, thumbnail in match:
      Add_Dir( name, baseUrl + "/" + movieUrl, 24, baseUrl + thumbnail )

   url = url.replace( "&page=1", "&page=" )
   print "List url:" + url, "#pages=" + str (len( pages ) )
   # Scrape pages 1-->5, there's about 50 movies in 5 pages
   for page in pages:
      rurl = url + page
      print "Access URL=" + rurl
      req = urllib2.Request(rurl)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
      response = urllib2.urlopen(req)
      link=response.read()
      response.close()
      match=re.compile('<a href="(.+)">(.+)</a> <br />\n\s+<a href=".+"><img src="(.+)" width').findall( link )
      for movieUrl, name, thumbnail in match:
         Add_Dir( name, baseUrl + "/" + movieUrl, 24, baseUrl + thumbnail )

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

def TV_Show_Episode_List( url ):
   print "Tv Episode url = " + url
   baseUrl = re.compile('www\.(.+)\.com').findall(url)[0]
   baseUrl = 'http://www.'+baseUrl+'.com'
   print "baseUrl=" + baseUrl
   req = urllib2.Request(url)
   req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
   response = urllib2.urlopen(req)
   link=response.read()
   response.close()

   match=re.compile('<img src=".+" alt=".+" /> <a href="(.+)">(.+)</a> <br />').findall( link )
   for movieUrl, title in match:
      Add_Dir( title, baseUrl + "/" + movieUrl, 1, '' )

params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
   Main_Categories()
       
elif mode == 1:
   Load_Video( url )

elif mode == 2:
   Load_and_Play_Video( url, name )

elif mode == 3:
   Load_and_Play_Video_Links( url, name )

elif mode == 10:
   Movie_Categories( url )

elif mode == 11:
   Movie_Sort_Order( url )

elif mode == 12:
   Movie_List( url )

elif mode == 13:
   Movie_A_Z( url )

elif mode == 14:
   Movies_Video_Link( url )

elif mode == 20:
   TV_Show_Sort_Order( url )

elif mode == 22:
   TV_Show_List( url )

elif mode == 23:
   TV_Show_A_Z( url )

elif mode == 24:
   TV_Show_Episode_List( url )

xbmcplugin.endOfDirectory(int(sys.argv[1]))

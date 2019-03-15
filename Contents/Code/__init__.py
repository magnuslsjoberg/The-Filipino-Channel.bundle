import json
import os


# TFC id URL patterns 
RE_VIDEO_ID = Regex(r"(?P<url>https?://tfc.tv/(episode|live)/details/(?P<video_id>\d+))(/?.*)")

# ID numbers to fetch the video
#  axios.post('/media/fetch', { eid: 140506, sid: 4512, pv: false })
RE_MEDIA_ID = Regex(r"axios\.post\('/media/fetch', \{ eid: (?P<episode_id>\d+), sid: (?P<show_id>\d+),", Regex.MULTILINE )

if 'PLEXTOKEN' in os.environ:
    PLEX_TOKEN = os.environ['PLEXTOKEN']
else:
    PLEX_TOKEN = None

JsonFromUrl_POST = SharedCodeService.TFC_Shared.JsonFromUrl_POST
HtmlFromUrl_GET  = SharedCodeService.TFC_Shared.HtmlFromUrl_GET





# Debug
DEBUG           = True
DEBUG_STRUCTURE = False

# General
TITLE      = 'The Filipino Channel'
PREFIX     = '/video/tfctv'
USER_AGENT = 'Mozilla/4,0'

# Resources
ART      = 'art-tfctv.png'
ICON     = 'icon-tfctv.png'
LOGO     = 'icon-tfctv.png'

# GitHub latest version
CHECK_VERSION = False
VERSION_URL = 'https://raw.githubusercontent.com/magnuslsjoberg/The-Filipino-Channel.bundle/master/Contents/Version.txt'

# TFC main website URLs
BASE_URL = 'https://tfc.tv'

RE_SUB_CAT_ID = Regex(r"/category/list/(?P<sub_cat_id>\d+)/")
RE_SHOW_ID    = Regex(r"/show/details/(?P<show_id>\d+)/")
RE_EPISODE_ID = Regex(r"/episode/details/(?P<episode_id>\d+)/")
RE_MOVIE_ID   = Regex(r"/episode/details/(?P<movie_id>\d+)/")
RE_LIVE_ID    = Regex(r"/live/details/(?P<live_id>\d+)/")

# For some extremely strange and annoying reason data-src can't be extracted with XPath!!!
# <div data-sid="4655" class="show-cover" data-src="https://timg.tfc.tv/xcms/episodeimages/129284/20170614-ikaw-487-1.jpg">
RE_EPISODE_IMAGE_PATH = Regex(r'^<div data-sid="[^"]+" class="show-cover" data-src="(?P<image_path>[^"]+)">')

# style="background-image:url(https://timg.tfc.tv/xcms/categoryimages/4046/I-AMERICA-HERO-WEB.jpg);">
RE_MOVIE_BANNER_PATH = Regex(r'background-image:url\((?P<banner_path>[^"]+)\);')

# Max number of items to show in one listing
NUM_SHOWS_ON_PAGE = 12
MAX_NUM_EPISODES  = 50


VERSION = "x.x.x"
CACHE_TIME  = 0
DEBUG_LEVEL = 0

Login  = SharedCodeService.TFC_Shared.Login
Logout = SharedCodeService.TFC_Shared.Logout
DBG    = SharedCodeService.TFC_Shared.DBG

####################################################################################################
@route(PREFIX + '/validateprefs')
def ValidatePrefs( **kwargs ):
    
	Log.Info(DBG( "ValidatePrefs()" ))
	
	SetPrefs()
    
	return True

####################################################################################################
@route(PREFIX + '/setprefs')
def SetPrefs():

    global CACHE_TIME
    global DEBUG_LEVEL

    try:
        CACHE_TIME = int(Prefs['cache_time']) * CACHE_1HOUR
    except:
        CACHE_TIME = 0
        
    try:
        DEBUG_LEVEL = int(Prefs['debug_level'])
    except:
        DEBUG_LEVEL = 3
        
    Log.Info(DBG( "SetPrefs: cache_time  = %d hours" % int(CACHE_TIME/CACHE_1HOUR) ))
    Log.Info(DBG( "SetPrefs: debug_level = %d"       % int(DEBUG_LEVEL)            ))

        

####################################################################################################
def Start( **kwargs ):
    
    Log.Info(DBG( "Starting TFC.tv channel. Version: %s" % VERSION ))
    Log.Info(DBG( "Client.Product: '%s', Client.Platform: '%s'" % (Client.Product,Client.Platform) ))
            
    InputDirectoryObject.thumb = R('Search.png')
    DirectoryObject.art  = R(ART)

    ObjectContainer.title1 = TITLE
    ObjectContainer.title2 = 'MAIN MENU'

    SetPrefs()

    HTTP.Headers['User-Agent']      = USER_AGENT
    HTTP.Headers['Accept']          = '*/*'
    HTTP.Headers['Accept-Encoding'] = 'deflate, gzip'
    HTTP.CacheTime                  = 0
    
    Logout()

    # Speed up loading by precaching main page
    HTTP.PreCache( BASE_URL )
    
    # Set user cache time
    HTTP.CacheTime = CACHE_TIME
            
####################################################################################################
@handler( PREFIX, TITLE, art=ART, thumb=LOGO )
def MainMenu( **kwargs ):

    try:
    
        oc = ObjectContainer()

        if CHECK_VERSION:
        
            # Check latest version in GitHub
            try:
                html = HTML.ElementFromURL( VERSION_URL, cacheTime = 0 ) #### 24*CACHE_1HOUR )
                
                version = HTML.StringFromElement(html)
                Log.Info( version )
                
                oc.header  = "UPGRADE AVAILABLE!"
                oc.message = "Latest version %s found." % (version)
        
                return oc

            except:
                oc.header  = "ALL OK"
                oc.message = "NO version found."

                return oc
            
        if DEBUG_LEVEL > 0: Log.Debug(DBG( "Parsing main TFC page..." ))

        html = HTML.ElementFromURL( BASE_URL )

        categories = html.xpath('//div[@id="main_nav_desk"]/ul/li/a[@data-id]')

        for category in categories:
            category_name = category.xpath('./text()')[0]
            category_name = String.DecodeHTMLEntities( category_name ).strip()

            category_id = int(category.xpath('./@data-id')[0])

            if DEBUG_LEVEL > 0: Log.Debug(DBG( "%s:%d" % (category_name,category_id) ))

            oc.add( DirectoryObject( key = Callback( Category, title = TITLE, name = category_name, cat_id = category_id ), title = category_name ) )

        #oc.add( DirectoryObject( key = Callback( MostLovedShows, title = TITLE, name = 'Most Loved Shows' ), title = 'Most Loved Shows' ) )
        #oc.add(InputDirectoryObject(key = Callback(Search), title='Search', summary='Search The Filipino Channel', prompt='Search for...'))
        #oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.tfctv', title='Search', summary='Search The Filipno Channel', prompt='Search:', thumb=R('search.png')))

        return oc
        
    except:

        return NothingFound(TITLE, 'MainMenu', 'content')


####################################################################################################
@route( PREFIX + '/category', cat_id=int )
def Category( title, name, cat_id, **kwargs ):

    try:
    
        oc = ObjectContainer( title1 = title, title2 = name )
        
        html = HTML.ElementFromURL( BASE_URL )

        if DEBUG_LEVEL > 5: Log.Debug(DBG( "html: '%s'" % (HTML.StringFromElement(html)) ))

        sub_categories = html.xpath( '//div[@id="main_nav_desk"]/ul/li/a[@data-id="%d"]/following::ul[1]//a' % int(cat_id) )

        for sub_category in sub_categories:
            sub_category_name = sub_category.xpath('./text()')[0]
            sub_category_name = String.DecodeHTMLEntities( sub_category_name ).strip()

            sub_category_url = sub_category.xpath('./@href')[0]
            if sub_category_url.startswith('/'):
                sub_category_url = BASE_URL + sub_category_url

            if DEBUG_LEVEL > 0: Log.Debug(DBG( "    %s: %s" % (sub_category_name,sub_category_url) ))

            # Speed up loading by precaching sub category page
            HTTP.PreCache( "%s/1" % (sub_category_url) )
            
            oc.add( DirectoryObject( key = Callback( SubCategory, title = name, name = sub_category_name, url = sub_category_url ), title = sub_category_name ) )


        if len(oc) < 1:
            return NothingFound(title, name, 'items')

        return oc    
        
    except:
    
        return NothingFound(title, name, 'content')


####################################################################################################
@route( PREFIX + '/subcategory', page=int )
def SubCategory( title, name, url, page=1, **kwargs ):
 
    try:

        page_url = "%s/%d" % (url,page)

        if DEBUG_LEVEL > 0: Log.Debug(DBG( "Show: %s : %s" % (name,page_url) ))

        html = HTML.ElementFromURL( page_url )

        # Do we have multiple pages?
        try:
            last_page = int(html.xpath('//ul[@id="pagination"]/li/a/text()')[-1])
        except:
            last_page = 1
        if DEBUG_LEVEL > 2: Log.Debug(DBG( "Page %d (%d)" % (page, last_page) ))
        if last_page > 1:
            title2 = "%s - PAGE %d (%d)" % (name,page,last_page)
        else:
            title2 = name
            
        oc = ObjectContainer( title1 = title, title2 = title2 )
            
        shows = html.xpath('//section[contains(@class,"category-list")]//li[contains(@class,"og-grid-item-o")]')

        for show in shows:

            show_name = show.xpath('./@data-title')[0]
            show_name = String.DecodeHTMLEntities( show_name ).strip()
            if DEBUG_LEVEL > 1: Log.Debug(DBG( "  show_name  : %s" % (show_name) ))

            show_url = show.xpath('./a/@href')[0]
            if show_url.startswith('/'):
                show_url = BASE_URL + show_url
            if DEBUG_LEVEL > 1: Log.Debug(DBG( "    show_url   : %s" % (show_url) ))

            show_image = show.xpath('./a//img/@src')[0]
            if DEBUG_LEVEL > 1: Log.Debug(DBG( "    show_image : %s" % (show_image) ))

            show_banner = show_image
            if DEBUG_LEVEL > 1: Log.Debug(DBG( "    show_banner: %s" % (show_banner) ))

            show_blurb = show.xpath('./a//h3[@class="show-cover-thumb-aired-mobile"]/text()')[0]
            show_blurb = String.DecodeHTMLEntities( show_blurb ).strip()
            if DEBUG_LEVEL > 1: Log.Debug(DBG( "    show_blurb : %s" % (show_blurb) ))

            oc.add( DirectoryObject( key = Callback( Show, title = name, name = show_name, url = show_url ), title = show_name, thumb = show_image, art = show_banner, summary = show_blurb ) )

        # Add 'More...' button if more pages
        if page < last_page:
            # Speed up loading by precaching next page
            next_page_url = "%s/%d" % (url,page+1)
            HTTP.PreCache( next_page_url )
            oc.add( NextPageObject(key = Callback( SubCategory, title = title, name = name, url = url, page = page + 1 ) ) )

        if len(oc) < 1:
            return NothingFound(title, name, 'shows')

        if DEBUG_LEVEL > 0: Log.Debug(DBG( "Added %d DirectoryObject!" % int(len(oc)) ))

        return oc 
    
    except: 
        pass
    
    return NothingFound(title, name, 'content')


####################################################################################################
@route( PREFIX + '/show', page=int )
def Show( title, name, url, page=1, **kwargs ):
 
    try:

        page_url = "%s/%d" % (url,page)

        if DEBUG_LEVEL > 0: Log.Debug(DBG( "Show: %s : %s" % (name,page_url) ))

        # Don't login if already logged in!
        try:
            html = HTML.ElementFromURL( page_url )
        except:
            HTTP.Headers['Cookie'] = Login()
            if DEBUG_LEVEL > 1: Log.Debug(DBG( "Show::cookies: '%s'" % (HTTP.Headers['Cookie']) ))
            html = HTML.ElementFromURL( page_url )

        # Do we have multiple pages?
        try:
            last_page = int(html.xpath('//ul[@id="pagination"]/li/a/text()')[-1])
        except:
            last_page = 1
        if DEBUG_LEVEL > 2: Log.Debug(DBG( "Page %d (%d)" % (page, last_page) ))
        if last_page > 1:
            title2 = "%s - PAGE %d (%d)" % (name,page,last_page)
        else:
            title2 = name
            
        oc = ObjectContainer( title1 = title, title2 = title2 )

        canonical_url = html.xpath('//link[@rel="canonical"]/@href')[0]
        if DEBUG_LEVEL > 2: Log.Debug(DBG( "  canonical_url : %s" % (canonical_url) ))

        try:
            live_id = RE_LIVE_ID.search(canonical_url).group('live_id')
        except:
            live_id = None
        if DEBUG_LEVEL > 2: Log.Debug(DBG( "  live_id : %s" % (live_id) ))

        if live_id:

            # Live stream
            live_name  = html.xpath('//meta[@property="og:title"]/@content')[0]
            live_name = String.DecodeHTMLEntities( live_name ).strip()
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "  live_name : %s" % (live_name) ))

            live_blurb = html.xpath('//meta[@property="og:description"]/@content')[0]
            live_blurb = String.DecodeHTMLEntities( live_blurb ).strip()
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "  live_blurb : %s..." % (live_blurb[:50]) ))

            live_image = html.xpath('//meta[@property="og:image"]/@content')[0]
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "  live_image : %s" % (live_image) ))

            live_banner = live_image
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "  live_banner : %s" % (live_banner) ))

            oc.add( 
                VideoClipObject(
                    #url                     = canonical_url,
                    key = Callback( MetadataObjectForURL_INIT, url = canonical_url ),
                    rating_key = canonical_url,
                    title                   = live_name,
                    thumb                   = live_image,
                    source_title            = 'TFC.tv',
                    summary                 = live_blurb,
                    #duration                = duration,
                    #originally_available_at = originally_available_at,
                    art                     = live_banner,
                    items = [
                        MediaObject(
                            parts = [
                                PartObject( key = HTTPLiveStreamURL( Callback( PlayVideo_INIT, url = BASE_URL + episode_url )))
                            ],
                            video_resolution = '720',
                            audio_channels = 2,
                            optimized_for_streaming = True
                        )
                    ]
                )
            )

            return oc

        # it is either a movie or a tv show
        try:
            show_banner = html.xpath('//link[@rel="image_src"]/@href')[0]
        except:
            show_banner = None
        if DEBUG_LEVEL > 1: Log.Debug(DBG( "  show_banner : %s" % (show_banner) ))

        try:
            episodes = html.xpath('//section[@class="sub-category-page"]//li[contains(@class,"og-grid-item")]')
        except:
            episodes = []
        if DEBUG_LEVEL > 1: Log.Debug(DBG( "  Found %d episodes!" % int(len(episodes)) ))

        if len(episodes) == 0:

            # Assume it is a movie

            movie_name  = html.xpath('//meta[@property="og:title"]/@content')[0]
            movie_name = String.DecodeHTMLEntities( movie_name ).strip()
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "    movie_name : %s" % (movie_name) ))

            movie_blurb = html.xpath('//meta[@property="og:description"]/@content')[0]
            movie_blurb = String.DecodeHTMLEntities( movie_blurb ).strip()

            movie_image = html.xpath('//meta[@property="og:image"]/@content')[0]
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "    movie_image : %s" % (movie_image) ))

            try:
                banner_path = html.xpath('//div[contains(@class,"header-hero-image")]/@style')[0]
                movie_banner = RE_MOVIE_BANNER_PATH.search( banner_path ).group('banner_path')
            except:
                movie_banner = None
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "    movie_banner : %s" % (movie_banner) ))

            # Extract movie_url
            movie_url = html.xpath('//div[contains(@class,"header-hero-image")]//a/@href')[0]
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "    movie_url : %s" % (movie_url) ))

            oc.add( 
                MovieObject(
                    #url                     = BASE_URL + movie_url,
                    key = Callback( MetadataObjectForURL_INIT, url = BASE_URL + movie_url ),
                    rating_key = movie_url,
                    title                   = movie_name,
                    thumb                   = movie_image,
                    source_title            = 'TFC.tv',
                    summary                 = movie_blurb,
                    #duration                = duration,
                    #originally_available_at = originally_available_at,
                    #art                     = movie_banner,
                    items = [
                        MediaObject(
                            parts = [
                                PartObject( key = HTTPLiveStreamURL( Callback( PlayVideo_INIT, url = BASE_URL + episode_url )))
                            ],
                            video_resolution = '720',
                            audio_channels = 2,
                            optimized_for_streaming = True
                        )
                    ]
                )
            )

            # Need to logout?
            #Log.Debug( '# About to log out 1 #' )
            #Logout()
            return oc

        else:

            # Extract show id from url
            show_id = RE_SHOW_ID.search(page_url).group('show_id')
            if DEBUG_LEVEL > 2: Log.Debug(DBG( "    show_id : %s" % (show_id) ))

            for episode in episodes:

                episode_name = episode.xpath('./a/div[@class="show-date"]/text()')[0]
                episode_name = String.DecodeHTMLEntities( episode_name ).strip()
                if DEBUG_LEVEL > 2: Log.Debug(DBG( "    episode_name : %s" % (episode_name) ))

                episode_url = episode.xpath('./a/@href')[0]
                if DEBUG_LEVEL > 2: Log.Debug(DBG( "        episode_url : %s" % (episode_url) ))

                #originally_available_at = Datetime.ParseDate(episode.xpath('./@data-aired'))

                # For some extremely strange and annoying reason data-src can't be extracted with XPath!!!
                # <div data-sid="4655" class="show-cover" data-src="https://timg.tfc.tv/xcms/episodeimages/129284/20170614-ikaw-487-1.jpg">
                image_path = HTML.StringFromElement( episode.xpath('./a//div[@class="show-cover"]')[0] )
                if DEBUG_LEVEL > 5: Log.Debug(DBG( "        image_path : %s" % (image_path) ))

                m = RE_EPISODE_IMAGE_PATH.search( image_path )
                if m:
                    episode_image = m.group('image_path')
                else:
                    episode_image = None
                if DEBUG_LEVEL > 2: Log.Debug(DBG( "        episode_image : %s" % (episode_image) ))

                episode_blurb = episode.xpath('./@data-show-description')[0]
                episode_blurb = String.DecodeHTMLEntities( episode_blurb ).strip()
                if DEBUG_LEVEL > 2: Log.Debug(DBG( "        episode_blurb : %s..." % (episode_blurb[:50]) ))

                oc.add( 
                    EpisodeObject(
                        #url                     = BASE_URL + episode_url,
                        key = Callback( MetadataObjectForURL_INIT, url = BASE_URL + episode_url ),
                        rating_key = episode_url,
                        title                   = episode_name,
                        thumb                   = episode_image,
                        source_title            = 'TFC.tv',
                        summary                 = episode_blurb,
                        show                    = name,
                        #season                  = season,
                        #absolute_index           = index,
                        #duration                = duration,
                        #originally_available_at = originally_available_at,
                        art                     = show_banner,
                        items = [
                            MediaObject(
                                parts = [
                                    PartObject( key = HTTPLiveStreamURL( Callback( PlayVideo_INIT, url = BASE_URL + episode_url )))
                                ],
                                video_resolution = '720',
                                audio_channels = 2,
                                optimized_for_streaming = True
                            )
                        ]
                    )
                )

                        
            # Add 'More...' button if more pages
            if page < last_page:
                # Speed up loading by precaching next page
                next_page_url = "%s/%d" % (url,page+1)
                HTTP.PreCache( next_page_url )
                oc.add( NextPageObject(key = Callback( Show, title = title, name = name, url = url, page = page + 1 ) ) )

            if len(oc) < 1:
                return NothingFound(title, name, 'episodes')

            # Need to logout?
            #Log.Debug( '# About to log out 2 #' )
            #Logout()
            return oc 

    except:

        # Need to logout?
        #Log.Debug( '# About to log out 3 #' )
        #Logout()
        return NothingFound(title, name, 'content')
    
    
####################################################################################################
def NothingFound(title, name, items):

    oc = ObjectContainer( title1 = title, title2 = name )

    oc.header  = name
    oc.message = "No %s found." % str(items)
    
    return oc


## EOF ##




####################################################################################################
# URLs to determine video type
# EPISODE: http://tfc.tv/episode/details/140208/the-good-son-october-20-2017
# MOVIE  : http://tfc.tv/show/details/2988/raketeros
# LIVE   : http://tfc.tv/live/details/41623/anc-live-streaming
# <link rel="canonical" href="http://tfc.tv/live/details/41623/anc-live-streaming" />
RE_TYPE_EPISODE = Regex(r"https?://tfc.tv/episode/.*")
RE_TYPE_MOVIE   = Regex(r"https?://tfc.tv/show/.*")
RE_TYPE_LIVE    = Regex(r"https?://tfc.tv/live/.*")

# Date and duration info
#         Episode 20 of 27 | October 20, 2017 | 32m
#          2017    |   1H 40M
RE_INFO_EPISODE = Regex(r"Episode\s+(?P<index>\d+)\s+of\s+\d+\s+\|\s+(?P<date>[1-2][0-9][0-9][0-9])\s+\|\s+(?P<minutes>[0-5]?[0-9])m")
RE_INFO_MOVIE   = Regex(r"(?P<date>[1-2][0-9][0-9][0-9])\s+\|\s+(?P<hours>[0-9])H (?P<minutes>[0-5][0-9])M")
         
# style="background-image:url(https://timg.tfc.tv/xcms/categoryimages/4046/I-AMERICA-HERO-WEB.jpg);">
RE_MOVIE_BANNER_PATH = Regex(r'background-image:url\((?P<banner_path>[^"]+)\);')       
  
@route( PREFIX + '/MetadataObjectForURL_INIT' )
def MetadataObjectForURL_INIT( url ):

    if DEBUG_LEVEL > 0: Log.Debug(DBG( "MetadataObjectForURL, url = '%s'" % (url) ))
    
    try:
    
        html = HTML.ElementFromURL( url, cacheTime = CACHE_TIME )

        try:
            info = html.xpath('//div[contains(@class,"hero-image-rating")]/text()')[0]
            info = String.DecodeHTMLEntities( info ).strip()
        except:
            info = None

        try:
            title  = html.xpath('//meta[@property="og:title"]/@content')[0]
            title = String.DecodeHTMLEntities( title ).strip()
        except:
            title = None

        try:
            summary = html.xpath('//meta[@property="og:description"]/@content')[0]
            summary = String.DecodeHTMLEntities( summary ).strip()
        except:
            summary = None

        try:
            image = html.xpath('//meta[@property="og:image"]/@content')[0].strip()
        except:
            image = None

        try:
            banner_path = html.xpath('//div[@class="header-hero-image"]/@style')[0]
            banner = RE_MOVIE_BANNER_PATH.search( banner_path ).group('banner_path')
        except:
            banner = None

        try:
            show = html.xpath('//h1[@class="topic-title-h1"]')[0]
            show = String.DecodeHTMLEntities( show ).strip()
        except:
            show = None
            
        if DEBUG_LEVEL > 3: Log.Debug(DBG( "info     : %s" % (info) ))
        if DEBUG_LEVEL > 3: Log.Debug(DBG( "title    : %s" % (title) ))
        if DEBUG_LEVEL > 3: Log.Debug(DBG( "summary  : %s" % (summary[:50]) ))
        if DEBUG_LEVEL > 3: Log.Debug(DBG( "image    : %s" % (image) ))
        if DEBUG_LEVEL > 3: Log.Debug(DBG( "banner   : %s" % (banner) ))
        if DEBUG_LEVEL > 3: Log.Debug(DBG( "show     : %s" % (show) ))
                    
        canonical_url = html.xpath('//link[@rel="canonical"]/@href')[0]
        if DEBUG_LEVEL > 3: Log.Debug(DBG( "canonical_url : %s" % (canonical_url) ))

        if RE_TYPE_EPISODE.match( canonical_url ):
        
            m = RE_INFO_EPISODE.match( info )
            if m:
                index    = int(m.group('index'))
                date     = Datetime.ParseDate(m.group('date'))
                duration = 60 * 1000 * int(m.group('minutes'))
            else:
                index    = None
                date     = None
                duration = None

            if DEBUG_LEVEL > 3: Log.Debug(DBG( "index    : %s" % (index) ))
            ####if DEBUG_LEVEL > 3: Log.Debug(DBG( "date     : %s" % (date.strftime('%Y-%m-%d')) ))
            if DEBUG_LEVEL > 3: Log.Debug(DBG( "duration : %s" % (duration) ))
            if DEBUG_LEVEL > 3: Log.Debug(DBG( "RETURN EpisodeObject" ))
                     
            return( 
                ObjectContainer(
                    objects = [
                        EpisodeObject(
                            key                     = Callback( MetadataObjectForURL_INIT, url = canonical_url ),
                            rating_key              = canonical_url,
                            title                   = title,
                            thumb                   = image,
                            source_title            = 'TFC.tv',
                            summary                 = summary,
                            show                    = show,
                            #season                  = season,
                            absolute_index          = index,
                            duration                = duration,
                            originally_available_at = date,
                            art                     = banner
                        )
                    ]
                )
            )
                       
        elif RE_TYPE_MOVIE.match( canonical_url ):
        
            m = RE_INFO_MOVIE.match( info )
            if m:
                date     = Datetime.ParseDate(m.group('date'))
                duration = 60 * 1000 * (int(m.group('hours')) + 60 * int(m.group('minutes')))
            else:
                date     = None
                duration = None

            #if DEBUG_LEVEL > 3: Log.Debug(DBG( "date     : %s" % (date.strftime('%Y-%m-%d')) ))
            if DEBUG_LEVEL > 3: Log.Debug(DBG( "duration : %d" % (duration) ))
            if DEBUG_LEVEL > 3: Log.Debug(DBG( "RETURN MovieObject" ))

            return( 
                ObjectContainer(
                    objects = [
                        MovieObject(
                            key                     = Callback( MetadataObjectForURL_INIT, canonical_url ),
                            rating_key              = canonical_url,
                            title                   = title,
                            thumb                   = image,
                            source_title            = 'TFC.tv',
                            summary                 = summary,
                            tagline                 = title,
                            duration                = duration,
                            originally_available_at = date,
                            art                     = banner
                        )
                    ]
                )
            )
                                                      
        elif RE_TYPE_LIVE.match( canonical_url ):
    
            if DEBUG_LEVEL > 3: Log.Debug(DBG( "RETURN VideoClipObject" ))

            return( 
                ObjectContainer(
                    objects = [
                        VideoClipObject(
                            key                     = Callback( MetadataObjectForURL_INIT, url = canonical_url ),
                            rating_key              = canonical_url,
                            title                   = title,
                            thumb                   = image,
                            source_title            = 'TFC.tv',
                            summary                 = summary,
                            tagline                 = title,
                            #duration                = duration,
                            #originally_available_at = originally_available_at,
                            art                     = banner
                        )
                    ]
                )
            )
      
    except:
        Log.Error(DBG( "MetadataObjectForURL_INIT FAILED! url = '%s'" % (url) ))
    
    raise Ex.MediaNotAvailable
    
    
    
    



####################################################################################################
@route( PREFIX + '/playvideo.m3u8' )
def PlayVideo_INIT( url, **kwargs ):

    try:

        if DEBUG_LEVEL > 1: Log.Debug(DBG( "PlayVideo_INIT, url = '%s'" % (url) ))

        # Get the m3u8 playlist url
        playlistUrl = GetPlaylistURL( url )
        if DEBUG_LEVEL > 1: Log.Debug(DBG( "playlistUrl: %s" % playlistUrl ))

        if DEBUG_LEVEL > 1: Log.Debug(DBG( "Client.Product: '%s', Client.Platform: '%s'" % (Client.Product,Client.Platform) ))
        
        #if Client.Product == 'Plex Web' and Client.Platform == 'Safari':
        #    # Play the stream directly...
        #    return IndirectResponse( VideoClipObject, key = HTTPLiveStreamURL( url = playlistUrl ) )
        
        # Can't play the stream directly, need to parse index files and segments
        indexUrl = GetIndexURL( playlistUrl )
        if DEBUG_LEVEL > 1: Log.Debug(DBG( "indexUrl: %s" % indexUrl ))

        segmentList = RewriteSegmentList( indexUrl )
    
        # Play the stream...
        ###return IndirectResponse( VideoClipObject, key = HTTPLiveStreamURL( url = playlistUrl ) )

        return segmentList
  
  
        '''
        some other videos have this:
2019-03-10 13:38:35 [ DEBUG ] PlayerComponent.cpp @ 593 - ffmpeg/demuxer: hls,applehttp: HLS request for url 'https://amssabscbn.akamaized.net/f20426f8-58d4-4319-a429-3d2b801994cd/gbl-tpq-20181208-.ism/QualityLevels(40000)/Fragments(audioname=0,format=m3u8-aapl)', offset 0, playlist 0 
2019-03-10 13:38:35 [ ERROR ] PlayerComponent.cpp @ 599 - ffmpeg/demuxer: hls,applehttp: SAMPLE-AES encryption is not supported yet 
        '''

      
    except:
        Log.Error(DBG( "PlayVideo(%s) FAILED!" % url ))

    raise Ex.MediaNotAvailable


####################################################################################################
def GetPlaylistURL( url ):

    try:
    
        playlistUrl = None
        
        # Login
        cookies = Login()
        if DEBUG_LEVEL > 0: Log.Debug(DBG( "cookies: '%s'" % (cookies) ))
        
        # Get episode/movie details
        source = HTTP.Request( url ).content

        # Extract episode and show id from HTML
        m = RE_MEDIA_ID.search( source )
        try:
            episode_id = m.group('episode_id')
            if DEBUG_LEVEL > 3: Log.Debug(DBG( "episode_id = %s" % (episode_id) ))
        except:
            Log.Error(DBG( "episode_id not found!" ))
            raise
        try:
            show_id = m.group('show_id')
            if DEBUG_LEVEL > 3: Log.Debug(DBG( "show_id = %s" % (show_id) ))
        except:
            Log.Error(DBG( "show_id not found!" ))
            raise

        # Build up POST request to get media info
        MEDIA_INFO_URL      = 'https://tfc.tv/media/fetch'    
        MEDIA_INFO_HEADERS  =  {
            'Cookie'  : cookies,
            'Referer' : url
        }
        MEDIA_INFO_PARAMS = {
            'eid' : episode_id,
            'sid' : show_id, 
            'pv'  : 'false'
        }
        mediaInfoJson = JsonFromUrl_POST( MEDIA_INFO_URL, headers = MEDIA_INFO_HEADERS, params = MEDIA_INFO_PARAMS )

        if DEBUG_LEVEL > 2: Log.Debug(DBG( "JSON:  %s" % json.dumps( mediaInfoJson, indent = 4, sort_keys = True ) ))

        if not (mediaInfoJson['StatusCode'] == 1 and mediaInfoJson['StatusMessage'] == 'OK'):
            Log.Error(DBG( "JSON ERROR %s:%s" % (mediaInfoJson['StatusCode'],mediaInfoJson['StatusMessage']) ))

        # Get master playlist URL
        playlistUrl = mediaInfoJson['media']['source'][0]['src']

        # Remove bandwidth limitation
        # playlistUrl = playlistUrl.replace('&b=100-1000', '')
        # playlistUrl = playlistUrl + '&__b__=5000'
        
        return playlistUrl
        
    except:
        raise Ex.MediaNotAvailable

    raise Ex.MediaNotAvailable


####################################################################################################
###@route( PREFIX + '/index/{url}.m3u8' )
def GetIndexURL( playlistUrl ):
    '''
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=362000,RESOLUTION=320x240,CODECS="avc1.66.30, mp4a.40.2",CLOSED-CAPTIONS=NONE
https://o2-i.akamaihd.net/i/epolapple/20020725/20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil/index_0_av.m3u8?null=0&id=AgBR5D7VAhetVIl4hVz4PWIc%2fviIs1XRBb534Z13CD%2fO5Yc5sLT8ZtLIaZgNJvSnDI52r%2f4EvebQZA%3d%3d&hdntl=exp=1552337417~acl=%2fi%2fepolapple%2f20020725%2f20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil%2f*~data=hdntl~hmac=ac4aa3b3426fca324f54ebc54e645e138856b201250ab04e4e9459c66f0b40b9
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=534000,RESOLUTION=480x360,CODECS="avc1.66.30, mp4a.40.2",CLOSED-CAPTIONS=NONE
https://o2-i.akamaihd.net/i/epolapple/20020725/20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil/index_1_av.m3u8?null=0&id=AgBR5D7VAhetVIl4hVz4PWIc%2fviIs1XRBb534Z13CD%2fO5Yc5sLT8ZtLIaZgNJvSnDI52r%2f4EvebQZA%3d%3d&hdntl=exp=1552337417~acl=%2fi%2fepolapple%2f20020725%2f20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil%2f*~data=hdntl~hmac=ac4aa3b3426fca324f54ebc54e645e138856b201250ab04e4e9459c66f0b40b9
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=838000,RESOLUTION=512x384,CODECS="avc1.77.30, mp4a.40.2",CLOSED-CAPTIONS=NONE
https://o2-i.akamaihd.net/i/epolapple/20020725/20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil/index_2_av.m3u8?null=0&id=AgBR5D7VAhetVIl4hVz4PWIc%2fviIs1XRBb534Z13CD%2fO5Yc5sLT8ZtLIaZgNJvSnDI52r%2f4EvebQZA%3d%3d&hdntl=exp=1552337417~acl=%2fi%2fepolapple%2f20020725%2f20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil%2f*~data=hdntl~hmac=ac4aa3b3426fca324f54ebc54e645e138856b201250ab04e4e9459c66f0b40b9
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1046000,RESOLUTION=640x480,CODECS="avc1.77.30, mp4a.40.2",CLOSED-CAPTIONS=NONE
https://o2-i.akamaihd.net/i/epolapple/20020725/20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil/index_3_av.m3u8?null=0&id=AgBR5D7VAhetVIl4hVz4PWIc%2fviIs1XRBb534Z13CD%2fO5Yc5sLT8ZtLIaZgNJvSnDI52r%2f4EvebQZA%3d%3d&hdntl=exp=1552337417~acl=%2fi%2fepolapple%2f20020725%2f20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil%2f*~data=hdntl~hmac=ac4aa3b3426fca324f54ebc54e645e138856b201250ab04e4e9459c66f0b40b9
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1359000,RESOLUTION=640x480,CODECS="avc1.77.30, mp4a.40.2",CLOSED-CAPTIONS=NONE
https://o2-i.akamaihd.net/i/epolapple/20020725/20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil/index_4_av.m3u8?null=0&id=AgBR5D7VAhetVIl4hVz4PWIc%2fviIs1XRBb534Z13CD%2fO5Yc5sLT8ZtLIaZgNJvSnDI52r%2f4EvebQZA%3d%3d&hdntl=exp=1552337417~acl=%2fi%2fepolapple%2f20020725%2f20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil%2f*~data=hdntl~hmac=ac4aa3b3426fca324f54ebc54e645e138856b201250ab04e4e9459c66f0b40b9
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1567000,RESOLUTION=640x480,CODECS="avc1.77.30, mp4a.40.2",CLOSED-CAPTIONS=NONE
https://o2-i.akamaihd.net/i/epolapple/20020725/20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil/index_5_av.m3u8?null=0&id=AgBR5D7VAhetVIl4hVz4PWIc%2fviIs1XRBb534Z13CD%2fO5Yc5sLT8ZtLIaZgNJvSnDI52r%2f4EvebQZA%3d%3d&hdntl=exp=1552337417~acl=%2fi%2fepolapple%2f20020725%2f20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil%2f*~data=hdntl~hmac=ac4aa3b3426fca324f54ebc54e645e138856b201250ab04e4e9459c66f0b40b9
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=62000,CODECS="mp4a.40.2",CLOSED-CAPTIONS=NONE
https://o2-i.akamaihd.net/i/epolapple/20020725/20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil/index_0_a.m3u8?null=0&id=AgBR5D7VAhetVIl4hVz4PWIc%2fviIs1XRBb534Z13CD%2fO5Yc5sLT8ZtLIaZgNJvSnDI52r%2f4EvebQZA%3d%3d&hdntl=exp=1552337417~acl=%2fi%2fepolapple%2f20020725%2f20020725-epolapple-,300000,500000,800000,1000000,1300000,1500000,.mp4.csmil%2f*~data=hdntl~hmac=ac4aa3b3426fca324f54ebc54e645e138856b201250ab04e4e9459c66f0b40b9
    '''
    RE_MASTER_M3U8_EXT = Regex( r"^#EXT-X-STREAM-INF:.*,BANDWIDTH=(?P<bandwidth>\d+).*,RESOLUTION=(?P<width>\d+)x(?P<height>\d+).*$" )
    RE_MASTER_M3U8_URL = Regex( r"^(?P<url>https://.*)$" )
    
    #playlistUrl = String.Decode(playlistUrl)
    #Log.Debug(DBG( "#################### playlistUrl = '%s'" % playlistUrl ))

    playlistHtml = HTTP.Request( playlistUrl ).content
    Log.Debug(DBG( "#################### PLAYLIST ####################\n%s##################################################" % playlistHtml ))
    
    stream  = None
    streams = []
    for line in playlistHtml.splitlines():
        #Log.Debug(DBG( "line: '%s'" % (line) ))
        m = RE_MASTER_M3U8_EXT.search( line )
        if m:
            stream = m.groupdict()
            Log.Debug(DBG( "STREAM: %s" % (stream) ))
        elif stream:
            m = RE_MASTER_M3U8_URL.search( line )
            if m:
                stream['url'] = m.group('url')
                streams.append( stream )
                stream = None
                Log.Debug(DBG( "INDEX URL = '%s'" % (m.group('url')) ))
                
    streams.sort( key = lambda s: int(s['bandwidth']), reverse = True )
    
    #for s in streams:
    #    Log.Debug(DBG( s['bandwidth'] ))
     
    return streams[0]['url']
    

####################################################################################################
def RewriteSegmentList( indexUrl ):
        
    segmentList = HTTP.Request( indexUrl ).content
    #Log.Debug(DBG( "#################### SEGMENT LIST ####################\n%s##################################################" % segmentList[:2048] ))

    RE_X_KEY_URI = Regex( r'#EXT-X-KEY:METHOD=AES-128,URI="(?P<uri>https://[^"]+)"') 
    
    newSegmentList = ''

    for line in segmentList.splitlines():

        if line.startswith('#EXT-X-KEY:'):
            m = RE_X_KEY_URI.search( line )
            if m:
                oldUri = m.group('uri')
                newUri = '/video/tfctv/segment/{}.ts?X-Plex-Token={}'.format( String.Encode(oldUri), PLEX_TOKEN )
                newSegmentList += line.replace( oldUri, newUri ) + '\n'
                #Log.Debug(DBG( "oldUri = '%s'" % oldUri ))
                #Log.Debug(DBG( "newUri = '%s'" % newUri ))
                #Log.Debug(DBG( "newLine = '%s'" % line.replace( oldUri, newUri ) ))
        elif line.startswith('http') or '.ts' in line:
            newSegmentList += '/video/tfctv/segment/{}.ts?X-Plex-Token={}\n'.format( String.Encode(line), PLEX_TOKEN )
        elif 'EXT-X-DISCONTINUITY' in line:
            continue
        else:
            newSegmentList += line + '\n'

    #Log.Debug(DBG( "#################### NEW SEGMENT LIST ####################\n%s##################################################" % newSegmentList[:2048] ))

    return newSegmentList
    
    
####################################################################################################
@route( PREFIX + '/segment/{url}.ts' )
def Segment(url):

    try:
        return HTTP.Request( String.Decode(url), headers = HTTP.Headers, cacheTime = 0 ).content
    except:
        raise Ex.MediaNotAvailable


## EOF ##

    

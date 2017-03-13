import base64
import pprint
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import brotli
import bs4

INDEX_NAME = '__index__'

PAGE_CACHE_DIR = 'cache'
LINK_CACHE_DIR = 'linkCache'

SEED_DIR = 'seed'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

MAX_ITERATIONS = 100

WAIT_TIME_MSEC = 1.5 * 1000

# Facebook usually deals with bots by sending them to an uncompressed login page.
# If we hit this number of uncompressed pages, then bail.
MAX_FAILURE_ENCODING_COUNT = 5

PERSON_URL_BASE = 'https://www.facebook.com/'
SITE_URL_BASE = 'https://www.facebook.com'

USERNAME_KEY = '__username__'

SKIP_URLS = set([
    'https://www.facebook.com/campaign/landing.php',
    'https://www.facebook.com/profile.php'
])

SKIP_SUBPAGES = set([
   'about',
   'allactivity',
   'approve',
   'apps_like',
   'apps_used',
   'books',
   'books_favorite',
   'books_read',
   'books_want',
   'endoapp',
   'events',
   'explanation',
   'friends',
   'following',
   'friends_all',
   'friends_college',
   'friends_current_city',
   'friends_high_school',
   'friends_hometown',
   'friends_mutual',
   'friends_recent',
   'friends_suggested',
   'friends_with_unseen_posts',
   'friends_with_upcoming_birthdays',
   'friends_work',
   'games',
   'games_play',
   'groups',
   'groups_member',
   'info',
   'likes',
   'likes_all',
   'likes_people',
   'likes_restaurants',
   'likes_section_apps_and_games',
   'likes_section_books',
   'likes_section_movies',
   'likes_section_music',
   'likes_section_sports_athletes',
   'likes_section_sports_teams',
   'likes_section_tv_shows',
   'map',
   'media_set',
   'movies',
   'music',
   'music_favs',
   'music_saved',
   'notes',
   'notes_about_me',
   'past_events',
   'photos',
   'photos_albums',
   'photos_all',
   'photos_of',
   'places_cities_desktop',
   'places_recent',
   'places_visited',
   'requests',
   'reviews',
   'sports',
   'sports_athletes',
   'sports_teams',
   'timeline',
   'tv',
   'upjawbone',
   'upcoming_events'
   'video_movies_favorite',
   'video_movies_want',
   'video_movies_watch',
   'videos',
   'videos_by',
   'videos_of',
   'video_tv_shows_favorite',
   'video_tv_shows_want',
   'video_tv_shows_watch'
])

class NoEncodingException(Exception):
    pass

# Transform the url into a path into the cache.
# We will stip off the protocol.
# Then everything before the page will be a dir.
# The page (and any params or anchors) will become a file.
# Finally, if the page does not have an extension, give it a .html extention.
# This is to prevent this situation:
#   - test.com/people
#   - test.com/people/bob.html
# Both are valid pages, but in one "people" will be a file and in the the other it is a dir.
# Fragments are ignored.
def cachePath(url, cacheDir):
    parts = urllib.parse.urlparse(url)

    path = os.path.join(cacheDir, parts.netloc, parts.path.lstrip('/'))

    if (not(path.endswith('.php') or path.endswith('.html'))):
        path += '.html'

    if (parts.query != ''):
        path += '?' + parts.query

    return path

def cacheFetch(url, cacheDir = PAGE_CACHE_DIR):
    path = cachePath(url, cacheDir)
    if (not os.path.isfile(path)):
        return False, ''

    content = ''
    with open(path, 'r') as inFile:
        content = inFile.read()

    return True, content

def cachePut(url, content, cacheDir = PAGE_CACHE_DIR):
    path = cachePath(url, cacheDir)
    os.makedirs(os.path.dirname(path), exist_ok = True)

    with open(path, 'w') as outFile:
        outFile.write(content)

def fetch(url):
    ok, content = cacheFetch(url)
    if (ok):
        return content

    # Wait the specificed amount of time between fetches.
    # We don't need to wait the full duration every time since there will be some lag
    # between the last fetch while we are processing the data.
    if hasattr(fetch, "lastFetch"):
        now = int(round(time.time() * 1000))
        sleepTimeMS = max(0, WAIT_TIME_MSEC - (now - fetch.lastFetch))

        time.sleep(sleepTimeMS / 1000.0)

    print("Fetching: " + url)

    request = urllib.request.Request(
        url,
        data = None,
        headers = {
            'pragma': 'no-cache',
            # 'accept-encoding': 'gzip, deflate, sdch, br',
            'accept-encoding': 'br',
            'accept-language': 'en-US,en;q=0.8,hr;q=0.6',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'cache-control': 'no-cache',
            'authority': 'www.facebook.com',
            # 'cookie': 'fr=0OC5lonEnZlOnJn8c..BYt6SV.uN.AAA.0.0.BYt7vN.AWWng2gp; datr=zru3WCG6iayT7Fs4LlLFy8jX; reg_fb_ref=https%3A%2F%2Fmbasic.facebook.com%2Fphoto.php%3Ffbid%3D1385526974790625; reg_fb_gate=https%3A%2F%2Fmbasic.facebook.com%2Fphoto.php%3Ffbid%3D1385526974790625; wd=1920x465',
            'referer': 'https://www.google.com/'
        }
    )

    try:
        content = ''
        with urllib.request.urlopen(request) as response:
            fetch.lastFetch = int(round(time.time() * 1000))

            if (response.status != 200):
                print("   FAILED to fetch. Code: %d, Reason: %s." % (response.status, response.reason))
                return ''

            # Check the encoding.
            # Facebook always sends content compressed in brotli.
            if (response.getheader('content-encoding') == 'br'):
                content = str(brotli.decompress(response.read()))
            elif (response.getheader('content-encoding') == None):
                raise NoEncodingException()
            else:
                print("   ERROR: Unknown encoding: '%s'" % (response.getheader('content-encoding')))
                return ''

            cachePut(url, content)

            print('   Success')
    except urllib.error.HTTPError as ex:
        # This is probably because of privacy settings.
        # Write an (almost) empty file so we don't try to fetch it again.
        if (ex.code == 404):
            cachePut(url, '404')
            print('   404')
            return ''
        else:
            raise ex
    except UnicodeEncodeError as ex:
        print('   UnicodeEncodeError')
        cachePut(url, "ERROR: %s -- %s" % (type(ex), str(ex)))
        return ''

    return content

# Will return None if we don't want the link.
def cleanFacebookURL(url):
    parts = urllib.parse.urlparse(url)

    scheme = parts.scheme.strip()
    netloc = parts.netloc.strip()
    path = parts.path.strip().rstrip('/')

    if (netloc != 'www.facebook.com'):
        return None

    if (path == '' or path == '/'):
        return None

    match = re.search(r'^/[^/]+/(.+)', path)
    if (match != None and match.group(1) in SKIP_SUBPAGES):
        return None

    url = scheme + '://' + netloc + path

    if (url in SKIP_URLS):
        return None

    return url

# Look for facebook links.
def parseForLinks(url, html):
    # A full parse takes a while, utilize the cache.
    ok, content = cacheFetch(url, LINK_CACHE_DIR)
    if (ok):
        return set(content.split("\n"))

    links = []

    doc = bs4.BeautifulSoup(html, 'html.parser')

    for pageLink in doc.find_all('a'):
        link = str(pageLink.get('href')).strip()
        if (link.startswith('https://www.facebook.com/')):
            link = cleanFacebookURL(link)

            if (link != None):
                links.append(link)

    links = set(links)
    cachePut(url, "\n".join(links), LINK_CACHE_DIR)

    return links

# The seed files are already complete files written to the SEED_DIR dir.
def fetchSeedLinks():
    links = set()

    seedPaths = [os.path.join(SEED_DIR, filename) for filename in os.listdir(SEED_DIR)]

    # Fetch the seeds
    for seedPath in seedPaths:
        html = ''
        with open(seedPath, 'r') as inFile:
            html = inFile.read()

        links |= parseForLinks(seedPath, html)

    return links

def fetchLinks():
    links = set()

    links = fetchSeedLinks()

    newLinks = set()
    linksToFetch = set(links)

    # After a certian number of bad encodes (usually caused by being locked out),
    # we will abandon this run.
    badEncoddingErrors = 0
    done = False

    # Fetch the page of each person in our set and look at their page for other people.
    # We will keep iterating until we stop growing or reach MAX_ITERATIONS.
    # We cache fetches, so we don't have to worry too much about wasting resources.
    for iteration in range(MAX_ITERATIONS):
        print("Iteration %02d -- Total Links: %d, Fetching: %d" % (iteration, len(links), len(linksToFetch)))

        for link in linksToFetch:
            html = ''
            try:
                html = fetch(link)
                sys.stdout.flush()
            except NoEncodingException:
                badEncoddingErrors += 1

                if (badEncoddingErrors == MAX_FAILURE_ENCODING_COUNT):
                    done = True
                    break
            except Exception as ex:
                print("   Error: %s" % (ex))
                continue

            tempLinks = parseForLinks(link, html)
            for tempLink in tempLinks:
                if (tempLink not in links and tempLink not in newLinks):
                    newLinks.add(tempLink)

        if (len(newLinks) == 0):
            break

        links |= newLinks
        linksToFetch = newLinks
        newLinks = set()

        if (done):
            break

    print("Fetched %d links" % (len(links)))

    return links

def main():
    os.makedirs(PAGE_CACHE_DIR, exist_ok = True)

    links = fetchLinks()

if __name__ == '__main__':
    main()

import os
import time
import urllib.error
import urllib.parse
import urllib.request

import brotli

DB_HOST = 'localhost'
DB_NAME = 'facebook'

IMAGE_CACHE_DIR = os.path.join('/', 'media', 'nas', 'data', 'facebook', 'imageCache')
IMAGE_URL_LIST = os.path.join('/', 'media', 'nas', 'data', 'facebook', 'imageCache', '__imageUrls.txt')

WAIT_TIME_MSEC = 1.5 * 1000

# If we get this many errors from the server, then abort.
MAX_ERROR_COUNT = 5

def cachePath(id):
    return os.path.join(IMAGE_CACHE_DIR, id)

def cacheHas(id):
    path = cachePath(id)
    return os.path.isfile(path)

def cacheFetch(id):
    path = cachePath(id)
    if (not os.path.isfile(path)):
        return False, ''

    content = ''
    with open(path, 'rb') as inFile:
        content = inFile.read()

    return True, content

def cachePut(id, content):
    path = cachePath(id)
    os.makedirs(os.path.dirname(path), exist_ok = True)

    with open(path, 'wb') as outFile:
        outFile.write(content)

def fetch(id, url):
    if (cacheHas(id)):
        return True

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
        content = None
        with urllib.request.urlopen(request) as response:
            fetch.lastFetch = int(round(time.time() * 1000))

            if (response.status != 200):
                print("   FAILED to fetch. Code: %d, Reason: %s." % (response.status, response.reason))
                return ''

            # Check the encoding.
            # Facebook always sends content compressed in brotli.
            if (response.getheader('content-encoding') == 'br'):
                content = brotli.decompress(response.read())
            else:
                content = response.read()

            if (response.getheader('content-type') != 'image/jpeg'):
                print("   ERROR: Unknown content type: '%s'" % (response.getheader('content-type')))

            cachePut(id, content)

            print('   Success')
    except urllib.error.HTTPError as ex:
        # This is probably because of privacy settings.
        # Write an empty file so we don't try to fetch it again.
        if (ex.code == 404):
            cachePut(id, b'')
            print('   404')
        else:
            raise ex

    return content

def getConnectionString():
    return "host='%s' dbname='%s" % (DB_HOST, DB_NAME)

# [[id, url], ...]
def getImageURLs():
    info = []

    lines = []
    with open(IMAGE_URL_LIST, 'r') as inFile:
        lines = inFile.readlines()

    for line in lines:
        parts = line.strip().split("\t", 1)
        info.append(parts)

    return info

def main():
    errorCount = 0

    os.makedirs(IMAGE_CACHE_DIR, exist_ok = True)
    urls = getImageURLs()

    print("Got %d image urls" % (len(urls)))

    for url in urls:
        try:
            fetch(url[0], url[1])
        except Exception as ex:
            print("Error: %s" % (ex))

            errorCount += 1
            if (errorCount >= MAX_ERROR_COUNT):
                break

if __name__ == '__main__':
    main()

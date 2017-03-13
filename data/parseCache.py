# Parse the page cache from the scraper and compile all the information into SQL statements.

import json
import os
import re

import bs4

PAGE_SIZE = 1000
OUTPUT_DIR = 'parsed'
OUTPUT_FILENAME_BASE = 'parsedEntities'

# CACHE_DIR = 'tempCache'
CACHE_DIR = os.path.join('/', 'media', 'temp', 'temp', 'facebook', 'cache')

# CSS selector information.
USERNAME_CLASS = '_8_2'
PROFILE_PIC_CLASS = 'profilePic'
ABOUT_ID = 'pagelet_timeline_medley_about'
ABOUT_INNER_ID = 'collection_wrapper_2327158227'

EDU_WORK_ID = 'pagelet_eduwork'
LIVES_ID = 'pagelet_hometown'

EDU_WORK_LOCATION_CLASS = '_2lzr _50f5 _50f7'
EDU_WORK_POSITION_CLASS = '_173e _50f8 _50f3'

CITY_ID_CLASS = '_50f5 _50f7'
CITY_RELATION_CLASS = 'fsm fwn fcg'

INFO_NAME = 'name'
# Note that this may be text of numeric.
INFO_ID = 'id'
INFO_IS_PAGE = 'isPage'
INFO_PIC = 'image'
INFO_WORK = 'work'
INFO_EDUCATION = 'education'
INFO_POSITION = 'position'
INFO_LIVES = 'lives'

UNICODE_DOT = '\\xc2\\xb7'

def parseIdFromLink(link):
    id = link.strip().replace('https://www.facebook.com/', '').strip('/')
    if (not id.startswith('pages/')):
        return id, False

    # If it looks like we are a page, just take the very last item (separated by '/').
    # Usually it is the numeric identifier.
    return id.split('/')[-1].strip(), True

def parseSection(div, idClasss = EDU_WORK_LOCATION_CLASS, positionClass = EDU_WORK_POSITION_CLASS):
    rtn = []

    for liItem in div.ul.children:
        liLink = liItem.find(class_ = idClasss).a

        item = {}
        id, isPage = parseIdFromLink(liLink.get('href'))

        item[INFO_ID] = id
        item[INFO_NAME] = liLink.get_text()
        item[INFO_IS_PAGE] = isPage

        positionText = None

        # Some people don't list their specific position.
        if (liItem.find(class_ = positionClass) != None):
            positionText = liItem.find(class_ = positionClass).get_text()
            # The text of the location is listed again after the potition.
            # We only care about the position.
            positionText = positionText.split(UNICODE_DOT)[0].strip()

        item[INFO_POSITION] = positionText

        rtn.append(item)

    return rtn

def parsePage(path):
    info = {}

    doc = None
    with open(path, 'r') as inFile:
        html = inFile.read()

        if (html == '404'):
            return None

        doc = bs4.BeautifulSoup(html, 'html.parser')

    userNameInfo = doc.find('a', class_ = USERNAME_CLASS)

    # If we cannot get the id, then just abandon this page.
    if (userNameInfo == None):
        # print("Failed to get id for: %s" % (path))
        return None
        
    info[INFO_NAME] = userNameInfo.span.get_text()
    id, isPage = parseIdFromLink(userNameInfo.get('href'))

    info[INFO_ID] = id
    info[INFO_IS_PAGE] = isPage

    # Check for a profile pic.
    profilePic = doc.find('img', class_ = PROFILE_PIC_CLASS)

    profilePicURL = None
    if (profilePic):
        profilePicURL = profilePic.get('src')
    info[INFO_PIC] = profilePicURL

    aboutInfo = doc.find(id = ABOUT_ID)

    # If the user does not have an about section, then we are done with just the id.
    if (aboutInfo == None):
        return info

    # Go into the info more.
    aboutInfo = aboutInfo.find(id = ABOUT_INNER_ID)

    eduWorkInfo = aboutInfo.find(id = EDU_WORK_ID)
    if (eduWorkInfo != None):
        workInfo = eduWorkInfo.find('div', attrs = {'data-pnref': 'work'})
        if (workInfo != None):
            info[INFO_WORK] = parseSection(workInfo)

        eduInfo = eduWorkInfo.find('div', attrs = {'data-pnref': 'edu'})
        if (eduInfo != None):
            info[INFO_EDUCATION] = parseSection(eduInfo)

    livesInfo = aboutInfo.find(id = LIVES_ID)
    if (livesInfo != None):
        info[INFO_LIVES] = parseSection(livesInfo.div, CITY_ID_CLASS, CITY_RELATION_CLASS)

    return cleanInfo(info)

def cleanInfo(info):
    # Make a lambda for use in re.sub() that replaces hex strings with their unicode equalents.
    if (not hasattr(cleanInfo, 'hexDecodeLambda')):
        cleanInfo.hexDecodeLambda = lambda match: bytes.fromhex(match[0].replace('\\x', '')).decode('utf-8')

    # Decode any unicode.
    for key in info:
        val = info[key]

        if (type(val) is dict):
            info[key] = cleanInfo(val)
        if (type(val) is list):
            for i in range(len(val)):
                info[key][i] = cleanInfo(val[i])
        elif (type(val) is str):
            info[key] = re.sub(r'(\\x[0-9a-f][0-9a-f])+', cleanInfo.hexDecodeLambda, val)
            
    return info

def parseCache(cachePath):
    totalCount = 0
    successCount = 0

    page = 0
    infos = []

    os.makedirs(OUTPUT_DIR, exist_ok = True)

    for dirPath, dirNames, filenames in os.walk(cachePath):
        for filename in filenames:
            totalCount += 1

            info = None
            try:
                info = parsePage(os.path.join(dirPath, filename))
            except Exception as ex:
                print("Failed to parse %s: %s" % (filename, ex))

            if (info == None):
                continue

            successCount += 1
            infos.append(info)

            if (len(infos) == PAGE_SIZE):
                outputPath = os.path.join(OUTPUT_DIR, "%s_%05d.json" % (OUTPUT_FILENAME_BASE, page))
                page += 1

                with open(outputPath, 'w') as outFile:
                    outFile.write(json.dumps(infos))
                    outFile.write("\n")
                    infos.clear()

    print("Successful info for %d / %d" % (successCount, totalCount))

def main():
    parseCache(CACHE_DIR)

    '''
    info = parsePage('tempCache/www.facebook.com/eriq.augustine.html')
    print(info)

    info = parsePage('tempCache/www.facebook.com/erachael.html')
    print(info)

    info = parsePage('tempCache/www.facebook.com/eric.bluestein.9.html')
    print(info)
    '''

if __name__ == '__main__':
    main()

# Look at all the images in the image cache and base64 encode them.

import base64
import os

IMAGE_CACHE_DIR = os.path.join('/', 'media', 'nas', 'data', 'facebook', 'imageCache')
IMAGE_URL_LIST_FILENAME = '__imageUrls.txt'
INSERT_PATH = os.path.join('sql', 'insert-images.sql')

FORMAT_STRING = 'string'
FORMAT_INT = 'int'
FORMAT_BOOL = 'bool'

FAKE_NAME = '!@#$__FAKE_NAME__@!#$'

# Convert everything to a string that would be sutible to put in an INSERT.
# Will escape and qupte strings.
def sqlFormat(text, formatType = FORMAT_STRING):
    if (text == None):
        return 'NULL'

    if (formatType == FORMAT_INT):
        return str(text)

    if (formatType == FORMAT_BOOL):
        return str(text).upper()

    # String
    return "'" + text.replace("'", "''") + "'"

def encodeImage(path):
    with open(path, "rb") as inFile:
        base64String = base64.b64encode(inFile.read()).decode("ascii")

    return base64String

def writeInsert(images, altImages):
    # We are actually doing only updates, but it is more efficient to do it as an upsert.
    with open(INSERT_PATH, 'w') as outFile:
        outFile.write("INSERT INTO Entities\n")
        outFile.write("   (name, facebookId, imageBase64)\n")
        outFile.write("VALUES\n")
        outFile.write(",\n".join(["   " + row for row in images]) + "\n")
        outFile.write("ON CONFLICT ON CONSTRAINT UQ_Entities_facebookId DO UPDATE SET imageBase64 = Excluded.imageBase64\n")
        outFile.write(";\n")

        outFile.write("INSERT INTO Entities\n")
        outFile.write("   (name, facebookId, imageBase64)\n")
        outFile.write("VALUES\n")
        outFile.write(",\n".join(["   " + row for row in altImages]) + "\n")
        outFile.write("ON CONFLICT ON CONSTRAINT UQ_Entities_facebookId DO UPDATE SET imageBase64 = Excluded.imageBase64\n")
        outFile.write(";\n")

        # Just incase, ensure that no actual inserts got through.# Just incase, ensure that no actual inserts got through.
        outFile.write("DELETE FROM Entities WHERE name = %s;\n" % (sqlFormat(FAKE_NAME)))

def main():
    images = []
    altImages = []

    for dirPath, dirNames, filenames in os.walk(IMAGE_CACHE_DIR):
        for filename in filenames:
            if (filename == IMAGE_URL_LIST_FILENAME):
                continue

            path = os.path.join(dirPath, filename)
            facebookId = path.replace(IMAGE_CACHE_DIR, '').lstrip('/')

            images.append("(%s, %s, %s)" % (
                sqlFormat(FAKE_NAME),
                sqlFormat(facebookId),
                sqlFormat(encodeImage(path))
            ))

            # Some facebook ids are a little different.
            if (facebookId != filename):
                altImages.append("(%s, %s, %s)" % (
                    sqlFormat(FAKE_NAME),
                    sqlFormat(filename),
                    sqlFormat(encodeImage(path))
                ))

    writeInsert(images, altImages)

if __name__ == '__main__':
    main()

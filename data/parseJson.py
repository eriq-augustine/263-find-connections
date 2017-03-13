# This assumes that we will not run into memory issues.

import json
import os

INSERT_PATH = os.path.join('sql', 'insert.sql')
CACHE_DIR = 'parsed'

INFO_NAME = 'name'
INFO_ID = 'id'
INFO_IS_PAGE = 'isPage'
INFO_PIC = 'image'
INFO_WORK = 'work'
INFO_EDUCATION = 'education'
INFO_POSITION = 'position'
INFO_LIVES = 'lives'

FORMAT_STRING = 'string'
FORMAT_INT = 'int'
FORMAT_BOOL = 'bool'

BAD_START = 'https://l.facebook.com/'

# TODO(eriq): I am concerned about conflicts beteen company names from the real page and from the links.

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

def writeInserts(fullEntityRows, partialEntityRows, educationRows, workRows, livedRows):
    with open(INSERT_PATH, 'w') as outFile:
        # Entities
        outFile.write("INSERT INTO Entities\n")
        outFile.write("   (facebookId, name, isPage, imageUrl)\n")
        outFile.write("VALUES\n")
        outFile.write(",\n".join(["   " + row for row in fullEntityRows]) + "\n")
        outFile.write("ON CONFLICT DO NOTHING\n")
        outFile.write(";\n")

        outFile.write("INSERT INTO Entities\n")
        outFile.write("   (facebookId, name, isPage)\n")
        outFile.write("VALUES\n")
        outFile.write(",\n".join(["   " + row for row in partialEntityRows]) + "\n")
        outFile.write("ON CONFLICT DO NOTHING\n")
        outFile.write(";\n")

        # Education
        outFile.write("INSERT INTO Education\n")
        outFile.write("   (userFacebookId, schoolFacebookId, position)\n")
        outFile.write("VALUES\n")
        outFile.write(",\n".join(["   " + row for row in educationRows]) + "\n")
        outFile.write("ON CONFLICT DO NOTHING\n")
        outFile.write(";\n")

        # Work
        outFile.write("INSERT INTO Employment\n")
        outFile.write("   (userFacebookId, workFacebookId, position)\n")
        outFile.write("VALUES\n")
        outFile.write(",\n".join(["   " + row for row in workRows]) + "\n")
        outFile.write("ON CONFLICT DO NOTHING\n")
        outFile.write(";\n")

        # Lived
        outFile.write("INSERT INTO Lived\n")
        outFile.write("   (userFacebookId, placeFacebookId, position)\n")
        outFile.write("VALUES\n")
        outFile.write(",\n".join(["   " + row for row in livedRows]) + "\n")
        outFile.write("ON CONFLICT DO NOTHING\n")
        outFile.write(";\n")

        # Special inserts for Eriq Augustine.
        # These are factual, but just don't appead on the public page.
        insert = '''
            INSERT INTO Education
                (userFacebookId, schoolFacebookId, position)
            VALUES
                ('eriq.augustine', '110030499019521', 'Student'),
                ('eriq.augustine', '107658532597137', 'Student'),
                ('eriq.augustine', '109828372368206', 'Student'),
                ('eriq.augustine', '155506624638636', 'Student'),
                ('eriq.augustine', 'CaliforniaPolytechnic', 'Student')
            ON CONFLICT DO NOTHING
            ;
        '''
        outFile.write(insert)

        insert = '''
            INSERT INTO Employment
                (userFacebookId, workFacebookId, position)
            VALUES
                ('eriq.augustine', '213223275359974', 'Developer'),
                ('eriq.augustine', '110030499019521', 'Developer'),
                ('eriq.augustine', '107658532597137', 'Lecturer'),
                ('eriq.augustine', '155506624638636', 'Lecturer'),
                ('eriq.augustine', '110331765661622', 'Developer'),
                ('eriq.augustine', '666909180067072', 'Developer'),
                ('eriq.augustine', 'CaliforniaPolytechnic', 'Lecturer'),
                ('eriq.augustine', 'netflixus', 'Developer')
            ON CONFLICT DO NOTHING
            ;
        '''
        outFile.write(insert)

        insert = '''
            INSERT INTO Lived
                (userFacebookId, placeFacebookId, position)
            VALUES
                ('eriq.augustine', '106277849402612', 'Lived'),
                ('eriq.augustine', '109650795719651', 'Hometown'),
                ('eriq.augustine', '113468615330042', 'Lived')
            ON CONFLICT DO NOTHING
            ;
        '''
        outFile.write(insert)

def parseFile(path):
    text = ''
    with open(path, 'r') as inFile:
        text = inFile.read()

    records = json.loads(text)

    fullEntityRows = []
    partialEntityRows = []
    educationRows = []
    workRows = []
    livedRows = []

    for record in records:
        if (record[INFO_ID].startswith(BAD_START)):
            continue

        # facebookId, name, isPage, imageUrl
        fullEntityRows.append("(%s, %s, %s, %s)" % (
            sqlFormat(record[INFO_ID]),
            sqlFormat(record[INFO_NAME]),
            sqlFormat(record[INFO_IS_PAGE], FORMAT_BOOL),
            sqlFormat(record[INFO_PIC])))

        if (INFO_EDUCATION in record):
            for education in record[INFO_EDUCATION]:
                if (education[INFO_ID].startswith(BAD_START)):
                    continue

                # facebookId, name, isPage
                partialEntityRows.append("(%s, %s, %s)" % (
                    sqlFormat(education[INFO_ID]),
                    sqlFormat(education[INFO_NAME]),
                    sqlFormat(education[INFO_IS_PAGE], FORMAT_BOOL)
                ))

                # userFacebookId, schoolFacebookId, position
                educationRows.append("(%s, %s, %s)" % (
                    sqlFormat(record[INFO_ID]),
                    sqlFormat(education[INFO_ID]),
                    sqlFormat(education[INFO_POSITION])
                ))

        if (INFO_WORK in record):
            for work in record[INFO_WORK]:
                if (work[INFO_ID].startswith(BAD_START)):
                    continue

                # facebookId, name, isPage
                partialEntityRows.append("(%s, %s, %s)" % (
                    sqlFormat(work[INFO_ID]),
                    sqlFormat(work[INFO_NAME]),
                    sqlFormat(work[INFO_IS_PAGE], FORMAT_BOOL)
                ))

                # userFacebookId, workFacebookId, position
                workRows.append("(%s, %s, %s)" % (
                    sqlFormat(record[INFO_ID]),
                    sqlFormat(work[INFO_ID]),
                    sqlFormat(work[INFO_POSITION])
                ))

        if (INFO_LIVES in record):
            for place in record[INFO_LIVES]:
                if (place[INFO_ID].startswith(BAD_START)):
                    continue

                # facebookId, name, isPage
                partialEntityRows.append("(%s, %s, %s)" % (
                    sqlFormat(place[INFO_ID]),
                    sqlFormat(place[INFO_NAME]),
                    sqlFormat(place[INFO_IS_PAGE], FORMAT_BOOL)
                ))

                # userFacebookId, placeFacebookId, position
                livedRows.append("(%s, %s, %s)" % (
                    sqlFormat(record[INFO_ID]),
                    sqlFormat(place[INFO_ID]),
                    sqlFormat(place[INFO_POSITION])
                ))

    return fullEntityRows, partialEntityRows, educationRows, workRows, livedRows

def main():
    fullEntityRows = set()
    partialEntityRows = set()
    educationRows = set()
    workRows = set()
    livedRows = set()

    for filename in os.listdir(CACHE_DIR):
        newFullEntityRows, newPartialEntityRows, newEducationRows, newWorkRows, newLivedRows = parseFile(os.path.join(CACHE_DIR, filename))

        fullEntityRows |= set(newFullEntityRows)
        partialEntityRows |= set(newPartialEntityRows)
        educationRows |= set(newEducationRows)
        workRows |= set(newWorkRows)
        livedRows |= set(newLivedRows)

    writeInserts(fullEntityRows, partialEntityRows, educationRows, workRows, livedRows)

if __name__ == '__main__':
    main()

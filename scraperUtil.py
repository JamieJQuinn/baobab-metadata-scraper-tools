import os.path
import sys
import json
from bs4 import BeautifulSoup
from pymarc import Record, Field, XMLWriter
import urllib
import urllib2
import subprocess

def getParsedHTML(url):
    try:
        url = urllib2.urlopen(url)
    except:
        print "Error: Cannot open url "+url
    try:
        html = url.read()
    except:
        print "Error: url could not be read: "+url
    url.close()
    try:
        parsed_html = BeautifulSoup(html, "html.parser")
    except:
        print "Error: Cannot parse html for url "+url
    return parsed_html

def createJSONFileIfNotPresent(filename, defaultJson=[]):
    if not os.path.isfile(filename):
        with open(filename, 'w') as fp:
            json.dump(defaultJson, fp)

def getUUID(string):
    uuid = subprocess.check_output(["/usr/local/baobab/bin/key_to_uuid.sh", string]).split()[0]
    return uuid

def saveBookFileAndMetadata(url, MARCMapping, getMetadata, saveLocation, debug=False):
    metadata = getMetadata(url)
    if u'downloadURL' in metadata:
        if os.path.isfile(saveLocation+metadata['UUID']+".xml"):
            print "Error: clean list hasn't worked"
            return
        if debug:
            print "Downloading "+ metadata[u'downloadURL']
        try:
            urllib.urlretrieve(metadata[u'downloadURL'], saveLocation + metadata['UUID'] + '.' + metadata[u'downloadURL'].rsplit('.')[-1])
        except:
            print "Error: Cannot download book file at "+metadata[u'downloadURL']
        writeMetadataToMarc(metadata, MARCMapping, saveLocation)

def writeRecordToFile(record, filename):
    try:
        writer = XMLWriter(open(filename, 'wb'))
        writer.write(record)
    except:
        print "Error: Cannot write metadata to "+filename
    writer.close()  # Important!

def writeMetadataToMarc(data, MARCMapping, saveLocation):
    record = Record()
    for key in data:
        if key in MARCMapping:
            if(key == u'UUID'):
                field = Field(
                    tag = MARCMapping[key],
                    data = data[key])
            else:
		field = Field(
			tag = MARCMapping[key][:3],
			subfields = [MARCMapping[key][3], data[key]],
			indicators=['0', '0'])  
            record.add_field(field)
    writeRecordToFile(record, filename)


def getAllUrls(pagesToIndex, getUrlsFromPage, debug=False):
    urls = []
    for pageNumber in xrange(0, pagesToIndex):
        if debug:
            print "Page ("+str(pageNumber)+"/"+str(pagesToIndex)+")"
        urls += getUrlsFromPage(pageNumber)
    if debug:
        print '\n'.join(urls)
    return urls

def saveJSON(data, filename):
    try:
        with open(filename, 'wb') as fp:
            json.dump(data, fp)
    except:
        print "Error: Cannot save json to "+filename

def scrape(saveLocation, MARCMapping, getNumberIndexPages, getUrlsFromPage, getMetadata, debug=False):
    if debug:
        print "WARNING: DEBUG"

    cleanListFile = saveLocation+'/.state/CleanUrlList.json' # List of URLs already processed
    if not os.path.exists(saveLocation+'/.state/'):
                os.makedirs(saveLocation+'/.state/')

    # Load existing lists
    createJSONFileIfNotPresent(cleanListFile)
    with open(cleanListFile, 'r') as fp:
        cleanUrls = json.load(fp)

    try:
        numberIndexPages = getNumberIndexPages(debug=debug)
    except: 
        print "Error: Cannot get number of index pages"
    print "SCRAPING " + str(numberIndexPages) + " PAGES FOR BOOK URLS"
    try:
        allUrls = getAllUrls(numberIndexPages, getUrlsFromPage, debug=debug)
    except:
        print "Error: Cannot get urls"
    dirtyUrls = [url for url in allUrls if url not in cleanUrls]
    print "SCRAPING "+ str(len(dirtyUrls)) + " BOOKS"
    for i, url in enumerate(dirtyUrls):
        if debug:
            print "Scraping " + url
        try:
            saveBookFileAndMetadata(url, MARCMapping, getMetadata, saveLocation, debug=debug)
        except:
            print "Error: Cannot save book + metadata from "+url
        cleanUrls.append(url)
        if(i%10):
            saveJSON(cleanUrls, cleanListFile)
    saveJSON(cleanUrls, cleanListFile)

import os.path
import sys
import json
from bs4 import BeautifulSoup
from pymarc import Record, Field, XMLWriter
import urllib
import urllib2

def getParsedHTML(url):
    url = urllib2.urlopen(url)
    html = url.read()
    url.close()
    return BeautifulSoup(html, "html.parser")

def createJSONFileIfNotPresent(filename):
    if not os.path.isfile(filename):
        with open(filename, 'w') as fp:
            json.dump([], fp)

def saveBookFileAndMetadata(url, MARCMapping, getMetadata, saveLocation, debug=False):
    metadata = getMetadata(url)
    if u'downloadURL' in metadata:
        if debug:
            print "Downloading "+ metadata[u'downloadURL']
        urllib.urlretrieve(metadata[u'downloadURL'], saveLocation + metadata['UUID'] + '.' + url.rsplit('.')[-1])
        writeMetadataToMarc(metadata, MARCMapping, saveLocation)

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
    writer = XMLWriter(open(saveLocation + data[u'UUID'] + '.xml', 'wb'))
    writer.write(record)
    writer.close()  # Important!

def getAllUrls(pagesToIndex, getUrlsFromPage, debug=False):
    urls = []
    for pageNumber in xrange(0, pagesToIndex):
        if debug:
            print "Page ("+str(pageNumber)+"/"+str(pagesToIndex)+")"
        urls += getUrlsFromPage(pageNumber)
    if debug:
        print '\n'.join(urls)
    return urls

def scrape(saveLocation, MARCMapping, getNumberIndexPages, getUrlsFromPage, getMetadata):
    debug = True
    if debug:
        print "WARNING: DEBUG"

    cleanListFile = saveLocation+'/.state/CleanUrlList.json' # List of URLs already processed
    if not os.path.exists(saveLocation+'/.state/'):
                os.makedirs(saveLocation+'/.state/')

    # Load existing lists
    createJSONFileIfNotPresent(cleanListFile)
    with open(cleanListFile, 'r') as fp:
        cleanUrls = json.load(fp)

    numberIndexPages = getNumberIndexPages(debug=debug)
    print "SCRAPING " + str(numberIndexPages) + " PAGES FOR BOOK URLS"
    allUrls = getAllUrls(numberIndexPages, getUrlsFromPage, debug=debug)
    dirtyUrls = [url for url in allUrls if url not in cleanUrls]
    print "SCRAPING "+ str(len(dirtyUrls)) + " BOOKS"
    for url in dirtyUrls:
        if debug:
            print "Scraping " + url
        saveBookFileAndMetadata(url, MARCMapping, getMetadata, saveLocation, debug=debug)
        cleanUrls.append(url)

    # Save clean file
    with open(cleanListFile, 'wb') as fp:
        json.dump(cleanUrls, fp)

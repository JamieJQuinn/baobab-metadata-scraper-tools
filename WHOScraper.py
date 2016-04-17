import urllib2
import urllib
from bs4 import BeautifulSoup
from pymarc import Record, Field, XMLWriter
import json
import os.path
import sys
import uuid

DEBUG = False

numItemsPerPage = 1000

# Change to ftpdownloads when needed
SAVE_LOCATION='/ftpdownloads/who/'

def getParsedHTML(url):
    url = urllib2.urlopen(url)
    html = url.read()
    url.close()
    return BeautifulSoup(html)

# This keeps up with the total number of index pages at http://www.ilo.org/global/publications/books/lang--en/index.htm
frontPage = getParsedHTML("http://apps.who.int/iris/simple-search?query=")
numItems = int(frontPage.find('div', attrs={'class':'discovery-result-pagination'}).find('div', attrs={'class':'alert-info'}).string.split(' ')[3][:-1])

if DEBUG:
	numItems = 20

if not os.path.exists(SAVE_LOCATION+'/.state/'):
	    os.makedirs(SAVE_LOCATION+'/.state/')
cleanListFile = SAVE_LOCATION+'/.state/CleanUrlList.json' # List of URLs already processed
errorListFile = SAVE_LOCATION+'/.state/ErrorUrlList.json' # List of URLs that cause problems

downloadLocation =SAVE_LOCATION

# create the clean list file if it doesn't exist
if not os.path.isfile(cleanListFile):
    with open(cleanListFile, 'w') as fp:
        json.dump([], fp)

# create the error list file if it doesn't exist
if not os.path.isfile(errorListFile):
    with open(errorListFile, 'w') as fp:
        json.dump([], fp)

## SCRAPE FOR BOOK URLS ##

incomingUrlList = []

# Scrape url list from ILO puplication list
print "SCRAPING " + str(int(numItems/float(numItemsPerPage))+1) + " PAGES FOR BOOK URLS"
for i in xrange(0, numItems, numItemsPerPage):
    print str((float(i)/numItems)*100) + "% complete" # Print percentage complete
    print "http://apps.who.int/iris/simple-search?query=&sort_by=score&order=desc&rpp="+str(numItemsPerPage)+"&etal=0&start="+str(i)
    parsed_html = getParsedHTML("http://apps.who.int/iris/simple-search?query=&sort_by=score&order=desc&rpp="+str(numItemsPerPage)+"&etal=0&start="+str(i))
	# Get specific list of book results
    aList = parsed_html.find_all('a', attrs={'class':'list-results'})
    for a in aList:
		# Scrape for urls
	incomingUrlList.append('http://apps.who.int' + a['href'])

# Check scraped list against urls for books that have already been scraped for metadata
with open(cleanListFile) as fp:
    cleanUrlList = json.load(fp)
with open(errorListFile) as fp:
    errorUrlList = json.load(fp)

if DEBUG:
	print "INCOMING LIST:"
	print "\n".join(incomingUrlList)
	print "CLEAN LIST:"
	print "\n".join(cleanUrlList)

dirtyUrlList = []
# If book already scraped, delete
for i, url in enumerate(incomingUrlList):
    if url not in cleanUrlList and url not in errorUrlList:
        dirtyUrlList.append(url)

## GET BOOK METADATA ##

bookMetaData = []

print "SCRAPING " + str(len(dirtyUrlList)) + " URLS FOR BOOK METADATA"
for i, url in enumerate(dirtyUrlList):
	print str(float(i)/len(dirtyUrlList)*100) + "% complete"
    # parse book html page
	parsed_html = getParsedHTML(url)
	metaTemp = {}
	try:
		# Get publication metadata
		trList = parsed_html.find(class_="table itemDisplayTable").find_all('tr')
		# Sort metadata
		for tr in trList:
			metaTemp[tr.find(class_="metadataFieldLabel").string[:-2].lower()] = tr.find(class_="metadataFieldValue").string
		# Get PDF download link if it exists
		aPdf = parsed_html.find('td', headers='t0', class_="standard").a
		if (aPdf):
			metaTemp[u'downloadURL'] = 'http://apps.who.int' + aPdf['href']
		# Record where all this data came from
		metaTemp[u'originURL'] = url
	except:
        # If there's an error, put it in error list
		errorUrlList.append(url)
	else:
        # if there's no error, save metadata
		bookMetaData.append(metaTemp)

# Save error file
with open(errorListFile, 'wb') as fp:
    json.dump(errorUrlList, fp)

## DOWNLOAD BOOKS ## 

downloadable = []
# Select books that are downloadable
for data in bookMetaData:
    if "downloadURL" in data:
        data[u'UUID'] = str(uuid.uuid1())
        downloadable.append(data)
    else:
	cleanUrlList.append(data[u'originURL'])

# Mapping for writing the marc records
MARCMapping = {u'UUID':'001', 
               u'title':'245a', 
               u'authors':'100a', 
               u'issue date':'260c',
               u'publisher':'260b',
	       u'place of publication':'260a',
	       u'language':'041a',
	       u'issn':'022a'
	       }

print "DOWNLOADING " + str(len(downloadable)) + " BOOKS"
for i, data in enumerate(downloadable):
    print str(float(i)/len(downloadable)*100) + "% complete"
	# Get PDF
    url = data['downloadURL']
    urllib.urlretrieve(url, downloadLocation + data['UUID'] + '.' + url.rsplit('.')[-1])
	# Print metadata in MARCXML
    record = Record()
    for key in data:
        if key in MARCMapping:
            if(key == u'UUID'):
                field = Field(
                    tag = MARCMapping[key],
                    data = data[key])
            else:
		if DEBUG:
			print key, data[key]
		field = Field(
			tag = MARCMapping[key][:3],
			subfields = [MARCMapping[key][3], data[key]],
			indicators=['0', '0'])  
            record.add_field(field)
    writer = XMLWriter(open(downloadLocation + data[u'UUID'] + '.xml', 'wb'))
    writer.write(record)
    writer.close()  # Important!
    cleanUrlList.append(data[u'originURL'])


# Save clean file
with open(cleanListFile, 'wb') as fp:
    json.dump(cleanUrlList, fp)

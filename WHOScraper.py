import urllib2
import urllib
from bs4 import BeautifulSoup
from pymarc import Record, Field, XMLWriter
import json
import os.path
import sys
import uuid

def getParsedHTML(url):
    url = urllib2.urlopen(url)
    html = url.read()
    url.close()
    return BeautifulSoup(html)

def createJSONFileIfNotPresent(filename):
    if not os.path.isfile(filename):
        with open(filename, 'w') as fp:
            json.dump([], fp)

numItemsPerPage = 1000

SAVE_LOCATION='/ftpdownloads/who'

cleanListFile = SAVE_LOCATION+'/.state/CleanUrlList.json' # List of URLs already processed
errorListFile = SAVE_LOCATION+'/.state/ErrorUrlList.json' # List of URLs that cause problems
allUrlListFile = SAVE_LOCATION+'/.state/allUrlList.json' # List of book/report page URLs that we already have (though perhaps not processed)

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

if not os.path.exists(SAVE_LOCATION+'/.state/'):
	    os.makedirs(SAVE_LOCATION+'/.state/')

createJSONFileIfNotPresent(cleanListFile)
createJSONFileIfNotPresent(errorListFile)
createJSONFileIfNotPresent(allUrlListFile)

# Load existing error lists
with open(cleanListFile, 'r') as fp:
	cleanUrlList = json.load(fp)
with open(errorListFile, 'r') as fp:
	errorUrlList = json.load(fp)
with open(allUrlListFile, 'r') as fp:
	allUrlList = json.load(fp)

# This keeps up with the total number of index results 
frontPage = getParsedHTML("http://apps.who.int/iris/simple-search?query=")
numItems = int(frontPage.find('div', attrs={'class':'discovery-result-pagination'}).find('div', attrs={'class':'alert-info'}).string.split(' ')[3][:-1])

numUrlsOnFile = len(allUrlList)

## SCRAPE FOR BOOK URLS ##
dirtyUrlList = []
# Scrape url list from ILO puplication list
print "SCRAPING " + str(int((numItems-numUrlsOnFile)/float(numItemsPerPage))+1) + " PAGES FOR BOOK URLS"
for i in xrange(numUrlsOnFile, numItems, numItemsPerPage):
	print str((float(i)/numItems)*100) + "% complete" # Print percentage complete
	# parse index page
	parsed_html = getParsedHTML("http://apps.who.int/iris/simple-search?query=&sort_by=score&order=ASC&rpp="+str(numItemsPerPage)+"&etal=0&start="+str(i))
	# grab all list results
	aList = parsed_html.find_all('a', attrs={'class':'list-results'})
	if len(aList) != 1000:
		print "http://apps.who.int/iris/simple-search?query=&sort_by=score&order=ASC&rpp="+str(numItemsPerPage)+"&etal=0&start="+str(i), len(aList)
	# add book page urls to list
	for a in aList:
		url = 'http://apps.who.int' + a['href']
		if url not in allUrlList:
			allUrlList.append(url)
		# if url not been processed, add to dirty list
		if url not in cleanUrlList and url not in errorUrlList:
			dirtyUrlList.append(url)
	with open(allUrlListFile, 'w') as fp:
		json.dump(allUrlList, fp)

## DOWNLOAD BOOK + BOOK METADATA ##
print "SCRAPING " + str(len(dirtyUrlList)) + " URLS FOR BOOKS"
for i, url in enumerate(dirtyUrlList):
	print str(float(i)/len(dirtyUrlList)*100) + "% complete"
	data = {}
	try:
		# parse book html page
		parsed_html = getParsedHTML(url)
		# Get raw publication metadata
		trList = parsed_html.find(class_="table itemDisplayTable").find_all('tr')
		# Sort metadata
		for tr in trList:
			data[tr.find(class_="metadataFieldLabel").string[:-2].lower()] = tr.find(class_="metadataFieldValue").string
		# Record where all this data came from
		data[u'originURL'] = url
		# If the pdf link exists, download book and print metadata
		aPdf = parsed_html.find('td', headers='t0', class_="standard").a
		if (aPdf):
			# Get PDF
			pdfUrl = 'http://apps.who.int' + aPdf['href']
			urllib.urlretrieve(pdfUrl, SAVE_LOCATION + data['UUID'] + '.' + url.rsplit('.')[-1])
			# Print metadata in MARCXML
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
			writer = XMLWriter(open(SAVE_LOCATION + data[u'UUID'] + '.xml', 'wb'))
			writer.write(record)
			writer.close() 
	except:
        # If there's an error, put it in error list
		errorUrlList.append(url)
		with open(errorListFile, 'wb') as fp:
			json.dump(errorUrlList, fp)
	else:
        # if there's no error, save metadata
		cleanUrlList.append(url)
		with open(cleanListFile, 'wb') as fp:
			json.dump(cleanUrlList, fp)

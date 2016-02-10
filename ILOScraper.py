
# coding: utf-8

# In[ ]:

import urllib2
import urllib
from bs4 import BeautifulSoup
from pymarc import Record, Field, XMLWriter
import json
import os.path
import sys
import uuid


# In[ ]:

# NEEDS CHANGING TO KEEP UP WITH TOTAL PAGE COUNT AT http://www.ilo.org/global/publications/books/lang--en/index.htm
pagesToIndex = 1


# In[ ]:

cleanListFile = './ilo/.state/ILOCleanUrlList.json' # List of URLs already processed
errorListFile = './ilo/.state/ILOErrorUrlList.json' # List of URLs that cause problems

downloadLocation = './ilo/'


# In[ ]:

def getParsedHTML(url):
    url = urllib2.urlopen(url)
    html = url.read()
    url.close()
    return BeautifulSoup(html)


# In[ ]:

if not os.path.isfile(cleanListFile):
    with open(cleanListFile, 'w') as fp:
        json.dump([], fp)

if not os.path.isfile(errorListFile):
    with open(errorListFile, 'w') as fp:
        json.dump([], fp)


# In[ ]:

incomingUrlList = []

# Scrape url list from ILO puplication list
for i in xrange(0, pagesToIndex*10, 10):
    # print str((float(i)/pagesToIndex)*10) + "% Comlpete" # Print percentage complete
    parsed_html = getParsedHTML("http://www.ilo.org/global/publications/books/lang--en/nextRow--"+str(i)+"/index.htm")
    liList = parsed_html.body.find('div', attrs={'class':'items-list'}).find_all('li')
    for li in liList:
        incomingUrlList.append('http://www.ilo.org' + li.a['href'])

# Check scraped list against urls for books that have already been scraped for metadata
with open(cleanListFile) as fp:
    cleanUrlList = json.load(fp)
with open(errorListFile) as fp:
    errorUrlList = json.load(fp)

dirtyUrlList = []
# If book already scraped, delete
for i, url in enumerate(incomingUrlList):
    if url not in cleanUrlList and url not in errorUrlList:
        dirtyUrlList.append(url)


# In[ ]:

bookMetaData = []

for i, url in enumerate(dirtyUrlList):
    # parse HTML
    parsed_html = getParsedHTML(url)
    metaTemp = {}
    try:
        # If the returned URL actually has data
        if parsed_html.find(class_="page-title"):
            metaTemp[u"title"] = parsed_html.find(class_="page-title").h1.string
            metaTemp[u'desc'] =  parsed_html.find(class_="page-title").p.string
        # Get publication metadata
        pubData = parsed_html.find(class_="pub-data").find_all('tr')
        # Sort metadata
        for tr in pubData:
            metaTemp[tr.th.string[:-2].lower()] = tr.td.string
        # Get PDF download link if it exists
        if (parsed_html.find(id='download')):
            metaTemp[u'downloadURL'] = 'http://www.ilo.org' + parsed_html.find(id='download').a['href']
        # Record where all this data came from
        metaTemp[u'originURL'] = url
        metaTemp[u'publisher'] = 'ILO'
    except:
        # If there's an error, put it in error list
        errorUrlList.append(url)
    else:
        # if there's no error, put the url on the clean list & save metadata
        cleanUrlList.append(url)
        bookMetaData.append(metaTemp)

with open(errorListFile, 'wb') as fp:
    json.dump(errorUrlList, fp)

with open(cleanListFile, 'wb') as fp:
    json.dump(cleanUrlList, fp)


# In[ ]:

downloadable = []
for data in bookMetaData:
    if "downloadURL" in data:
        data[u'UUID'] = str(uuid.uuid1())
        downloadable.append(data)


# In[ ]:

MARCMapping = {u'UUID':'001', 
               u'title':'245$a', 
               u'authors':'100$a', 
               u'date issued':'260$c',
               u'desc':'520$a',
               u'publisher':'260$b',
               u'reference':'020$a'}


for data in downloadable:
    url = data['downloadURL']
    urllib.urlretrieve(url, downloadLocation + data['UUID'] + '.' + url.rsplit('.')[-1])
    record = Record()
    for key in data:
        if key in MARCMapping:
            if(len(MARCMapping[key].split('$')) == 1):
                field = Field(
                    tag = MARCMapping[key].split('$')[0],
                    data = data[key])
            else:
                field = Field(
                    tag = MARCMapping[key].split('$')[0],
                    subfields = [MARCMapping[key].split('$')[1], data[key]],
                    indicators=['0', '0'])  
            record.add_field(field)
    writer = XMLWriter(open(downloadLocation + data[u'UUID'] + '.xml', 'wb'))
    writer.write(record)
    writer.close()  # Important!


# In[ ]:




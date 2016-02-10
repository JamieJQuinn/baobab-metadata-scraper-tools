
# coding: utf-8

# In[1]:

import urllib2
import urllib
from bs4 import BeautifulSoup
import json
import os.path
import sys
import uuid


# In[2]:

dirtyListFile = 'WHODirtyUrlList.json'
cleanListFile = 'WHOCleanUrlList.json'
metaDataFile =  'WHOMetaDataDict.json'


# In[3]:

def getParsedHTML(url):
    url = urllib2.urlopen(url)
    html = url.read()
    url.close()
    return BeautifulSoup(html)


# In[4]:

if not os.path.isfile(cleanListFile):
    with open(cleanListFile, 'w') as fp:
        json.dump([], fp)

if not os.path.isfile(metaDataFile):
    with open(metaDataFile, 'w') as fp:
        json.dump([], fp)


# In[9]:

# Get HTML of list of pubs from WHO puplication list
parsed_html = getParsedHTML("http://apps.who.int/iris/browse?type=dateissued&sort_by=2&order=ASC&rpp=159864&etal=0&submit_browse=Update")


# In[10]:

bookUrlList = []

aList = parsed_html.body.find_all('a', attrs={'class':'list-results'})

#print aList
for a in aList:
    bookUrlList.append('http://apps.who.int' + a['href'])

# Check scraped list against urls for books that have already been scraped for metadata
with open(cleanListFile) as fp:
    cleanUrls = json.load(fp)

dirtyUrlList = []
# If book already scraped, delete
for i, url in enumerate(bookUrlList):
    if url not in cleanUrls:
        dirtyUrlList.append(url)

# Save resulting urls, these must be books we haven't scraped yet
with open(dirtyListFile, 'wb') as fp:
    json.dump(dirtyUrlList, fp)

print len(dirtyUrlList)


# In[ ]:

# Load list of books we haven't scraped yet
with open(dirtyListFile) as fp:
    dirtyUrlList = json.load(fp)
    
cleanUrlList = []
newDirtyUrlList = []
errorUrlList = []

bookMetaData = []

for i, url in enumerate(dirtyUrlList):
    print str(float(i)/len(dirtyUrlList) * 100) + '% complete'
    parsed_html = getParsedHTML(url)
    metaTemp = {}
    try:
        if parsed_html.find(class_="page-title"):
            metaTemp["title"] = parsed_html.find(class_="page-title").h1.string
            metaTemp['desc'] =  parsed_html.find(class_="page-title").p.string
        else:
            print "No title: " + url
        pubData = parsed_html.find(class_="pub-data").find_all('tr')
        for tr in pubData:
            metaTemp[tr.th.string[:-2].lower()] = tr.td.string
        if (parsed_html.find(id='download')):
            metaTemp['downloadURL'] = 'http://www.ilo.org' + parsed_html.find(id='download').a['href']
        else:
            print "No Download: " + url
        metaTemp['originURL'] = url
    except:
        # If there's an error, put it in error list
        errorUrlList.append(url)
        print 'dirty: ' + url
        print "Unexpected error:", sys.exc_info()[0]
    else:
        # if there's no error, put the url on the clean list & save metadata
        cleanUrlList.append(url)
        bookMetaData.append(metaTemp)

with open(dirtyListFile, 'wb') as fp:
    json.dump(newDirtyUrlList, fp)

with open(cleanListFile, 'wb') as fp:
    json.dump(cleanUrlList, fp)

# Load in previous metaData
with open(metaDataFile) as fp:
    prevMetaData = json.load(fp)
# And append new data
with open(metaDataFile, 'w') as fp:
    json.dump(bookMetaData + prevMetaData, fp)


# In[ ]:

with open(metaDataFile) as fp:
    prevMetaData = json.load(fp)

downloadable = []
for data in prevMetaData:
    if "downloadURL" in data:
        data['UUID'] = str(uuid.uuid1())
        downloadable.append(data)
print len(downloadable)


# In[ ]:

for data in downloadable[:3]:
    url = data['downloadURL']
    urllib.urlretrieve(url, data['UUID'] + '.' + url.rsplit('.')[-1])


from pymarc import Record, Field, XMLWriter
from scraperUtil import getParsedHTML, createJSONFileIfNotPresent, saveBookFileAndMetadata,writeMetadataToMarc, scrape
import os.path
import json
import subprocess

def getNumberIndexPages_ILO(debug=False):
    if debug:
        return 1
    frontPage = getParsedHTML("http://www.ilo.org/global/publications/books/lang--en/index.htm")
    pagesToIndex = int(frontPage.find('aside', attrs={'class':'pagination'}).find('strong').string.split(' ')[2])
    return pagesToIndex

def getUrlsFromPage_ILO(pageNumber):
    parsed_html = getParsedHTML("http://www.ilo.org/global/publications/books/lang--en/nextRow--"+str(pageNumber*10)+"/index.htm")
    liList = parsed_html.body.find('div', attrs={'class':'items-list'}).find_all('li')
    return ['http://www.ilo.org'+li.a['href'] for li in liList]

def getMetadata_ILO(url):
    metadata={}
    parsed_html = getParsedHTML(url)
    # If the returned URL actually has data
    if parsed_html.find(class_="page-title"):
        metadata[u"title"] = parsed_html.find(class_="page-title").h1.string
        metadata[u'desc'] =  parsed_html.find(class_="page-title").p.string
    # Get publication metadata
    pubData = parsed_html.find(class_="pub-data").find_all('tr')
    # Sort metadata into field:data pairs
    for tr in pubData:
        metadata[tr.th.string[:-2].lower()] = tr.td.string
    # Get PDF download link if it exists
    if (parsed_html.find(id='download')):
        metadata[u'downloadURL'] = 'http://www.ilo.org' + parsed_html.find(id='download').a['href']
        uniqueILONumber = metadata[u'downloadURL'].split('/')[-1].split('_')[1].split('.')[0]
        metadata[u'UUID'] = subprocess.check_output(["/usr/local/baobab/bin/key_to_uuid.sh", uniqueILONumber]).split()[0] 
    # Record where all this data came from
    metadata[u'originURL'] = url
    metadata[u'publisher'] = 'ILO'
    return metadata

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

scrape('ilo/', MARCMapping, getNumberIndexPages_ILO, getUrlsFromPage_ILO, getMetadata_ILO)

from pymarc import Record, Field, XMLWriter, parse_xml_to_array
from scraperUtil import writeRecordToFile, getParsedHTML, createJSONFileIfNotPresent
import json
import urllib
import os.path

def getMarcFile(itemStart, itemEnd, xmlFilename):
    # Gets marcxml file for all items from nItemStart (inclusive) to nItemEnd (not inclusive)
    print "Getting records for items " + str(itemStart) + " to " +str(itemEnd)
    url = "http://oldlace.ilo.org/search?jrec="+str(itemStart)+"ln=en&as=1&m1=a&p1=&f1=&op1=a&m2=a&p2=&f2=&op2=a&m3=a&p3=&f3=&year=&year1=&year2=&location=&pl=%2Bedoc%3A%22%25%22+&rm=yt&rg="+str(itemEnd-1)+"&sc=0&of=xm"
    print "from "+url
    urllib.urlretrieve(url, xmlFilename)

def splitMarcFile(marcFilename, saveLocation):
    records = parse_xml_to_array(marcFilename)
    for record in records:
        print "Saving record for " + record.title()
        if '856' in record:
            url = record['856']['u']
            if url.split('.')[-1] == "pdf":
                print "Downloading PDF"
                outputFilename = os.path.join(saveLocation,record['001'].format_field())
                try:
                    urllib.urlretrieve(record['856']['u'], outputFilename+'.pdf')
                except:
                    print "Error: Cannot download pdf file " + url
                try:
                    writeRecordToFile(record, outputFilename+".xml")
                except:
                    print "Error: Cannot write record to "+outputFilename+".xml"
    return len(records)

def getItemCount():
    return 10
    url = "http://oldlace.ilo.org/search?ln=en&p=&f=&action_search=Search&edoc=%25&c=ILO+publications&c=Other+publications"
    html = getParsedHTML(url)
    try:
        countString = html.find('td', attrs={'class':'resultStatsPaging'}).strong.string
    except:
        print "Error: Cannot parse item count html"
    return int(countString.replace(',', ''))

def getPageCount(itemsPerPage, itemCount):
    return int(float(itemCount)/itemsPerPage)+1

def getAllMarcFiles(itemsPerPage, saveLocation, stateFile):
    with open(stateFile, 'r') as fp:
        state = json.load(fp)
        lastItemProcessed = state["lastItemProcessed"]
        print "Last processed item was " + str(lastItemProcessed)

    itemCount = getItemCount()
    for nItem in xrange(lastItemProcessed+1, itemCount+1, itemsPerPage):
        xmlFilename = os.path.join(saveLocation,"temp.xml")
        getMarcFile(nItem, nItem+itemsPerPage, xmlFilename )
        lastItemProcessed += splitMarcFile(xmlFilename ,saveLocation)
        with open(stateFile, 'w') as fp:
            state["lastItemProcessed"] = lastItemProcessed
            json.dump(state, fp)

def main():
    itemsPerPage=10
    saveLocation="ilo"
    stateFile = os.path.join(saveLocation, ".state.json")
    createJSONFileIfNotPresent(stateFile, {"lastItemProcessed":0})
    getAllMarcFiles(itemsPerPage, saveLocation, stateFile)

main()

from pymarc import Record, Field, XMLWriter
import os
import openpyxl
import uuid
import json
import sys

DEBUG = False

def loadMapping(mapFile = ""):
    # Maps the index to the field in the csv file. Eg, if field A or 0 is the publisher, mapping[0] is the\
    # publisher code 260b
    #
    # only accepts mappings with marc code lengths of 0 (for disabled) or 4
    #
    # Sample Astral Mapping:
    # mapping = ["260b", "", "020a", "", "245a", "250a", "100a", "260c", "072a", "520a", "260a", "", "041a", "365b", "365c"]

    mapping = ["260b", "245a", "020a", "250a", "100a", "260c", "" "365b", "365c", "260a",               "", "500a", "", "", "520a", "505a", "041a", "942c"]
    
    if mapFile:
        try:
            with open(mapFile, 'rb') as fp:
                mapping = json.load(fp)
        except:
            print mapFile + " not found or not valid JSON file."
            exit(0)
    
    # Check mapping for errors
    for key in mapping:
        if not (len(key) == 4 or len(key) == 0):
            print "Error: given mapping has keys with incorrect lengths (valid lengths are 0 or 4)"
            return []
    
    return mapping

def writeMARCXML(record, filename):
    # Write out record in MARCXML format
    writer = XMLWriter(open(filename,'wb'))
    writer.write(record)
    writer.close()  # Important!

def addField(record, key, sf):
    # record is the pymarc record, 
    # key is the key of format '123a' defined in mapping
    # sf is the subfields, i.e. data in the form ['a', 'somedatastring']
    
    # Deal with currency field
    if key[:3] == "365":
        # if field already exists
        if '365' in record:
            # if field doesn't already contain the data we've got
            if key[-1] not in record['365']:
                record['365'].add_subfield(key[-1], sf[1])
                return # so as to not create another field below
    
    record.add_field(
    Field(
        tag = key[:3], # Grab only field number e.g. |520|b
        indicators = ['0', '0'],
        subfields = sf
    ))

def handleXLSX(mapping, sheet, outputFolder, rowsToIgnore):
    # mapping as defined in mapping function loadMapping
    # sheet is the specific excel sheet that contains the data we're extracting
    # rowsToIgnore is the number of rows at top of sheet that we don't care about
    for row in sheet.rows[rowsToIgnore:]:
        record = Record()
        # for every key in our map
        for i, key in enumerate(mapping):
            # if the key isn't empty (i.e. we're not mapping that column)
            if key:
                addField(record, key, [key[3], unicode(row[i].value)])
        if DEBUG:
            print record.title()
            
        # Create unique UUID & add to record
        bookUUID = str(uuid.uuid1())
        record.add_field(Field(tag='001', data=bookUUID))
        
        # Write out our marcxml for each row
        writeMARCXML(record, os.path.join(outputFolder, record.isbn() + '.xml'))

def formatNumber(n):
    # n is some incoming float
    if int(n) == n:
        # n must actually be an int
        return int(n)
    else:
        # n is just a float
        return n

def test_formatNumber():
    testCases = [1000.0, 1234.0, 0.1, 0.001]
    for case in testCases:
        print formatNumber(case)

#test_formatNumber()

def main():
    if DEBUG:
        print "WARNING: In DEBUG mode"
        rowsToIgnore = 1
        excelFilename = './test/BaobabMetadataTemplate.xlsx'
        outputFolder = './test/templateConversionXML/'
        mappingFilename = './test/BaobabMetadataTemplateMapping.json'
        sheetName = 'Sheet1'
    
    # Deal with arguments
    if not DEBUG:
        for i in xrange(len(sys.argv)):
            arg = sys.argv[i]
            if arg == '--help' or arg == '-h' or             '-m' not in sys.argv or '-o' not in sys.argv or '-i' not in sys.argv or '-s' not in sys.argv:
                print "Usage: ./excel2marc.py [-h] [-r rowsToIgnore] -m <mapping file> -i <input excel file> -o <output folder> -s <sheetname>"
                return
            elif arg == '-r':
                rowsToIgnore = int(sys.argv[i+1]) # number of rows to ignore at top of spreadsheet
            elif arg == '-m':
                mappingFilename = sys.argv[i+1]
            elif arg == '-i':
                excelFilename = sys.argv[i+1]
            elif arg == '-o':
                outputFolder = sys.argv[i+1]
            elif arg == '-s':
                sheetName = sys.argv[i+1]
        
    # Get mapping
    mapping = loadMapping(mappingFilename)
    #mapping = loadMapping()

    # Make output dir
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

    # Open excel file
    if excelFilename.split(".")[-1] == "xlsx":
        try:
            wb = openpyxl.load_workbook(filename = excelFilename)
        except:
            e = sys.exc_info()[1]
            print e
            print excelFilename + " is not found or not a valid .xlsx file."
            return
        sheet = wb[sheetName]
        handleXLSX(mapping, sheet, outputFolder, rowsToIgnore)
    else:
        print "Not a valid filetype. Must be .xlsx format."
        
main()

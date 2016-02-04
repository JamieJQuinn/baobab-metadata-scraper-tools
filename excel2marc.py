
# coding: utf-8

# In[ ]:

from pymarc import Record, Field, XMLWriter
import os
import openpyxl
import xlrd
import uuid
import json
import sys

DEBUG = True


# In[ ]:

def loadMapping(mapFile = ""):
    # Maps the index to the field in the csv file. Eg, if field A or 0 is the publisher, mapping[0] is the\
    # publisher code 260b
    #
    # only accepts mappings with marc code lengths of 0 (for disabled) or 4
    #
    # Sample Astral Mapping:
    # mapping = ["260b", "", "020a", "", "245a", "250a", "100a", "260c", "072a", "520a", "260a", "", "041a", "365b", "365c"]

    #mapping = ["260b", "", "020a", "", "245a", "250a", "100a", "260c", "072a", "520a", "260a", "", "041a", "365b", "365c"]
    mapping = ["020a", "245a", "100a", "", "260b", "365c", "365b", "942c", "260c", "041a", "", "520a", "300b", "", "072a", ""]

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
    


# In[ ]:

def writeMARCXML(record, filename):
    # Write out record in MARCXML format
    writer = XMLWriter(open(filename,'wb'))
    writer.write(record)
    writer.close()  # Important!


# In[ ]:

def handleXLSX(mapping, sheet, outputFolder, rowsToIgnore):
    for row in sheet.rows[rowsToIgnore:]:
        record = Record()
        for i, key in enumerate(mapping):
            # If we're actually mapping this column (or this key)
            if key:
                # Add field to record
                record.add_field(
                    Field(
                        tag = key[:3], # Grab only field number e.g. |520|b
                        indicators = ['0', '0'],
                        subfields = [key[3], unicode(row[i].value)]
                    ))
        if DEBUG:
            print record.title()
        # Create unique UUID
        bookUUID = str(uuid.uuid1())
        record.add_field(Field(tag='001', data=bookUUID))
        writeMARCXML(record, os.path.join(outputFolder, record.isbn() + '.xml'))


# In[ ]:

def handleXLS(mapping, sheet, outputFolder, rowsToIgnore):
    for rowCount in xrange(rowsToIgnore, sheet.nrows):
        record = Record()
        for i, key in enumerate(mapping):
            # If we're actually mapping this column (or this key)
            if key:
                # Add field to record
                if sheet.row(rowCount)[i].ctype == 2 or sheet.row(rowCount)[i].ctype == 3:
                    sf = [key[3], unicode(int(sheet.row(rowCount)[i].value))]
                else:
                    sf = [key[3], unicode(sheet.row(rowCount)[i].value)]
                record.add_field(
                    Field(
                        tag = key[:3], # Grab only field number e.g. |520|b
                        indicators = ['0', '0'],
                        subfields = sf
                    ))
        # Create unique UUID
        bookUUID = str(uuid.uuid1())
        record.add_field(Field(tag='001', data=bookUUID))
        writeMARCXML(record, os.path.join(outputFolder, record.isbn() + '.xml'))


# In[ ]:

def main():
    # no of rows to ignore in incoming spreadsheet
    rowsToIgnore = 0
    excelFilename = './Astral/Astral1.xls'
    outputFolder = './Astral/AstralXML1/'
    mappingFilename = ''
    
    # Deal with arguments
    for i in xrange(len(sys.argv)):
        arg = sys.argv[i]
        if arg == '--help' or arg == '-h' or         '-m' not in sys.argv or '-o' not in sys.argv or '-i' not in sys.argv:
            print "Usage: ./excel2marc.py [-h] [-r rowsToIgnore] -m <mapping file> -i <input excel file> -o <output folder>"
            return
        elif arg == '-r':
            rowsToIgnore = int(sys.argv[i+1]) # number of rows to ignore at top of spreadsheet
        elif arg == '-m':
            mappingFilename = sys.argv[i+1]
        elif arg == '-i':
            excelFilename = sys.argv[i+1]
        elif arg == '-o':
            outputFolder = sys.argv[i+1]
        
    
    # Get mapping
    mapping = loadMapping(mappingFilename)
    
    # Open excel file
    if excelFilename.split(".")[-1] == "xlsx":
        try:
            wb = openpyxl.load_workbook(filename = excelFilename)
        except:
            print excelFilename + " is not found or not a valid .xlsx file."
            return
        sheet = wb[wb.get_sheet_names()[0]]
        handleXLSX(mapping, sheet, outputFolder, rowsToIgnore)
    elif excelFilename.split(".")[-1] == "xls":
        try:
            wb = xlrd.open_workbook(excelFilename)
        except:
            print excelFilename + " is not found or not a valid .xls file."
            return
        sheet = wb.sheet_by_index(0)
        handleXLS(mapping, sheet, outputFolder, rowsToIgnore)

    else:
        print "Not a valid filetype. Must be either .xlsx or .xls format."
        
main()



# coding: utf-8

# In[39]:

from pymarc import Record, Field, XMLWriter
import os
import openpyxl
import xlrd
import uuid
import json
import sys

DEBUG = True


# In[40]:

def loadMapping(mapFile = ""):
    # Maps the index to the field in the csv file. Eg, if field A or 0 is the publisher, mapping[0] is the\
    # publisher code 260b
    #
    # only accepts mappings with marc code lengths of 0 (for disabled) or 4
    #
    # Sample Astral Mapping:
    # mapping = ["260b", "", "020a", "", "245a", "250a", "100a", "260c", "072a", "520a", "260a", "", "041a", "365b", "365c"]

    mapping = ["260b", "245a", "020a", "250a", "100a", "260c", "" "365b", "365c", "260a", "", "500a", "", "", "520a", "505a", "041a", "942c"]
    
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
    


# In[41]:

def writeMARCXML(record, filename):
    # Write out record in MARCXML format
    writer = XMLWriter(open(filename,'wb'))
    writer.write(record)
    writer.close()  # Important!


# In[42]:

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


# In[43]:

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
#                 if key[:3] == "365":
#                     # Dealing with currency
#                     if '365' in record:
#                         # Field already exists and contains something
#                         if key[-1] not in record['365']:
#                             # Field doesn't already contain this type of input
#                             record['365'][key[-1]] = unicode(row[i].value)
#                             continue
                        
#                 # Add field to record
#                 record.add_field(
#                     Field(
#                         tag = key[:3], # Grab only field number e.g. |520|b
#                         indicators = ['0', '0'],
#                         subfields = [key[3], unicode(row[i].value)]
#                     ))
        if DEBUG:
            print record.title()
            
        # Create unique UUID & add to record
        bookUUID = str(uuid.uuid1())
        record.add_field(Field(tag='001', data=bookUUID))
        
        # Write out our marcxml for each row
        writeMARCXML(record, os.path.join(outputFolder, record.isbn() + '.xml'))


# In[44]:

def formatNumber(n):
    # n is an incoming float
    if int(n) == n:
        # n must be an int
        return int(n)
    else:
        return n


# In[45]:

def test_formatNumber():
    testCases = [1000.0, 1234.0, 0.1, 0.001]
    for case in testCases:
        print formatNumber(case)

#test_formatNumber()


# In[46]:

def handleXLS(mapping, sheet, outputFolder, rowsToIgnore):
    # mapping as defined in mapping function loadMapping
    # sheet is the specific excel sheet that contains the data we're extracting
    # rowsToIgnore is the number of rows at top of sheet that we don't care about
    
    for rowCount in xrange(rowsToIgnore, sheet.nrows):
        record = Record()
        for i, key in enumerate(mapping):
            # if the key isn't empty
            if key:
                ########### HACK TO GET AROUND XLS NUMBER STORAGE ##############
                # If field is an integer
                if sheet.row(rowCount)[i].ctype == 2 or sheet.row(rowCount)[i].ctype == 3:
                    # Convert to integer before inputting
                    sf = [key[3], unicode(formatNumber(sheet.row(rowCount)[i].value))]
                else:
                    # keep as string
                    sf = [key[3], unicode(sheet.row(rowCount)[i].value)]
                ################################################################
                #sf = [key[3], unicode(sheet.row(rowCount)[i].value)]
                # Then add to record
                addField(record, key, sf)

        # Create unique UUID
        bookUUID = str(uuid.uuid1())
        record.add_field(Field(tag='001', data=bookUUID))
        
        # Write out our marcxml for each row
        writeMARCXML(record, os.path.join(outputFolder, record.isbn() + '.xml'))


# In[48]:

def main():
    if DEBUG:
        print "WARNING: In DEBUG mode"
        rowsToIgnore = 1
        excelFilename = './test/BaobabMetadataTemplate.xls'
        outputFolder = './test/templateConversionXML/'
        mappingFilename = './test/BaobabMetadataTemplateMapping.json'
    
    # Deal with arguments
    if not DEBUG:
        for i in xrange(len(sys.argv)):
            arg = sys.argv[i]
            if arg == '--help' or arg == '-h' or             '-m' not in sys.argv or '-o' not in sys.argv or '-i' not in sys.argv:
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
    #mapping = loadMapping(mappingFilename)
    mapping = loadMapping()
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


# In[ ]:




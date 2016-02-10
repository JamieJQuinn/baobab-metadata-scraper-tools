
# coding: utf-8

# In[4]:

from pymarc import XMLWriter, Record, Field, MARCReader


# In[14]:

inputFileName = "./Astral/Astral1.mrc"
outputFolder = "./Astral/AstralXML1/"
def main():
    with open(inputFileName, 'rb') as fp:
        reader = MARCReader(fp)
        i = 0
        for record in reader:
            writer = XMLWriter(open(outputFolder + record['020']['a'] + '.xml','wb'))
            writer.write(record)
            writer.close()  # Important!
            
main()


# In[ ]:




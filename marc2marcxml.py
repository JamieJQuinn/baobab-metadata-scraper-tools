#!/usr/bin/env python

import argparse
from pymarc import XMLWriter, Record, Field, MARCReader

parser = argparse.ArgumentParser()
parser.add_argument('files', metavar='file', type=str, nargs='+')

def main():
    files = parser.parse_args().files
    for filename in files:
        print filename
        with open(filename) as fp:
            reader = MARCReader(fp)
            writer = XMLWriter(open(filename.split('.')[0]+'.xml', 'wb'))
            for record in reader:
                writer.write(record)
            writer.close()  # Important!
                
main()

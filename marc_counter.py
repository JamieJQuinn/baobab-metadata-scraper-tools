import argparse
from pymarc import MARCReader

parser = argparse.ArgumentParser()
parser.add_argument('files', metavar='file', type=str, nargs='+',
                   help='counts number of marc records in file')

def main():
    count = 0
    files = parser.parse_args().files
    for filename in files:
        with open(filename, 'r') as fp:
            reader = MARCReader(fp)
            for record in reader:
                count += 1

    print count
            

main()

# Baobab Metadata Scraper Tools

> Archived **2024-04-08**  |  Last Commit **2016-08-15**

> This is a collection of tools I wrote for Baobab Ebooks who were developing a curated library of free ebooks and required data scrapers and convertors for associated metadata.

A selection of scripts written for Baobab Ebooks

# excel2marc.py
Takes a mapping file and excel spreadsheet and maps the columns of the spreadsheet to MARC fields. Outputs one marcxml file per row in the spreadsheet. Handles both xls and xlsx.
Usage:
./excel2marc.py [-h] [-r rowsToIgnore] -m <mapping file> -i <input excel file> -o <output folder>

# marc2marcxml.py
Takes a marc file in transmission format and converts to marcxml, outputting one xml file per record in input.

# ILOScraper.py
Scrapes the ILO site for download links and metadata for all available books then downloads and formats metadata into marcxml.

# WHOScraper.py
Same as ILOScraper but applied to the World Health Organisation.

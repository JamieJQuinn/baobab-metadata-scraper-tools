# baobab-scripts
A selection of scripts written for Baobab Ebooks

* excel2marc.py: Takes a mapping file and excel spreadsheet and maps the columns of the spreadsheet to MARC fields. Outputs one marcxml file per row in the spreadsheet. Handles both xls and xlsx.

* marc2marcxml.py: takes a marc file in transmission format and converts to marcxml, outputting one xml file per record in input.

* ILOScraper.py: Scrapes the ILO site for download links and metadata for all available books then downloads and formats metadata into marcxml.

* WHOScraper.py: Same as ILOScraper but applied to the World Health Organisation.

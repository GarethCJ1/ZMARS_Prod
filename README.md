# ZMARS_Prod
 ZMARS Mainframe Availability and Resilience Service Tools
### Introduction
This project provides tooling to analyse aspects of Db2 for z/OS. 
It is used by Triton Consulting Ltd's ZMARS service (Mainframe 
Availability and Resilience Study).
### Contributors
Gareth Copplestone-Jones Gareth.Copplestone-Jones@triton.co.uk
### Description
Post process Omegamon for Db2 PE, RMF and other reports to faciliate
analysis of the resilience and availability of Db2 for z/OS subsystems
and data sharing groups. Output will be in the form of csv files for
analysis with Microsoft Excel, and in other forms.
### Programs
- **TZM_BSDS_Listing_Parser.py:** Parse the output of the DSNJU004 BSDS listing to
produce two csv files to be imported into a Microsoft Excel spreadsheet, one
for the active logs, one for the archive logs.
- **TZM_BSDS_Parser_Driver.py:** Drive the BSDS listing parser with the names
of the output directory, the output file prefix, the SSIDs or member names,
and the file name of the listing for each SSID or member.

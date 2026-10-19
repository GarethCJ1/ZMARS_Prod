# -*- coding: utf-8 -*-
"""
Created on Friday 11th October 2023

@author: gcopplestone-jones
@purpose: Build a ditcionary of DSNJU004 BSDS listing file 
         names, the target output file directory, and the 
         output file name prefix, and pass the dictionary to 
         TZM_BSDS_Listing_Parser.py
"""

import TZM_OMPE_Stats_Trace_Parser
from pathlib import Path

bsdsp_dict = {
    'dsnju004_listings': [Path('C:\\Users\\garet\\OneDrive - Triton Consulting\\Documents\\Customers\\Zions Bank\\bsds1.txt')],
    'ssids': ['DB2P'],
    'odir': 'C:\\Users\\garet\\OneDrive - Triton Consulting\\Documents\\Customers\\Zions Bank',
    'opref': 'DB2PN'
}

TZM_OMPE_Stats_Trace_Parser.main(bsdsp_dict)
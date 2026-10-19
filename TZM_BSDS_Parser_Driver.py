# -*- coding: utf-8 -*-
"""
Created on Friday 11th October 2023

@author: gcopplestone-jones
@purpose: Build a ditcionary of DSNJU004 BSDS listing file 
         names, the target output file directory, and the 
         output file name prefix, and pass the dictionary to 
         TZM_BSDS_Listing_Parser.py
"""

import TZM_BSDS_Listing_Parser
from pathlib import Path

bsdsp_dict = {
    'dsnju004_listings': [Path('C:\\Users\garet\OneDrive - Triton Consulting\Documents\Customers\PKO Bank Polski SA\Data\DSNJU004_DBP1.txt'),
                          Path('C:\\Users\garet\OneDrive - Triton Consulting\Documents\Customers\PKO Bank Polski SA\Data\DSNJU004_DBP2.txt'),
                          Path('C:\\Users\garet\OneDrive - Triton Consulting\Documents\Customers\PKO Bank Polski SA\Data\DSNJU004_DBP3.txt'),
                          Path('C:\\Users\garet\OneDrive - Triton Consulting\Documents\Customers\PKO Bank Polski SA\Data\DSNJU004_DBP4.txt')],
    'ssids': ['DBP1', 'DBP2', 'DBP3', 'DBP4',], 
    'odir': 'C:\\Users\garet\OneDrive - Triton Consulting\Documents\Customers\PKO Bank Polski SA\Data',
    'opref': 'DSNDB2P'
} 
TZM_BSDS_Listing_Parser.main(bsdsp_dict)
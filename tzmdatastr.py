# -*- coding: utf-8 -*-
"""
Current version Tuesday 11th October 2023

Author: Gareth Copplestone-Jones, Triton Consulting
    gareth.copplestone-jones@triton.co.uk

Purpose: 
    Define all Db2 for z/OS DSNZPARM macros and allowable values
    Data only     
"""

"""
Structure:
    {Macro}:
        {parameter:[
        {type:['K' for keyword or 'P' for positional},[Position],
        [allowable values],[min value],[max value],[recommended value by release]] }

    Note: The first two parameters for macro DSN6SPRM are positional and require
          special processing. All other parameters are keyword.
          For keyword parameters, Position is omitted.
          If there is a list of discrete allowed values, they are listed in 'Allowable_values'.
          If there is a list of values in a range, they are listed as 'Min_value' and 'Max_value'.
          If there is no recommended value for a release, the value is 'N/A'.
"""

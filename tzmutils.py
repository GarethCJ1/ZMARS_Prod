# -*- coding: utf-8 -*-
"""
Current version Tuesday 11th October 2023

Author: Gareth Copplestone-Jones, Triton Consulting
    gareth.copplestone-jones@triton.co.uk

Purpose: 
    Various utility functions for use by Triton Z MARS programs

Functions:
    File existence checker 
     
"""

import sys
import os.path

def file_check(listing, outlog, caller):
    if not os.path.exists(listing):
        outlog.write(f"{caller} file check error ===>")
        outlog.write(f"\t File {listing} not found, exiting")
        print(f"{caller} exiting with error, see logfile")
        sys.exit(8)
        
def t_hours(timevalue):
    """ 
    Converts a time value in hh:mm:ss to hours
    Throws away the seconds value
    For Python timedelta strings with 'n day(s)' convert days to hours
    """
    timevalue = str(timevalue)            # convert to string for manipulation
    timevalue = timevalue.strip('"')      # Remove any double quote marks
    if 'day' in timevalue:
        days_time = timevalue.split(",")
        ddays = days_time[0].split(" ")
        dhours = (int(ddays[0])) * 24
        timevalue = days_time[1]
    else:
        dhours = 0
    zmtimes = timevalue.split(":")
    zmtimes[0] = (int(zmtimes[0])) * 60     # convert hours to minutes
    zmtimes[1] = int(zmtimes[1])     
    zmtimes[2] = dhours * 60 
    return (sum(zmtimes) // 60)         # return minutes converted to hours

def t_minutes(timevalue):
    """ 
    Converts a time value in hh:mm:ss to minutes
    For Python timedelta strings with 'n day(s)' convert days to hours
    """
    timevalue = str(timevalue)            # convert to string for manipulation
    timevalue = timevalue.strip('"')      # Remove any double quote marks
    if 'day' in timevalue:
        days_time = timevalue.split(",")
        ddays = days_time[0].split(" ")
        dhours = (int(ddays[0])) * 24
        timevalue = days_time[1]
    else:
        dhours = 0
    zmtimes = timevalue.split(":")
    zmtimes[0] = (int(zmtimes[0])) * 60     # convert hours to minutes
    zmtimes[1] = int(zmtimes[1])     
    zmtimes[2] = dhours * 60 
    return sum(zmtimes)                     # return minutes
# -*- coding: utf-8 -*-
"""
Created on Tuesday 13th February 2024

Author: Gareth Copplestone-Jones, Triton Consulting
    gareth.copplestone-jones@triton.co.uk

Purpose: 
    Parse BSDS listings (output from DSNJU004).
    Produce active log and archive log csv files for input to a
    spreadsheet for analysis of the health of the Db2 logging 
    subsystem.

Dependencies: 
    This code is dependent on the BSDS being in the extended
    (10 byte RBA/LRSN) format. The extended format is required for 
    Db2 12, optional for Db2 11 ad not supported in prior releases.
    This code is also dependent on receiving a valid DSNJU004 (Print 
    Log Map) report, in the format as documented in the Db2 12 and 
    Db2 13 manuals (see the Utility Guide and Reference)

Input:
    A Python dictionary containing:
        DSNJU004 BSDS listing
        Output file prefix
        Output file directory

Output:
    Active log csv file
    Archive log csv file
    TZM BSDS Parser output log file        
"""

import sys
from sys import platform
import csv
from tzmutils import file_check, t_minutes
from datetime import datetime , timedelta


def unxeof(listing):
    """Close files on enexpected end of input file and exit with error code 8"""
    outlog.write(f"Unexpected end of file found in {listing}\n")
    outlog.close()
    actcsv.close()
    archcsv.close()
    return 8

def getbsdsline(dsnju004, listing, check_cc = False):
    """Return a line, the line split into a word list, and a word index bypassing any
    ASA print control characters"""
    global remove_cc
    bsdsline = dsnju004.readline()
    if not bsdsline:
        ret_code = unxeof(listing)
        if ret_code > 0:
            return ret_code
    if check_cc and bsdsline[0] in "01-":
        remove_cc = True
    elif remove_cc:
        # Leave the remove_cc flag set to True if it has been set previously, even if the current line does not have a print control character
        pass
    else:
        remove_cc = False
    if remove_cc:
        bsdsline = bsdsline[1:]
    linelist = bsdsline.split()
    return bsdsline, linelist

def tsbuild(datepart,timepart):
    """Builds a Python datetime object from the active and archive log julian date
    and timestamp reported by the DSNJU004 utility.
    DSNJU004 timestamp is in the form hh:mm:ss:t e.g. 14:51:03.4
    Julian date is in the format YYYY.DDD.
    Also builds a Python datetime object from a manufactured timestamp in the 
    correct format.
    Output format is YYYY-MM-DD HH:MM:SS """
    if "." in datepart:
        # Remove the '.' from the date string
        datepart = datepart[0:4] + datepart[5:]
    thh = str(timepart[0:2])  # hours
    tmm = str(timepart[3:5])  # minutes
    tss = str(timepart[6:8])  # seconds
    #  Round up seconds if needed
    if int(timepart[9:10]) >= 5:
        tss = int(tss)
        tss += 1
        tss = str(tss)
        if tss == "60":
            tss = "00"
            tmm = int(tmm)
            tmm += 1
            tmm = str(tmm)
            if tmm == "60":
                tmm = "00"
                thh = int(thh)
                thh += 1
                thh = str(thh)
                if thh == "24":
                    thh = "00"
                    datepart = datetime.strptime(datepart, "%Y%j")
                    datepart = datepart + timedelta(days = 1)
                    datepart = datepart.timetuple()
                    datepart = datepart.tm_yday 
    jtstamp = datepart + thh + tmm + tss
    return datetime.strptime(str(jtstamp), "%Y%j%H%M%S")

def bsds_parse(listing):
    """Parses the output of the DSNJU004 (Print Log Map) utility and extracts and writes data
    to the output csv-format file"""
    global ssidix
    global DSSIZE
    global LTIME
    actlognum = 0
    archlognum = 0
    actlines = []
    archlines = []
    archlog_ts_list = []
    if not listing:
        outlog.write("Function bsds_parse requires a file name argument, terminating with error code 8")
        # Tidy up before exiting
        actcsv.close()
        archcsv.close()
        return 8
    logline = "Processing started for input listing dataset " + str(listing) + "started \n"
    outlog.write(logline)
    prev_arch_dsn = " "
    dsnju004 = open(listing, "r", newline = "") 
    # Get the ssid for this BSDS listing
    if ssid_list:
        ssid = ssids[ssidix]
        ssidix += 1
    # Identify whether this Db2 is part of a data sharing group -
    # search for the line with "LOG MAP OF THE BSDS DATA SET" 
    dsfound = False
    while not dsfound:
        bsdsline, linelist = getbsdsline(dsnju004, listing, check_cc = True)
        if LOGMAP in bsdsline:
            dsfound = True
            # If member name is "NO NAME" data sharing mode is off
            if NONAME in bsdsline:
                ds_mode = False
                outlog.write("\tData Sharing mode is OFF \n")
            else:
                ds_mode = True
                outlog.write("\tData Sharing mode is ON \n")
                # If data sharing mode but no ssid provided then get from LOG MAP line
                if not ssid_list:
                    logmapstart = bsdsline.find(LOGMAP)
                    logmapwords = bsdsline[logmapstart:]
                    ssid = logmapwords[10].strip("'")
    actfound = False
    # Search for the active log section
    while not actfound:
        bsdsline, linelist = getbsdsline(dsnju004, listing)
        if ACTLOGC in bsdsline:
            actfound = True
    archfound = False
    # Now we have found the active log section, we need to search for the STARTRBA header line
    startrbafound = False
    # Extract the active log information, and search for the archive log section
    while not archfound:
        bsdsline, linelist = getbsdsline(dsnju004,listing)
        if START_RBA in bsdsline:
            # We have found the STARTRBA header line
            # Skip over the heading lines to the active log detail
            bsdsline, linelist = getbsdsline(dsnju004,listing)
            startrbafound = True
            outlog.write("START RBA found for active log section, active log processing started \n")
        while startrbafound and not archfound:
            # Common processing for data sharing member and standalone subsystem
            # See below for sample active log detail lines

            # From the first line of output, extract the startrba, endrba and  
            # name of the active log dataset
            actlines.append({})
            bsdsline, linelist = getbsdsline(dsnju004,listing)
            if ARCHLOGC in bsdsline:
                archfound = True
                break
            startrba = linelist[0]
            endrba = linelist[1]
            actlines[actlognum]["ENDRBA"] = endrba
            # Calculate the active log dataset size in MiB
            actsizebytes = int(str(endrba), 16) - int(str(startrba), 16)
            actlines[actlognum][DSSIZE] = round(actsizebytes / (1024 ** 2)) 
            dsname = linelist[3]
            actlines[actlognum]["DSNAME"] = dsname.removeprefix("DSN=")
            # If ssid is not provided and data sharing mode is off, make best effort to get from data set name
            if not ssid_list and not ds_mode:
                dsn_quals = actlines[actlognum]["DSNAME"].split(".")
                if len(dsn_quals) == 3:
                    ssid = dsn_quals[0]
                else:
                    ssid = dsn_quals[-2]    
            if ds_mode:
                # Data sharing active log detail with header lines (formatting simplified)
                # START RBA/LRSN/TIME    END RBA/LRSN/TIME      DATE/LTIME DATA SET INFORMATION
                # ---------------------- ---------------------- ---------- --------------------
                # 000000004C444BBDD000   000000004C44A455CFFF   2011.193   DSN=DSNL5LOG.DL51.LOGCOPY1.DS03
                #   00CB81C00D9C43400400   00CB81C3CE783A060000    9:41    STATUS=REUSABLE
                #   2013.164  16:35:33.3   2013.164  16:52:20.9

                # Extract the endlrsn and the active log dataset status
                bsdsline,linelist = getbsdsline(dsnju004,listing)
                actlines[actlognum]["ENDLRSN"] = linelist[1]
                status = linelist[3]
                status = status.removeprefix("STATUS=")
                # Add addtional status if it is, e.g., "TRUNCATED, REUSABLE"
                if len(linelist) > 4:
                    status = status.rstrip(",") + " " + linelist[4]
                actlines[actlognum]["STATUS"] = status
            else:
                # Standalone subsystem active log detail with header lines (formatting simplified)
                # START RBA/LRSN/TIME    END RBA/LRSN/TIME      DATE/LTIME DATA SET INFORMATION
                # ---------------------- ---------------------- ---------- --------------------
                # 000000004C444BBDD000   000000004C44A455CFFF   2011.193   DSN=DSNL5LOG.DL51.LOGCOPY1.DS03
                #   2013.164  16:35:33.3   2013.164  16:52:20.9    9:41    STATUS=REUSABLE

                # For stand-alone mode, set the endlrsn to null
                actlines[actlognum]["ENDLRSN"] = ""
            # Extract the start and end dates and times
            actlines[actlognum]["SSID"] = ssid
            bsdsline, linelist = getbsdsline(dsnju004,listing)
            if not ds_mode:
                # For stand-alone mode, extract the active log dataset status
                status = linelist[5]
                status = status.removeprefix("STATUS=")
                if len(linelist) > 6:
                    status = status.rstrip(",") + " " + linelist[6]
                actlines[actlognum]["STATUS"] = status
            if status == NOTREUSABLE:
                actlines[actlognum]["ENDTIME"] = ""
            else:
                enddate = linelist[2]
                endtime = linelist[3]
                actlines[actlognum]["ENDTIME"] = tsbuild(enddate,endtime)
            actlognum += 1
    # Write out the active log data for this listing
    del actlines[-1]
    actwriter.writerows(actlines)
    logline = "Active log processing completed for " + ssid + " , for " + str(actlognum) + " active log pairs\n"
    outlog.write(logline)
    # Parse the archive log section
    # First, reset the active log found and the startrbafound flags 
    actfound = False
    startrbafound = False
    outlog.write("Archive log processing started \n")
    while not actfound:
        bsdsline, linelist = getbsdsline(dsnju004,listing)
        if START_RBA in bsdsline:
            # We have found the STARTRBA header for the archive log section
            # Skip over the heading lines to the archive log detail
            bsdsline, linelist = getbsdsline(dsnju004,listing)
            bsdsline, linelist = getbsdsline(dsnju004,listing)
            startrbafound = True
        # Commence processing of archive log detail, one anonymous dictionary for each csv output line
        while startrbafound and archfound:
            archlines.append({})
            archsizebytes = 0
            # Check to see if we've reached the end of the archive log detail and have moved onto 
            # the section for active log copy 2
            if ACTLOGC in bsdsline:
                actfound = True
                archfound = False
                break
            # Common archive log processing for data sharing member and standalone subsystem
            #
            # Set the mulit-volume flag initially to null, extract the start and end RBA, 
            # and the file name 
            archlines[archlognum]["MULTI"] = ""
            startrba = linelist[0]
            endrba = linelist[1]
            archdsn = linelist[3].removeprefix("DSN=")
            # If this archive log file has the same name as the previous one, set the multi-volume 
            # flag to YES and concatenate the volume serial numbers  
            if archdsn == prev_arch_dsn:
                archlines[archlognum]["MULTI"] = "YES"
                archsizebytes = archsizebytes + int(str(endrba), 16) - int(str(startrba), 16)
                bsdsline, linelist = getbsdsline(dsnju004,listing)
                if ds_mode:
                    archlines[archlognum]["VOL"] = archlines[archlognum]["VOL"] + " " + linelist[3].removeprefix("VOL=")
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
                else:
                    archlines[archlognum]["VOL"] = archlines[archlognum]["VOL"] + " " + linelist[5].removeprefix("VOL=")
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
            # Otherwise, process as a new archive log file
            else:
                prev_arch_dsn = archdsn
                archlines[archlognum]["DSNAME"] = archdsn
                # Continue common archive log processing for data sharing member and standalone subsystem
                # Calculate the size of the archive log and extract the local date (year and julian day)
                archsizebytes = int(str(endrba), 16) - int(str(startrba), 16)
                archlines[archlognum]["SSID"] = ssid
                archdate = linelist[2]
                archdatelist = archdate.split(".")
                archlines[archlognum]["YEAR"] = archdatelist[0]
                archlines[archlognum]["DAY"] = archdatelist[1]
                bsdsline, linelist = getbsdsline(dsnju004,listing)
                if ds_mode:
                    # Data sharing member archive log detail with header lines (formatting simplified)
                    # START RBA/LRSN/TIME    END RBA/LRSN/TIME      DATE/LTIME DATA SET INFORMATION
                    # ---------------------- ---------------------- ---------- --------------------
                    # 000000003ECDEE9AE000   000000003ECE4732DFFF   2013.074   DSN=DSNL5AR1.DL51.D13074.T0753360.A0165898
                    #   00CB108020450A8B8600   00CB10817DEBA05B8000    7:54    VOL=ARX081 UNIT=SYSDA
                    #   2013.074 14:47:52.2     2013.074 14:53:58.8
                    #                                                        CATALOGUED
                    # 
                    # Extract the local time, the disk/tape volume serial and the unit, 
                    # and skip to the next archive log detail line
                    archlines[archlognum]["LOCAL TIME"] = linelist[2]
                    archlines[archlognum]["VOL"] = linelist[3].removeprefix("VOL=")
                    archlines[archlognum]["UNIT"] = linelist[4].removeprefix("UNIT=")
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
                else:
                    # Standalone subsystem archive log detail with header lines (formatting simplified)
                    # START RBA/LRSN/TIME    END RBA/LRSN/TIME      DATE/LTIME DATA SET INFORMATION
                    # ---------------------- ---------------------- ---------- --------------------
                    # 000000003ECDEE9AE000   000000003ECE4732DFFF   2013.074   DSN=DSNL5AR1.DL51.D13074.T0753360.A0165898
                    #   2013.074 14:47:52.2     2013.074 14:53:58.8    7:54    VOL=ARX081 UNIT=SYSDA
                    #                                                          CATALOGUED
                    # Extract the local time, the disk/tape volume serial and the unit, 
                    # and skip to the next archive log detail line
                    archlines[archlognum][LTIME] = linelist[4]
                    archlines[archlognum]["VOL"] = linelist[5].removeprefix("VOL=")
                    archlines[archlognum]["UNIT"] = linelist[6].removeprefix("UNIT=")
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
                    bsdsline, linelist = getbsdsline(dsnju004,listing)
            # Resume common processing for data sharing members and standalone subsystems
            # Calculate the archive log file size in MiB, and calculate the period required
            # to wrap around the active logs, excluding the first <number_of_active_logs> 
            # archive logs
            archlog_ts_list.append(0)
            archlines[archlognum][DSSIZE] = round(archsizebytes / (1024 ** 2))
            if len(archlines[archlognum][LTIME]) == 4:
                archlines[archlognum][LTIME] = "0" + archlines[archlognum][LTIME]
            arch_tstamp = archlines[archlognum][LTIME] + ":00.0"
            archlog_ts_list[archlognum] = tsbuild(archdate, arch_tstamp)  # noqa: F821
            if archlognum > actlognum:
                archlines[archlognum][PERIOD_COVERED] = t_minutes(archlog_ts_list[archlognum] - archlog_ts_list[archlognum - actlognum])
            else:
                archlines[archlognum][PERIOD_COVERED] = "N/A"
            archlines[archlognum][LTIME] = archlog_ts_list[archlognum]
            archlognum += 1
    del archlines[-1]
    archwriter.writerows(archlines)
    logline = "Archive log processing completed for " + ssid + " , for " + str(archlognum) + " archive log files\n"
    outlog.write(logline)
    dsnju004.close()
    return None              
                

def main(bsdsdict):
    # Declare global variables
    global actcsv        # output active log csv file
    global archcsv       # output archive log csv file
    global LOGMAP        # search string for the start of the log map output 
    global NONAME        # search string for non-data sharing indicator       
    global ACTLOGC       # search string for the DSNJU004 active log section
    global ARCHLOGC      # search string for the DSNJU004 archive log section
    global START_RBA     # search string for the DSNJU004 active and archive log header lines
    global HEX           # hexadecimal number indicator
    global NOTREUSABLE   # indicates current active log data set, therefore no end time
    global DSSIZE        # indicates the size of the active or archive log data set 
    global LTIME         # indicates the local time of the active or archive log data set
    global PERIOD_COVERED # indicates the period covered by the archive log data set
    global outlog        # output parser log - informational and error messages
    global ssids         # list of Db2 ssids
    global actwriter     # csv file writer for the active log output
    global archwriter    # csv file writer for the archive log output
    global ssid_list       # flag to indicate list of ssids is absent
    global ssidix        # index for the ssid list
    global remove_cc     # remove ASA print control characters

    # Constants
    ACTLOGC = "ACTIVE LOG COPY"
    ARCHLOGC = "ARCHIVE LOG COPY"
    START_RBA = "START RBA"
    LOGMAP = "LOG MAP OF THE BSDS DATA SET"
    NONAME = "NO NAME"
    NOTREUSABLE = "NOTREUSABLE"
    HEX = "0x"
    DSSIZE = "DSSIZE(MiB)"
    LTIME = "LOCAL TIME"
    PERIOD_COVERED = "PERIOD COVERED"

    # Variables
    ssid_list = True
    ssidix = 0
    ret_code = 0
    # Set the directory separator according to the OS we are running on.
    # Currently only Windows and Linux are supported.
    if platform == "linux" or platform == "linux2":
        oldsep = "\\"
        newsep = "/"
    elif platform == "win32":
        oldsep = "/"
        newsep = "\\"
    else:
        print(f"TZM BSDS Parser Unexpected run-time environment {platform}, exiting")
        return 8
        # sys.exit(8)

    # Set the output file directory and filename prefix
    odir = bsdsdict.get("odir")
    odir.replace(oldsep, newsep)
    if odir[-1] != newsep:
        odir += newsep
    opref = bsdsdict.get("opref")
    # Get the list of ssids or member names passed in the argument dictionary
    ssids = bsdsdict.get("ssids")
    # If ssids not provided ...
    if ssids is None:
        ssid_list = False

    # Open the output parser log file and write initial informational
    # and diagnostic output
    logfile = odir + opref + ".log.txt"
    try:
        outlog = open(logfile, "w")
    except (IOError, OSError) as e:
        print(f"Open error {e} trying to open file {logfile}, exiting")
        return 8
    logline = "TZM_BSDS_Listing_Parser processing started " + datetime.now().strftime("%a %d %b %Y, %H").rjust(40) + "\n"
    outlog.write(logline)
    outlog.write("\n")
    logline = "Output directory for Parser log and csv files ==> " + odir + "\n"
    outlog.write(logline)
    logline = "Filename prefix for all output files ==> " + opref + "\n"
    outlog.write(logline)
    if ssid_list:
        if len(bsdsdict["dsnju004_listings"]) != len(ssids):
            logline = "Error: number of input DSNJU004 listings " + str(len(bsdsdict["dsnju004_listings"]))  
            logline = logline + " differs from number of input SSIDs " + str(len(ssids)) + "\n"
            outlog.write(logline)
            outlog.write("List of input DSNJU004 listings ==> \n")
            for in_listing in bsdsdict["dsnju004_listings"]:
                logline = "\t" + str(in_listing) + "\n"
                outlog.write(logline)
            outlog.write("List of input SSIDS ==> \n")
            for in_ssid in bsdsdict["ssids"]:
                logline = "\t" + in_ssid + "\n"
                outlog.write(logline)
            outlog.write("Terminating with above error")
            return 8
        else:
            outlog.write("List of DSNJU004 listings and SSID pairs ==> \n")
            for pair in range(0, len(ssids)):
                logline = "\t" + ssids[pair] +  " ==> " + str(bsdsdict["dsnju004_listings"][pair]) + "\n"
                outlog.write(logline)
    else:
        outlog.write("No list of ssids provided, list of input DSNJU004 listings follows ==> \n")
        for in_listing in bsdsdict["dsnju004_listings"]:
            logline = "\t" + str(in_listing) + "\n"
            outlog.write(logline)
    outlog.write("Initial input argument validation complete, commencing TZM BSDS Parser input file verification \n")
    # Check the input files exist
    for dsnju004_listing in bsdsdict["dsnju004_listings"]:
        file_check(dsnju004_listing, outlog, "TZM BSDS Parser")
    outlog.write("TZM BSDS Parser input file verification completed \n")

    # Open the output active log and archive log csv files and write headers
    # Create empty dictionaries and lists for active and archive log output 
    actfile = odir + opref + ".active.csv"
    archfile = odir + opref + ".archive.csv"
    # ssid_list = False
    # Open the csv output file for the active logs and write the header row
    try:
        actcsv = open(actfile, "w", newline="")
    except (IOError, OSError) as e:
        print(f"Open error {e} trying to open file {actfile}, exiting")
        return 8
    actfields = [
        "SSID",
        "DSNAME",
        "ENDTIME",
        "ENDRBA",
        "ENDLRSN",
        "STATUS",
        DSSIZE,
    ]
    actwriter = csv.DictWriter(actcsv, fieldnames=actfields)
    actwriter.writeheader()
    # Open the csv output file for the archive logs and write the header row
    try:
        archcsv = open(archfile, "w", newline="")
    except (IOError, OSError) as e:
        print(f"Open error {e} trying to open file {archfile}, exiting")
        return 8
        # sys.exit(8)
    archfields = [
        "SSID",
        "YEAR",
        "DAY",
        LTIME,
        "LOCAL TIMESTAMP",
        "DSNAME",
        "MULTI",
        "UNIT",
        "VOL",
        DSSIZE,
        PERIOD_COVERED,
    ]
    archwriter = csv.DictWriter(archcsv, fieldnames=archfields)
    archwriter.writeheader()

    # Call the parser function for each listing in the argument dictionary
    for dsnju004_listing in bsdsdict["dsnju004_listings"]:
        remove_cc = False
        ret_code = bsds_parse(dsnju004_listing)

    outlog.write("Processing completed\n")
    outlog.close()
    actcsv.close()
    archcsv.close()

    return ret_code


if __name__ == "__main__":
    # This is the main entry point for the TZM BSDS Parser
    # The code is designed to be called from a driver program, but can be run standalone
    # for testing purposes.
    # The driver program should pass a dictionary containing the input file names, output directory and prefix
    # to the main function. The dictionary should be in the form:
    # { 'dsnju004_listings': [<list of input file names>],
    #   'ssids': [<list of ssids>],
    #   'odir': <output directory>,
    #   'opref': <output file prefix> }
    # The dictionary can be built in the driver program and passed to the main function.
    # The driver program should also handle any errors returned by the main function.
    main(sys.argv[1])

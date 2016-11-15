#!/usr/bin/env python

import os, sys
import datetime
from pyhdf.SD import SD, SDC


def extractEVDCData(fileAbsPath):
    inFile = SD(fileAbsPath, SDC.READ)
    outFileName = os.path.split(fileAbsPath)[1][0:-3] + 'xml'
    outFile = open(outFileName, 'w')
    
    siteName = inFile.attributes(True)['DATA_LOCATION'][0]
    siteLatitude = inFile.select('LATITUDE.INSTRUMENT')[0]
    siteLongitude = inFile.select('LONGITUDE.INSTRUMENT')[0]
    siteElevation = inFile.select('ALTITUDE.INSTRUMENT')[0]
    
    outFile.write('<EVDC>\n')
    outFile.write('    <siteName>' + siteName + '</siteName>\n')
    outFile.write('    <siteLatitude>' + str(siteLatitude) + '</siteLatitude>\n')
    outFile.write('    <siteLongitude>' + str(siteLongitude) + '</siteLongitude>\n')
    outFile.write('    <siteElevation>' + str(siteElevation) + '</siteElevation>\n')
    
    timestamps = inFile.select('DATETIME')
    timestampCount = timestamps.info()[2]
    
    so2absorption = inFile.select('SO2.COLUMN_ABSORPTION.SOLAR')
    field = so2absorption.attributes(True)['VAR_NAME'][0]
    
    for i in range(0, timestampCount):
        referenceDate = datetime.date(2000,1,1)
        days = int(timestamps[i])
        hours = int((timestamps[i]-days) * 24)
        minutes = int(((timestamps[i]-days)*24-hours) * 60)
        seconds = int(((((timestamps[i]-days)*24-hours)*60)-minutes) * 60)
        
        date = referenceDate + datetime.timedelta(days)
        measurementTime = date.strftime('%Y-%m-%dT') + str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2) + 'Z'
        
        outFile.write('    <data>\n')
        outFile.write('        <timeStart>' + measurementTime + '</timeStart>\n')
        outFile.write('        <timeEnd>' + measurementTime + '</timeEnd>\n')
        outFile.write('        <field>'+ field + '</field>\n')
        outFile.write('        <value>' + str(so2absorption[i]) + '</value>\n')
        outFile.write('    </data>\n')
        
        
    outFile.write('</EVDC>')
    outFile.close()
    
    return [outFileName]
        

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s EVDC_file' % sys.argv[0])
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])
            
    extractEVDCData(sys.argv[1])
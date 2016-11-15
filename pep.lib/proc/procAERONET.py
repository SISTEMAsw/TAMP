#!/usr/bin/env python

import os, sys

def extractAERONETData(fileAbsPath):
    inFile = open(fileAbsPath, 'r')
    outFileName = os.path.split(fileAbsPath)[1][0:-5] + 'xml'
    outFile = open(outFileName, 'w')
        
    lines = inFile.read().split('\n')
    preamble = lines[2].split(',')
    
    siteName = preamble[0].split('=')[1]
    siteLongitude = preamble[1].split('=')[1]
    siteLatitude = preamble[2].split('=')[1]
    siteElevation = preamble[3].split('=')[1]
    
    outFile.write('<AERONET>\n')
    outFile.write('    <siteName>' + siteName + '</siteName>\n')
    outFile.write('    <siteLongitude>' + siteLongitude + '</siteLongitude>\n')
    outFile.write('    <siteLatitude>' + siteLatitude + '</siteLatitude>\n')
    outFile.write('    <siteElevation>' + siteElevation + '</siteElevation>\n')

    header = lines[4].split(',')

    for i in range (5, len(lines)-1):
        data = lines[i].split(',')
        day = data[0].split(':')
        measurementTime = day[2] + '-' + day[1] + '-' + day[0] + 'T' + data[1] + 'Z'
        fieldName = header[8]
        fieldData = data[8]
        outFile.write('    <data>\n')
        outFile.write('        <timeStart>' + measurementTime + '</timeStart>\n')
        outFile.write('        <timeEnd>' + measurementTime + '</timeEnd>\n')
        outFile.write('        <field>' + fieldName + '</field>\n')
        outFile.write('        <value>' + fieldData + '</value>\n')
        outFile.write('    </data>\n')
        
    outFile.write('</AERONET>\n')
    
    inFile.close()
    outFile.close()
    
    return [outFileName]
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s AERONET_file\n' % sys.argv[0])
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])
            
    extractAERONETData(sys.argv[1])
#!/usr/bin/env python

import os, sys
import psycopg2
import logging

#filePath = "test_new.xml"


def databaseCon():  # Opens db connection
    installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    parser = SafeConfigParser()
    parser.read("%s/../etc/das_ing.ini" % installation_dir)
    print "connecting..."
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" % (parser.get("proc", "name"), parser.get("proc", "user"), parser.get("proc", "host"), parser.get("proc", "pass")))
    #conn = psycopg2.connect(connection)

    return conn


def searchStationID(conn, stationCode):  # checks if station is already in the DB
    foundstation = {}
    query = """SELECT name, longitude, latitude, height, "stationCode" FROM stations WHERE "stationCode"='{}';""".format(stationCode)
    cur = conn.cursor()
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        sys.exit("Can't SELECT from stations\n{}".format(e))
    if not rows:  # if no station is found -> false
         sys.exit("No station found!")
    else:

        foundstation["station"] = rows[0][0]
        foundstation["longitude"] = float(rows[0][1])
        foundstation["latitude"] = float(rows[0][2])
        foundstation["height"] = float(rows[0][3])
        foundstation["stationCode"] = rows[0][4]
    return foundstation


def extractGroundSO2Data(fileAbsPath):    
    inFile = open(fileAbsPath)    
    outFileNameHourly = os.path.basename(fileAbsPath)[0:-4] + '_hourly.xml' 
    outFileHourly = open(outFileNameHourly, 'w')    
    
    stationCode = os.path.basename(fileAbsPath)[0:9]
    conn = databaseCon()
    station = searchStationID(conn, stationCode)


    #if stationCode == '1010-SON1':
    #    station = 'Sonnblick'
    #    lon = '12.9575'
    #    lat = '47.0542'
    #    height = '3105'

    #elif stationCode == '1003-2401':
    #    station = 'Wiener Neustadt'
    #    lon = '16.2550'
    #    lat = '47.8142'
    #    height = '265'
    
    lines = inFile.read().split('\n')
    
    outFileHourly.write('<groundSO2>\n')
    outFileHourly.write('    <siteName>' + station["station"] + '</siteName>\n')
    outFileHourly.write('    <siteLongitude>' + station["longitude"] + '</siteLongitude>\n')
    outFileHourly.write('    <siteLatitude>' + station["latitude"] + '</siteLatitude>\n')
    outFileHourly.write('    <siteElevation>' + station["height"] + '</siteElevation>\n')
    
    dailyAverage = {}
    
    for i in lines:       
        if i == '':
            continue
        
        day = i[0:4] + '-' + i[4:6] + '-' + i[6:8]
        time = i[9:11] + ':' + i[11:13] + ':' + i[13:15]
        value = i.split('  ')[1]
        
        if float(value) < 0:
            value = 'N/A'
        else:        
            try:
                dailyAverage[day].append(float(value))
            except KeyError:
                dailyAverage[day] = [float(value)]
        
        outFileHourly.write('    <data>\n')
        outFileHourly.write('        <timeStart>' + day + 'T' + time + 'Z' + '</timeStart>\n')
        outFileHourly.write('        <timeEnd>' + day + 'T' + time + 'Z' + '</timeEnd>\n')
        outFileHourly.write('        <field>' + 'SO2 Ground Measurement' + '</field>\n')
        outFileHourly.write('        <value>' + value + '</value>\n')
        outFileHourly.write('    </data>\n')        
    outFileHourly.write('</groundSO2>')    
    outFileHourly.close()    
    
    outFileNameAvg = os.path.basename(fileAbsPath)[0:-4] + '_average.xml' 
    outFileAvg = open(outFileNameAvg, 'w')
    
    outFileAvg.write('<groundSO2>\n')
    outFileAvg.write('    <siteName>' + station["station"] + '</siteName>\n')
    outFileAvg.write('    <siteLongitude>' + station["longitude"]  + '</siteLongitude>\n')
    outFileAvg.write('    <siteLatitude>' + station["latitude"] + '</siteLatitude>\n')
    outFileAvg.write('    <siteElevation>' + station["height"] + '</siteElevation>\n')
    keylist = dailyAverage.keys()
    keylist.sort()
    for key in keylist:
        date = key[0:4] + '-' + key[4:6] + '-' + key[6:8]
        avg = sum(dailyAverage[key]) / len(dailyAverage[key])
        outFileAvg.write('    <data>\n')
        outFileAvg.write('        <timeStart>' + key + 'T00:00:00Z' + '</timeStart>\n')
        outFileAvg.write('        <timeEnd>' + key + 'T23:59:59Z' + '</timeEnd>\n')
        outFileAvg.write('        <field>' + 'SO2 Daily Average' + '</field>\n')
        outFileAvg.write('        <value>' + str(avg) + '</value>\n')
        outFileAvg.write('    </data>\n')    
    outFileAvg.write('</groundSO2>')    
    outFileAvg.close()
    
    return [outFileNameHourly, outFileNameAvg]


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s Ground_SO2' % sys.argv[0])
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])
            
    extractGroundSO2Data(sys.argv[1])

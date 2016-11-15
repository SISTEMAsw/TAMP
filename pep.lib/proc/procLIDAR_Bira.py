#!/usr/bin/env python
import sys
import os
import gdal
import numpy as np
from osgeo import osr
import re
import logging
################################################################################

def calculateAltiudes(P):
    P = float(P)
    if abs(P-9.99e+29) < 0.00000001:
        return P
    else:
        h = ((1-((P/1013.25)**(0.190284)))*145366.45)
        hmeters = 0.3048 * h
        return hmeters


def makeLidarPicture(DataSet, station, headerline):
    header = findHeader(headerline)

    seq = [float(element['Ozone Number Density']) for element in DataSet]
    
    altiudes = []
    for element in DataSet:
        h = calculateAltiudes(element['Reference Pressure used (hPa)'])
        altiudes.append(h)

    timestring = header['TIME_START'].replace("-", "")
    timestring = timestring.replace("T", ".")
    timestring = timestring.replace(":", "")
    timestring = timestring.replace("Z", "")


    outFilename = 'LIDAR_BIRA_O3' + "_" + timestring + '.tif'
    driver = gdal.GetDriverByName('GTiff')
    dataType = gdal.GDT_Float32
    dst_ds = driver.Create(outFilename, 1, 1, len(altiudes), dataType)
    ozone2d = np.array([[seq]])

    for i in range(len(altiudes)):
        dst_ds.GetRasterBand(i+1).WriteArray(ozone2d[:,:,i])
        dst_ds.GetRasterBand(i+1).SetNodataValue(-9999)

    dst_ds.SetMetadataItem('AREA_OR_POINT', 'POINT')
    dst_ds.SetMetadataItem('TIME_START', header['TIME_START'])
    dst_ds.SetMetadataItem('TIME_END', header['TIME_END'])
    dst_ds.SetMetadataItem('GLOBAL_MAX', str(max(seq)))
    dst_ds.SetMetadataItem('GLOBAL_MIN', str(min(seq)))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', header['Altitude_reported'])
    dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(altiudes)[1:-1].replace(' ', ''))

    lower_left = [float(header['Longitude']), float(header['Latitude'])]
    upper_right = [float(header['Longitude']), float(header['Latitude'])]

    pixelWidth = 0.4
    pixelHeight = 0.4

    dst_ds.SetGeoTransform([lower_left[0], pixelWidth, 0, upper_right[1], 0, -pixelHeight])
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())
    dst_ds = None
    
    return outFilename



def findData(line, dataSet_Line):
    tmp = line.split()
    dataSet_Line['Ozone Number Density'] = tmp[1]
    dataSet_Line['Ozone Number Density Total Error'] = tmp[2]
    dataSet_Line['Range Resolution (meters)'] = tmp[3]
    dataSet_Line['Derived Ozone Mixing Ratio (ppmv)'] = tmp[5]
    dataSet_Line['Ozone Mixing Ratio Total Error (1 std-dev) (ppmv)'] = tmp[6]
    dataSet_Line['Reference Pressure used (hPa)'] = tmp[7]
    dataSet_Line['Reference Density used (kg/m3)'] = tmp[8]
    dataSet_Line['Derived Potential Temperature (from lidar measure) (K)'] = tmp[9]

    return dataSet_Line


def findHeader(rawDates):
    details = {}
    tmp = rawDates.split()
    for i in range(3, 9):
        if len(tmp[i]) <= 1:
            tmp[i] = "0" + tmp[i]
    startDate = tmp[2] + "-" + tmp[3] + "-" + tmp[4] + "T" + tmp[5]+ ":" + tmp[6] + ":00Z"
    details['TIME_START'] = startDate
    endDate = tmp[2] + "-" + tmp[3] + "-" + tmp[4] + "T" + tmp[7]+ ":" + tmp[8] + ":00Z"
    details['TIME_END'] = endDate
    Lat = float(tmp[10])/10
    Long = float(tmp[11])/10

    if Long >180:
        Long -= 360

    if Lat >90:
        Lat -= 180

    details['Longitude'] = Long
    details['Latitude'] = Lat
    details['Altitude'] = tmp[12]
    details['Altitude_reported'] = tmp[1]
    return details


################################################################################
def createImgLIDAR_Bira(file):
    try:
        fh = open(file, 'r')
        rawData = fh.readlines()
        fh.close()

    except Exception as e:
        logging.error("Something went wrong: ".format(e))

    tempString = rawData[0]
    tempString = tempString[32:len(tempString)]
    tempString = tempString.split()

    station = None

    # Find station
    if len(tempString) > 5:
        i = 0
        while len(tempString) > 6:
            if not station:
                station = tempString[0]
                tempString.pop(0)
            else:
                station = station + " " + tempString[i]
                tempString.pop(0)
                i += 1

    rawDataList = rawData[41:len(rawData)]

    headerline = None
    dataList = []
    outFileList = []
    
    for line in rawDataList:
        if re.search('^(\s|[1-9])[0-9]+\.[0-9]+', line):
            if not headerline:
                headerline = line
            else:
                outFileList.append(makeLidarPicture(dataList, station, headerline))
                headerline = line
                dataList[:] = []
        else:
            dataSet = {}
            dataSet = findData(line, dataSet)
            dataList.append(dataSet)

    # for the last dataset
    outFileList.append(makeLidarPicture(dataList, station, headerline))
    
    return outFileList
    
    
################################################################################

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s LIDAR_File \n' % sys.argv[0])
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])

    fileAbsPath = sys.argv[1]
    createImgLIDAR_Bira(fileAbsPath)

    exit(0)

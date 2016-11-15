#!/usr/bin/env python

import os, subprocess
from os.path import basename
import sys
import re
import pygrib
import numpy as np
import numpy.ma as ma
import gdal
import math
from gdalconst import *
from osgeo import ogr, osr
from datetime import datetime, date, timedelta

def extractProduct(fileAbsPath, grbs_name, grbs_typeOfLevel):
    grbs = pygrib.open(fileAbsPath)
    driver = gdal.GetDriverByName('GTiff')

    a_data = grbs.select(name=grbs_name, typeOfLevel=grbs_typeOfLevel)
    numBands = len(a_data)

    a_pressure = np.zeros(numBands)

    rasterXSize = len(a_data[0]['values'][0])
    rasterYSize = len(a_data[0]['values'])

    grbs.close()

    val = re.findall(r'\d+',basename(fileAbsPath))
    prefix = 'ALARO_'+a_data[0]['name'].replace(' ','_')+'_'+a_data[0]['typeOfLevel']+'_'
    dateString = str(a_data[0]['dataDate'])+str(a_data[0]['dataTime']).zfill(4)

    for i in range(numBands):
        #add single band in multibands dataset
        band = a_data[i]['values']
        band = np.flipud(band)

        a_pressure[i] = a_data[i]['level']
        #print a_temperature[i]
        try:
            dst_ds
        except NameError:
            #create new dataset if not exists. Only the first time in the loop
            outputFilename = prefix+dateString+'_'+val[1]+'.tif'
            dst_ds = driver.Create(outputFilename, rasterXSize, rasterYSize, numBands, gdal.GDT_Float64)

        if grbs_name == "Surface pressure":
            # /100 is used to convert Pa in hPa
            #dst_ds.GetRasterBand(numBands-i).WriteArray(np.flipud(band/100))
            dst_ds.GetRasterBand(numBands-i).WriteArray(band/100)
        else:
            #dst_ds.GetRasterBand(numBands-i).WriteArray(np.flipud(band))
            dst_ds.GetRasterBand(numBands-i).WriteArray(band)
        
        dst_ds.GetRasterBand(numBands-i).ComputeStatistics(False)
        
        band = None
    
    #TODO: hard-coded for now, automate it later
    if grbs_name == 'Specific humidity':
        dst_ds.SetMetadataItem('GLOBAL_MIN', '0')
        dst_ds.SetMetadataItem('GLOBAL_MAX', '1050')
    elif grbs_name == 'Temperature':
        dst_ds.SetMetadataItem('GLOBAL_MIN', '150')
        dst_ds.SetMetadataItem('GLOBAL_MAX', '350')
    elif grbs_name == 'Surface pressure':
        dst_ds.SetMetadataItem('GLOBAL_MIN', '0')
        dst_ds.SetMetadataItem('GLOBAL_MAX', '1')
        
    heightLevels = getAltitude(a_pressure)
    levels = str()
    for l in heightLevels:
        levels += str(l) + ','
    levels = levels[:-1] 
    dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(heightLevels)))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(levels))

    dateStart, dateEnd = getDateTime(fileAbsPath)
    dst_ds.SetMetadataItem('TIME_START', dateStart)
    dst_ds.SetMetadataItem('TIME_END', dateEnd)
    
    coords = getCoords(fileAbsPath)
    pixelWidth = (coords[3] - coords[1])/rasterXSize
    pixelHeight = (coords[0] - coords[2])/rasterYSize
    dst_ds.SetGeoTransform([coords[1], pixelWidth, 0, coords[0], 0, -pixelHeight])
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())
        
    del dst_ds
    return  outputFilename


def getCoords(fileAbsPath):
    grbs = pygrib.open(fileAbsPath)
    temperature_start = 64
    a_temperature = grbs[temperature_start]
    grbs.close()
    #RETURN LOWER LEFT UPPER RIGHT!!
    #coords = [ a_temperature['latitudeOfFirstGridPointInDegrees'], a_temperature['longitudeOfFirstGridPointInDegrees'], a_temperature['latitudeOfLastGridPointInDegrees'], a_temperature['longitudeOfLastGridPointInDegrees'] ]
    coords = [a_temperature['latitudeOfLastGridPointInDegrees'], a_temperature['longitudeOfFirstGridPointInDegrees'], a_temperature['latitudeOfFirstGridPointInDegrees'], a_temperature['longitudeOfLastGridPointInDegrees']]
    return coords


def getDateTime(fileAbsPath):
    val = re.findall(r'\d+',basename(fileAbsPath))
    grbs = pygrib.open(fileAbsPath)
    temperature_start = 64
    a_temperature = grbs[temperature_start]
    grbs.close()
    dateTime = str(a_temperature['dataDate'])+str(a_temperature['dataTime']).zfill(4)
    startDateTime = (datetime.strptime(dateTime, "%Y%m%d%H%M") + timedelta(hours = int(val[1]))).strftime("%Y-%m-%dT%H:%M:%SZ")
    endDateTime = startDateTime 
    del a_temperature #= None
    return startDateTime, endDateTime


def getAltitude(pressure_levels):
    levels = len(pressure_levels)
    height = np.zeros(levels)
    p0 = 101325
    t0 = 288.15
    g = 9.80665
    r = 287.053
    for i in range(len(height)):
        if pressure_levels[i] == 0:
            height[i] = 0
        else:
            height[i] = -((r*t0)/(g))* math.log(pressure_levels[i]*100/p0)
    return height[::-1]


def createImgALARO(fileAbsPath):
    outFileList = {}
    outFileList['SPECIFICHUMIDITY'] = extractProduct(fileAbsPath, 'Specific humidity', 'isobaricInhPa')
    outFileList['TEMPERATUREPROFILE'] = extractProduct(fileAbsPath, 'Temperature', 'isobaricInhPa')
    outFileList['TEMPERATURESURFACE'] = extractProduct(fileAbsPath, 'Temperature', 'surface')
    outFileList['SURFACEPRESSURE'] = extractProduct(fileAbsPath, 'Surface pressure', 'surface')
    
    return outFileList
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s ALARO_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
   
    fileAbsPath = sys.argv[1]
    
    createImgALARO(fileAbsPath)

    exit(0)

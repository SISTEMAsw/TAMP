#!/usr/bin/env python

import os,sys, subprocess, math, datetime
from os.path import basename
import numpy as np
import time as tt
import gdal
import h5py
from datetime import timedelta
from gdalconst import GDT_Float32
from osgeo import ogr, osr


def createImgAURA_L3(fileAbsPath, pixelSize=0.1):
    hdf = h5py.File(fileAbsPath, 'r')
    
    driver = gdal.GetDriverByName('GTiff')        

    lat = np.array(hdf['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/Latitude'])
    lon = np.array(hdf['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/Longitude'])
    time = np.array(hdf['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/Time'])
    data = np.array(hdf['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/ColumnAmountSO2_PBL'])
    dataAttributes = hdf['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/ColumnAmountSO2_PBL'].attrs    
    attributes = hdf['/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES'].attrs
    
    timeOffset = (datetime.date(1993, 1, 1) - datetime.date(1970, 1, 1)).days * (24*60*60)
    time += timeOffset
    
    sensor = str(attributes['InstrumentName'])
    level = str(attributes['ProcessLevel'])
    fillValue = dataAttributes['_FillValue']
    
    data[data == fillValue] = -9999
       
    dataType = GDT_Float32
    
    timeStart = attributes['StartUTC'][:19] + 'Z'
    timeEnd = attributes['EndUTC'][:19] + 'Z'
    
    year = str(attributes['GranuleYear'][0]).zfill(2)
    month = str(attributes['GranuleMonth'][0]).zfill(2)
    day = str(attributes['GranuleDay'][0]).zfill(2)
    hour = str(timeStart[11:13])
    minute = str(timeStart[14:16])
    second = str(timeStart[17:19])
    date = year + month + day + '.' + hour + minute + second
    
    xSize = data.shape[1]
    ySize = data.shape[0]
    
    filename = sensor + '_L' + level + '_SO2_' + date + '.tif'
    dst_ds = driver.Create(filename, xSize, ySize, 1, dataType)
    data[data == fillValue] = -9999
    #the image in the HDF file is flipped
    data = np.flipud(data)
    dst_ds.GetRasterBand(1).WriteArray(data)     
          
    data[data == -9999] = False          
    dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.max(data)))
    dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.min(data)))        
                    
    dst_ds.SetMetadataItem('TIME_START', timeStart)
    dst_ds.SetMetadataItem('TIME_END', timeEnd)
                     
    dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
    dst_ds.GetRasterBand(1).ComputeStatistics(False)      

    lower_left = [np.amin(lat), np.amin(lon)]
    upper_right = [np.amax(lat), np.amax(lon)]    
    pixelHeight = abs(lower_left[0]-upper_right[0]) / ySize
    pixelWidth = abs(lower_left[1]-upper_right[1]) / xSize 
    dst_ds.SetGeoTransform([lower_left[1], pixelWidth, 0, upper_right[0], 0, -pixelHeight])
    
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())
    
    dst_ds = None
    
    return [filename]
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s AURA_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
    createImgAURA_L3(fileAbsPath) 

    exit(0)
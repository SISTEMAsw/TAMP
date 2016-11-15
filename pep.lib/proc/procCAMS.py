#!/usr/bin/env python

import sys, os
import gdal
import numpy as np
from gdalconst import GDT_Float32
from osgeo import osr
from netCDF4 import Dataset

def createImgCAMS(inputPath):
    driver = gdal.GetDriverByName('GTiff')
    
    ncfile = Dataset(inputPath, 'r') 
    data = ncfile.variables['so2_conc'][:]
    xSize = data.shape[3]
    ySize = data.shape[2]
    numBands = data.shape[1]
    timestamps = data.shape[0]
    lat = ncfile.variables['latitude'][:]
    lon = ncfile.variables['longitude'][:]
    day = ncfile.variables['time'].long_name.replace('ANALYSIS time from ', '')
    ncfile.close()
    
    outFileList = []
        
    for t in range(timestamps):
        filename = 'CAMS_SO2_' + day + '.' + str(t).zfill(2) + '0000.tif'
        dst_ds = driver.Create(filename, xSize, ySize, numBands, GDT_Float32)
        
        lat = map(lambda x: x-180 if x > 90 else x, lat)
        lon = map(lambda x: x-360 if x > 180 else x, lon)
        lower_left = [lon[0], lat[-1]]
        upper_right = [lon[-1], lat[0]]
        
        for i in range(numBands):
            band = data[t,i,:,:]
            dst_ds.GetRasterBand(i+1).WriteArray(band)
            
            dst_ds.GetRasterBand(i+1).SetNoDataValue(-9999)
            dst_ds.GetRasterBand(i+1).ComputeStatistics(False)
        
            pixelWidth = abs((lower_left[0]-upper_right[0]) / xSize)
            pixelHeight = abs((lower_left[1]-upper_right[1]) / ySize)
        
            dst_ds.SetGeoTransform([lower_left[0], pixelWidth, 0, upper_right[1], 0, -pixelHeight])
            srs = osr.SpatialReference()
            srs.SetWellKnownGeogCS('WGS84')
            dst_ds.SetProjection(srs.ExportToWkt())
        
            time = day[:4] + '-' + day[4:6] + '-' + day[6:8] + 'T' + str(t).zfill(2) + ':00:00Z'
            dst_ds.SetMetadataItem('TIME_START', str(time))
            dst_ds.SetMetadataItem('TIME_END', str(time))
            
            dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.amin(data[:])))
            dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.amax(data[:])))
            dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(1))
            dst_ds = None
            
        outFileList.append(filename)
        
    return outFileList
        
if __name__ == '__main__':
    if len(sys.argv) > 2:
        sys.exit('\nUsage: %s CAMS_file(s) \n' % sys.argv[0])
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: Path %s was not found\n' % sys.argv[0])
    
    inputPaths = sys.argv[1:]
    for inputPath in inputPaths:
        createImgCAMS(inputPath)
    
    exit(0)

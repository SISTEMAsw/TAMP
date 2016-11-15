#!/usr/bin/env python

import sys, os
import gdal
import datetime
import numpy as np
from gdalconst import GDT_Float32
from osgeo import osr
from netCDF4 import Dataset

def createImgMACC(inputPath):
    driver = gdal.GetDriverByName('GTiff')
    
    ncfile = Dataset(inputPath, 'r') 
    data = ncfile.variables['tcso2']
    noDataValue = data._FillValue
    offset = data.add_offset
    scaleFactor = data.scale_factor
    data = data[:]
    xSize = data.shape[2]
    ySize = data.shape[1]-1
    numBands = 1
    timestamps = ncfile.variables['time'][:]
    lat = ncfile.variables['latitude'][:-1]
    lon = ncfile.variables['longitude'][:]
    ncfile.close()
    
    outFileList = []    
    #lon = lon-180
    #lower_left = [lat[-1], lon[0]]
    #upper_right = [lat[0], lon[-1]]
    pixelSize = 1.125
    reference_date = datetime.datetime(1900,1,1, 0,0,0)
        
    for i,t in enumerate(timestamps):
        time = reference_date + datetime.timedelta(hours=int(t))
        
        filename = 'MACC_SO2_' + time.strftime('%Y%m%d.%H%M%S') + '.tif'
        dst_ds = driver.Create(filename, xSize, ySize, numBands, GDT_Float32)
        
        band = data[i,:-1,:]
        band = band * scaleFactor
        band = band + offset
        band[band == noDataValue] = -9999
        dst_ds.GetRasterBand(1).WriteArray(band)
        
	band[band == noDataValue] = -9999
        
	dst_ds.GetRasterBand(1).WriteArray(band)
        
        dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
        dst_ds.GetRasterBand(1).ComputeStatistics(False)
    
        #pixelWidth = abs((lower_left[0]-upper_right[0]) / xSize)
        #pixelHeight = abs((lower_left[1]-upper_right[1]) / ySize)
    
        #dst_ds.SetGeoTransform([lower_left[0], pixelWidth, 0, upper_right[1], 0, -pixelHeight])
        dst_ds.SetGeoTransform([lon[0], pixelSize, 0, lat[0], 0, -pixelSize])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('WGS84')
        dst_ds.SetProjection(srs.ExportToWkt())
    
        dst_ds.SetMetadataItem('TIME_START', time.strftime('%Y-%m-%dT%H:%M:%ST'))
        dst_ds.SetMetadataItem('TIME_END', time.strftime('%Y-%m-%dT%H:%M:%ST'))
        
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
        createImgMACC(inputPath)
    
    exit(0)

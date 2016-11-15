#!/usr/bin/env python

import os, sys, subprocess
from os.path import basename,dirname
import h5py
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import gdal
from gdalconst import *
from osgeo import ogr, osr
from datetime import datetime, date

def createImgSCISAT(fileAbsPath):
    # read info from netcdf
    ncfile = Dataset(fileAbsPath, 'r')
    latitude = ncfile.groups['ACE-FTS-v2.2'].latitude
    longitude = ncfile.groups['ACE-FTS-v2.2'].longitude
    datestart = datetime.strptime(ncfile.groups['ACE-FTS-v2.2'].start_time,'%Y-%m-%d %H:%M:%S+00')
    dateend = datetime.strptime(ncfile.groups['ACE-FTS-v2.2'].end_time,'%Y-%m-%d %H:%M:%S+00')
    ozone = ncfile.groups['ACE-FTS-v2.2'].groups['Data-L2_1km_grid'].variables['O3'][:]
    heightLevels = ncfile.groups['ACE-FTS-v2.2'].groups['Data-L2_1km_grid'].variables['z'][:]
    numBand = len(ozone)
    ncfile.close()
    
    #common vars
    no_value = -9999
    minValue = ma.min(ozone)
    maxValue = ma.max(ozone)
    ma.set_fill_value(ozone, no_value)
    ozone = ozone.filled()
    #ma.set_fill_value(heightLevels, no_value)
    #heightLevels = heightLevels.filled()    
    sizeX = 1
    sizeY = 1
    dataType = gdal.GDT_Float32
    resolution = 1.0 # in degree
    driver = gdal.GetDriverByName('GTiff' ) 
    outFile = 'ACE-FTS_L2_ozone_'+datestart.strftime('%Y%m%d.%H%M%S')+'.tif'
    
    #create tiff
    dst_ds = driver.Create(outFile, sizeX, sizeY, numBand, dataType)
    for i in range(numBand):
        dst_ds.GetRasterBand(i+1).WriteArray(np.expand_dims(np.expand_dims(ozone[i],axis=0),axis=0))
        # The computed stat produces this warning 
        # Warning 1: Lost metadata writing to GeoTIFF ... too large to fit in tag.
        # An additional  *.aux.xml is added
        #if ozone[i] != no_value:
        #    dst_ds.GetRasterBand(i+1).ComputeStatistics(False)
        dst_ds.GetRasterBand(i+1).SetNoDataValue(no_value)

    #set geotrasform matrix
    top_left_x = longitude - (resolution / 2)
    w_e_pixel_resolution = resolution
    top_left_y = latitude - (resolution / 2)
    n_s_pixel_resolution = - resolution
    coord = [top_left_x, w_e_pixel_resolution, 0, top_left_y,0, n_s_pixel_resolution]
    dst_ds.SetGeoTransform(coord)
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())
    
    #set metadata
    dst_ds.SetMetadataItem('GLOBAL_MAX',str(maxValue))
    dst_ds.SetMetadataItem('GLOBAL_MIN',str(minValue))            
    dst_ds.SetMetadataItem('TIME_END', dateend.strftime('%Y-%m-%dT%H:%M:%SZ'))
    dst_ds.SetMetadataItem('TIME_START', datestart.strftime('%Y-%m-%dT%H:%M:%SZ'))        
    dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(heightLevels)))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS', ','.join(str(x) for x in heightLevels))
    
    dst_ds =None
    
    return [outFile]

if __name__ == '__main__':
        
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s L2_SCISAT_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
    outFileName = createImgSCISAT(fileAbsPath)
    

    exit(0)
# else:
    # Module is imported from another module

#!/usr/bin/env python

import os, sys, subprocess
from os.path import basename,dirname
import h5py
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import gdal
import math
from gdalconst import *
from osgeo import ogr, osr
from datetime import datetime, date

def createImgOSIRIS(fileAbsPath):
    # read info from netcdf
    ncfile = Dataset(fileAbsPath, 'r')
    ozone_concentration = ncfile.variables['ozone_concentration'][:]
    a_lat = ncfile.variables['latitude'][:] 
    a_lon = np.subtract(ncfile.variables['longitude'][:],180)
    heightLevels = ncfile.variables['altitude'][:]
    datestart = datetime.strptime(ncfile.time_coverage_start,'%Y%m%dT%H%M%SZ')
    dateend = datetime.strptime(ncfile.time_coverage_end,'%Y%m%dT%H%M%SZ')
    fillValue = ncfile.value_for_nodata
    ncfile.close()

    # raster common info
    driver = gdal.GetDriverByName('GTiff' ) 
    sizeY = 1 
    sizeX = ozone_concentration.shape[0]
    window = str(sizeX)+'x'+str(sizeY)
    numBands = ozone_concentration.shape[1]
    dataType = GDT_Float32
    no_data = -9999
    pixelSize = 0.5  
    upper_left = []
    lower_right = []
    upper_left.append(np.amax(a_lat))
    upper_left.append(np.amin(a_lon))
    lower_right.append(np.amin(a_lat))
    lower_right.append(np.amax(a_lon))
    prefix = 'LPL2OSIRIS_ozone_concentration_'
    maxValue = np.max(ozone_concentration) #ma.masked_equal(ozone_concentration,fillValue))
    minValue = np.min(ozone_concentration) #ma.masked_equal(ozone_concentration,fillValue))
    

    # create lat lon tif
    coordsFilename = prefix+'coord_'+datestart.strftime('%Y%m%d.%H%M%S')+'.tif'
    coord_ds = driver.Create(coordsFilename, sizeX , sizeY, 2, gdal.GDT_Float32 )
    tmp_array = np.empty([1,len(a_lat)])
    tmp_array[0,...] = a_lat[...]
    coord_ds.GetRasterBand(1).WriteArray(tmp_array)
    tmp_array[0,...] = a_lon[...]
    coord_ds.GetRasterBand(2).WriteArray(tmp_array)
    coord_ds = None
    
    # 1st band
    tmpOutFile = prefix +'tmp_'+datestart.strftime('%Y%m%d.%H%M%S')+'.tif'
    data_ds = driver.Create(tmpOutFile, sizeX, sizeY, 1, dataType)
    band = ozone_concentration[...,0]
    band[band == fillValue] = no_data
    maxValue=np.max(ma.masked_equal(band,no_data))
    minValue=np.min(ma.masked_equal(band,no_data))   
    data_ds.GetRasterBand(1).WriteArray(np.expand_dims(band, axis=0))     
    data_ds = None
    
    # remapping mask
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    command_call = [workingDir + 'bin/remap', '-i', tmpOutFile,
                    '-l', str(upper_left[0]), str(upper_left[1]), 
                    '-e', str(lower_right[0]), ',', str(lower_right[1]), 
                    '-a', coordsFilename, '-s', str(pixelSize), 
                    '-w', window, '-f',  '100000',
                    '-n', str(no_data), '-q', '-o', tmpOutFile + '_mask']

    # remapping 1st band 
    mask_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))
    command_call.pop()
    command_call.append(tmpOutFile + '_remapped')
    command_call.append('-c')
    mask_process.wait()
    coord_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))        
    coord_process.wait()

    remap_ds = gdal.Open(tmpOutFile + '_remapped', gdal.GA_ReadOnly)
    transform_i = remap_ds.GetRasterBand(1).ReadAsArray().transpose()
    transform_j = remap_ds.GetRasterBand(2).ReadAsArray().transpose()
    mask_ds = gdal.Open(tmpOutFile + '_mask', gdal.GA_ReadOnly)
    mask = mask_ds.GetRasterBand(1).ReadAsArray().transpose()  
      

    #test
    #numBands = 1
 
    # creating outpufile
    filenameOutput_ozone_concentration = prefix+datestart.strftime('%Y%m%d.%H%M%S')+'.tif'
    dst_ds = driver.Create(filenameOutput_ozone_concentration, transform_j.shape[0], transform_j.shape[1], numBands, gdal.GDT_Float32)
    for k in range(numBands):
        #print "Remapp band ", k
        outData = np.ones([transform_j.shape[0], transform_j.shape[1]]) * no_data
        band = np.expand_dims( ozone_concentration[...,k], axis=0)    
        for i in range(outData.shape[0]):
            for j in range(outData.shape[1]):
                #print  transform_j[i,j], transform_i[i,j]
                #print band.shape
                if band[ transform_j[i,j], transform_i[i,j]] != no_data:
                    outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]
                else: 
                    outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]
        outData[mask==no_data] = no_data
        dst_ds.GetRasterBand(k+1).WriteArray(outData.transpose())
        dst_ds.GetRasterBand(k+1).SetNoDataValue(-9999)
        dst_ds.GetRasterBand(k+1).ComputeStatistics(False)

    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())
    dst_ds.SetMetadataItem('GLOBAL_MAX',str(maxValue))
    dst_ds.SetMetadataItem('GLOBAL_MIN',str(minValue))            
    dst_ds.SetMetadataItem('TIME_END', dateend.strftime('%Y-%m-%dT%H:%M:%SZ'))
    dst_ds.SetMetadataItem('TIME_START', datestart.strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(heightLevels)))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS', ','.join(str(x) for x in heightLevels))
    #remove temporary files
    os.system('rm '+ tmpOutFile+ '*')
    os.system('rm '+ prefix+'coord_'+datestart.strftime('%Y%m%d.%H%M%S')+'.tif')
 
    return [filenameOutput_ozone_concentration]

if __name__ == '__main__':
        
    #fileAbsPath = '/media/moris/STORAGE/VMANIP/INPUT/OZONE/LIMB_PROFILE/L2/ODIN/OSIRIS/ESACCI-OZONE-L2-LP-OSIRIS_ODIN-SASK_V5_7-200809-fv0007.nc' 
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s LPL2_OSIRIS_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
    
    outFileName = createImgOSIRIS(fileAbsPath)
    

    exit(0)
# else:
    # Module is imported from another module

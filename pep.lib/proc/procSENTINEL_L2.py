#!/usr/bin/env python

import numpy.ma as ma
import os,sys, subprocess, math, datetime
from os.path import basename
import numpy as np
import time as tt
import gdal
import h5py
from datetime import timedelta,datetime
from gdalconst import GDT_Float32, GA_Update
from osgeo import ogr, osr

def createImgSENTINEL_L2(fileAbsPath, pixelSize=0.1):
    #fileAbsPath='S5P_NRTI_L2__SO2____20080808T224727_20080808T234211_21635_01_021797_00000000T000000.nc'
    filename = os.path.basename(fileAbsPath)
    instrument = filename.split('_')[0]
    product = filename[4:19]
    date = datetime.strptime(filename[20:35],'%Y%m%dT%H%M%S').strftime('%Y%m%d.%H%M%S')
    outFileList = []
    hdf = h5py.File(fileAbsPath, 'r')
    
    driver = gdal.GetDriverByName('GTiff')        
    coordFillValue = hdf['PRODUCT']['latitude'].attrs['_FillValue'][0]
    
    #searching the last valid column
    for i in range(np.array(hdf['PRODUCT']['latitude']).shape[1]):
        if np.array(hdf['PRODUCT']['latitude'])[0,i] == coordFillValue:
            break
    
    lat = np.array(hdf['PRODUCT']['latitude'][:,:i])
    lon = np.array(hdf['PRODUCT']['longitude'][:,:i])
    so2_vertical_column = np.array(hdf['PRODUCT']['so2_vertical_column'][0,:,:i]) #/100000000000000000000000000000000000 
    qa_value = np.array(hdf['PRODUCT']['qa_value'][0,:,:i])
    dataType = GDT_Float32
    xSize = lat.shape[1] 
    ySize = lat.shape[0] 
    no_data = -9999
    fillValue = hdf['PRODUCT']['so2_vertical_column'].attrs['_FillValue']
    
    #workingDir='/home/tamp/pep.lib/'
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    
    timeStart = datetime.strptime(filename[20:35],'%Y%m%dT%H%M%S').strftime('%Y-%m-%dT%H:%M:%SZ')
    timeEnd = datetime.strptime(filename[36:51],'%Y%m%dT%H%M%S').strftime('%Y-%m-%dT%H:%M:%SZ')
        
    filenameCoords = 'SENTINEL_Coords_' + date + '.tif'
    coord_ds = driver.Create(filenameCoords, xSize, ySize, 2, dataType)
    coord_ds.GetRasterBand(1).WriteArray(lat)
    coord_ds.GetRasterBand(2).WriteArray(lon)
    coord_ds = None
    
    tmpOutFile_so2_vertical_column = instrument + '_SO2_VERTICAL_COLUMN_L2_' + date + '_tmp.tif'
    data_ds = driver.Create(tmpOutFile_so2_vertical_column, xSize, ySize, 1, dataType)
    band = so2_vertical_column
    band[band == fillValue] = no_data
    maxValue=np.max(ma.masked_equal(band,no_data))
    minValue=np.min(ma.masked_equal(band,no_data))
    data_ds.GetRasterBand(1).WriteArray(band)     
    data_ds = None
    window = str(xSize)+'x'+str(ySize)
    upper_left = []
    lower_right = []
    upper_left.append(np.amax(lat))
    upper_left.append(np.amin(lon))
    lower_right.append(np.amin(lat))
    lower_right.append(np.amax(lon))
    
            
    command_call = [workingDir + 'bin/remap', '-i', tmpOutFile_so2_vertical_column , '-l', str(upper_left[0]), str(upper_left[1]), '-e', str(lower_right[0])+','+ str(lower_right[1]), '-a', filenameCoords, '-s', str(pixelSize), '-n', str(no_data), '-q', '-o', tmpOutFile_so2_vertical_column+ '_mask','-f','60000']
        
    mask_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))
    # remove tmpOutFile_so2_vertical_column++'_mask','-f','60000' from command_call
    command_call.pop()
    command_call.pop()
    command_call.pop()
    command_call.append(tmpOutFile_so2_vertical_column+'_remapped')
    command_call.append('-c')
    coord_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))       
    mask_process.wait() 
    coord_process.wait()
    
    remap_ds = gdal.Open(tmpOutFile_so2_vertical_column+'_remapped', gdal.GA_ReadOnly)
    transform_i = remap_ds.GetRasterBand(1).ReadAsArray().transpose()
    transform_j = remap_ds.GetRasterBand(2).ReadAsArray().transpose()
    mask_ds = gdal.Open(tmpOutFile_so2_vertical_column + '_mask', gdal.GA_ReadOnly)
    mask = mask_ds.GetRasterBand(1).ReadAsArray().transpose()
    
    filenameOutput_so2_vertical_column = instrument + '_SO2_VERTICAL_COLUMN_L2_' + date + '.tif'
    dst_ds = driver.Create(filenameOutput_so2_vertical_column, transform_j.shape[0], transform_j.shape[1], 1, gdal.GDT_Float32) 
    outData = np.ones([transform_j.shape[0], transform_j.shape[1]]) * no_data
    band = so2_vertical_column  
    for i in range(outData.shape[0]):
        for j in range(outData.shape[1]):
            if band[ transform_j[i,j], transform_i[i,j]] != no_data:
                outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]
            else: 
                outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]
    outData[mask==no_data] = no_data
    dst_ds.GetRasterBand(1).WriteArray(outData.transpose())
    dst_ds.SetGeoTransform([upper_left[1], pixelSize, 0, upper_left[0], 0, -pixelSize])
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())
    dst_ds.SetMetadataItem('GLOBAL_MAX',str(maxValue))
    dst_ds.SetMetadataItem('GLOBAL_MIN',str(minValue))            
    dst_ds.SetMetadataItem('TIME_END', timeEnd)
    dst_ds.SetMetadataItem('TIME_START', timeStart)
    dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
    dst_ds.GetRasterBand(1).ComputeStatistics(False)
    dst_ds = None      
    
    
    filenameOutput_qa_value = instrument + '_SO2_QA_VALUE_L2_' + date + '.tif'
    dst_ds = driver.Create(filenameOutput_qa_value, transform_j.shape[0], transform_j.shape[1], 1, gdal.GDT_Float32)
    outData = np.ones([transform_j.shape[0], transform_j.shape[1]]) * no_data
    band = qa_value
    for i in range(outData.shape[0]):
        for j in range(outData.shape[1]):
            if band[ transform_j[i,j], transform_i[i,j]] != no_data:
                outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]
            else:
                outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]
    outData[mask==no_data] = no_data
    dst_ds.GetRasterBand(1).WriteArray(outData.transpose())
    dst_ds.SetGeoTransform([upper_left[1], pixelSize, 0, upper_left[0], 0, -pixelSize])
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())
    dst_ds.SetMetadataItem('GLOBAL_MAX',str(np.max(ma.masked_equal(band,no_data))))
    dst_ds.SetMetadataItem('GLOBAL_MIN',str(np.min(ma.masked_equal(band,no_data))))
    dst_ds.SetMetadataItem('TIME_END', timeEnd)
    dst_ds.SetMetadataItem('TIME_START', timeStart)
    dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
    dst_ds.GetRasterBand(1).ComputeStatistics(False)
    dst_ds = None
    

    outFileList.append(filenameOutput_so2_vertical_column)
    outFileList.append(filenameOutput_qa_value)
    #os.system('rm ' +tmpOutFile_so2_vertical_column)
    #os.system('rm ' + tmpOutFile_so2_vertical_column + '_mask')
    #os.system('rm ' + tmpOutFile_so2_vertical_column + '_remapped')
    #os.system('rm ' + filenameCoords)
    
    return outFileList
        

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s SENTINEL_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
    createImgSENTINEL_L2(fileAbsPath) 

    exit(0)

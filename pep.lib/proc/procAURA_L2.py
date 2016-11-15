#!/usr/bin/env python

import os,sys, subprocess, math, datetime
from os.path import basename
import numpy as np
import time as tt
import gdal
import h5py
from datetime import timedelta
from gdalconst import GDT_Float32, GA_Update
from osgeo import ogr, osr
from osgeo.gdalconst import GA_ReadOnly
import logging

#TODO: change fileIdentifyer to handle Aerosol files

def extract_product(fileAbsPath, productType, pixelSize=0.1):
    hdf = h5py.File(fileAbsPath, 'r')
    
    driver = gdal.GetDriverByName('GTiff')
    dataType = GDT_Float32
    cnt = 0
    
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    processes = []
    outputFiles = {}

    if productType == 'SO2':
        hdfGroup = '/HDFEOS/SWATHS/OMI Total Column Amount SO2/'
        data = np.array(hdf[hdfGroup + 'Data Fields/SO2indexP1'])
        dataAttributes = hdf[hdfGroup + 'Data Fields/SO2indexP1'].attrs
        
    else:
        hdfGroup = '/HDFEOS/SWATHS/ColumnAmountAerosol/'
        data = np.array(hdf[hdfGroup + 'Data Fields/AerosolOpticalThicknessMW'])
        dataAttributes = hdf[hdfGroup + 'Data Fields/AerosolOpticalThicknessMW'].attrs        
        if productType == 'AOT367':
            data = data[:,:,1]
        elif productType == 'AOT388':
            data = data[:,:,3]            
        elif productType == 'AOT451':
            data = data[:,:,10]
        elif productType == 'AOT483':
            data = data[:,:,13]
    
    lat = np.array(hdf[hdfGroup + 'Geolocation Fields/Latitude'])
    lon = np.array(hdf[hdfGroup + 'Geolocation Fields/Longitude'])
    missingValueLonLat = hdf[hdfGroup + 'Geolocation Fields/Latitude'].attrs['MissingValue']
    time = np.array(hdf[hdfGroup + 'Geolocation Fields/Time'])
    attributes = hdf['/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES'].attrs
    
    timeOffset = (datetime.date(1993, 1, 1) - datetime.date(1970, 1, 1)).days * (24*60*60)
    time += timeOffset
    
    sensor = str(np.squeeze(attributes['InstrumentName']))
    level = str(np.squeeze(attributes['ProcessLevel']))
    fillValue = dataAttributes['_FillValue']
    scaleFactor = dataAttributes['ScaleFactor']
    
    ySize = lat.shape[1]
        
    stepSize = 200
    
    for i in range(0,len(lat),stepSize):            
        if i + stepSize > len(lat):
            stepSize = len(lat)-i
        
        timeSlice = time[i:stepSize+i]        
        timeAvg = datetime.datetime.fromtimestamp(np.average(timeSlice))
        date = str(timeAvg.year) + str(timeAvg.month).zfill(2) + str(timeAvg.day).zfill(2) + '.' + str(timeAvg.hour).zfill(2) + str(timeAvg.minute).zfill(2) + str(timeAvg.second).zfill(2)
        timeStart = timeSlice[0]
        timeEnd = timeSlice[-1]
        latSlice = lat[i:stepSize+i][:]
        lonSlice = lon[i:stepSize+i][:]
        latSlice = np.ma.compress_cols(np.ma.masked_where(latSlice == missingValueLonLat, latSlice))
        lonSlice = np.ma.compress_cols(np.ma.masked_where(lonSlice == missingValueLonLat, lonSlice))
        upper_left = (latSlice[0][0], lonSlice[0][0])
        lower_right = (latSlice[-1][-1], lonSlice[-1,-1])
                
        filenameCoords = 'AURA_Coords_' + date + '.tif'
        coord_ds = driver.Create(filenameCoords, ySize, stepSize, 2, dataType)
        coord_ds.GetRasterBand(1).WriteArray(latSlice)
        coord_ds.GetRasterBand(2).WriteArray(lonSlice)        
        coord_ds = None
        
        filename = sensor + '_L' + level + '_' + productType + '_' + date + '_tmp.tif'
        filenameOutput = filename[0:-8] + '.tif'
            
        data_ds = driver.Create(filename, ySize, stepSize, 1, dataType)
                            
        outputFiles[filenameOutput] = (timeStart, timeEnd)
                        
        band = data[i:stepSize+i][:]        
        band = band * scaleFactor
        band[band == fillValue*scaleFactor] = -9999
        data_ds.GetRasterBand(1).WriteArray(band)
        data_ds = None
        
        processes.append(((subprocess.Popen([workingDir + '/bin/remap', '-i', filename, '-o', filenameOutput, '-a', filenameCoords,'-q','-s', str(pixelSize),'-n','-9999', '-f' , '70000', '-l', str(upper_left[0]), str(upper_left[1]), '-e', str(lower_right[0])+','+str(lower_right[1])], stdout=open(os.devnull, 'wb')), filenameOutput, cnt)))     
        cnt += 1
    
    numProcesses = cnt-1
        
    while processes:
        for p in processes:            
            if p[0].poll() != None:
                logging.debug('Finished remapping for ' + p[1])
                processes.remove(p)
            
        tt.sleep(0.05)        
        
    os.system('rm ' + filenameCoords[0:11] + '*')
    os.system('rm ' + '*_tmp.tif')        
    
    for k in outputFiles:
        dst_ds = gdal.Open(k, gdal.GA_Update)
        xSize = dst_ds.RasterXSize
        ySize = dst_ds.RasterYSize

        dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
        dst_ds.GetRasterBand(1).ComputeStatistics(False)

        data[data == -9999] = False
        dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.max(data)))
        dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.min(data)))
        
        timeStart = datetime.datetime.fromtimestamp(outputFiles[k][0])
        timeEnd = datetime.datetime.fromtimestamp(outputFiles[k][1])
        timeStart = str(timeStart.year) + '-' + str(timeStart.month).zfill(2) + '-' + str(timeStart.day).zfill(2) + 'T' + str(timeStart.hour).zfill(2) + ':' + str(timeStart.minute).zfill(2) + ':' + str(timeStart.second) + 'Z'
        timeEnd = str(timeEnd.year) + '-' + str(timeEnd.month).zfill(2) + '-' + str(timeEnd.day).zfill(2) + 'T' + str(timeEnd.hour).zfill(2) + ':' + str(timeEnd.minute).zfill(2) + ':' + str(timeEnd.second) + 'Z'
        dst_ds.SetMetadataItem('TIME_START', str(timeStart))
        dst_ds.SetMetadataItem('TIME_END', str(timeEnd))
        
        dst_ds = None
        
    return outputFiles.keys()



def createImgAURA_L2_SO2(fileAbsPath):
    return extract_product(fileAbsPath, 'SO2')



def createImgAURA_L2_AEROSOL(fileAbsPath):
    outFiles = []
    productTypes = ['AOT367', 'AOT388', 'AOT451', 'AOT483']
    
    for i in productTypes:
        for j in extract_product(fileAbsPath, i):
            outFiles.append(j)            
    return outFiles



if __name__ == '__main__':    
    if len(sys.argv) < 2:
        sys.exit('\nUsage: %s AURA_file(s) \n' % sys.argv[0] )
    
    start = tt.time()     
    files = sys.argv[1:]
    for file in files:
        if not os.path.exists(file):
            print '\nERROR: File %s was not found!\n' % file            
        try:
            createImgAURA_L2_SO2(os.path.abspath(file))
        except:
            createImgAURA_L2_AEROSOL(os.path.abspath(file))

    print 'Processing took ' + str(tt.time() - start) + ' seconds'
    exit(0)

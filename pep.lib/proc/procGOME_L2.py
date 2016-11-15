#!/usr/bin/env python

import numpy.ma as ma
import os,sys, subprocess, math, datetime
from os.path import basename
import numpy as np
import time as tt
import gdal
import h5py
from datetime import timedelta
from gdalconst import GDT_Float32, GA_Update
from osgeo import ogr, osr
import logging

#TODO: change for handling of SUB data
#def extractProduct(lat, lon, time, data, dataAttributes, attributes):

def createImgGOME_L2(fileAbsPath, pixelSize=0.25):
    hdf = h5py.File(fileAbsPath, 'r')
    
    driver = gdal.GetDriverByName('GTiff')        

    lat = np.array(hdf['/GEOLOCATION/LatitudeCentre'])
    lon = np.array(hdf['/GEOLOCATION/LongitudeCentre'])
    lon = -180*(lon.astype(int)/180) + (lon%180)
    time = np.array(hdf['/GEOLOCATION/Time'])
    data = np.array(hdf['/TOTAL_COLUMNS/SO2'])
    dataAttributes = hdf['/TOTAL_COLUMNS/SO2'].attrs
    metadata = hdf['/META_DATA'].attrs
    
    time_computed = []
    for i in range(len(time)):
		time_computed.append(tt.mktime((datetime.datetime(1950, 1, 1)+timedelta(days=int(time['Day'][i]))+timedelta(milliseconds=int(time['MillisecondOfDay'][i]))).timetuple()))

    instrument = metadata['InstrumentID'][0]
    level = 'L'+metadata['ProcessingLevel'][0]
    fillValue = dataAttributes['FillValue'][0]
    satellite = metadata['SatelliteID'][0]
       
    dataType = GDT_Float32
    stepSize = 1500
    cnt = 0    
    ySize = 1 
    
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    processes = []
    outFileList = []
    
    for i in range(0,len(lat),stepSize):
        if i + stepSize > len(lat):
            stepSize = len(lat)-i
        timeSlice = time_computed[i:stepSize+i]
        timeAvg = np.average(timeSlice)
        date = datetime.datetime.fromtimestamp(timeAvg).strftime('%Y%m%d.%H%M%S')
        timeStart = timeSlice[0]
        timeEnd = timeSlice[-1]        
        
        filenameCoords = 'GOME_Coords_' + date + '.tif'
        coord_ds = driver.Create(filenameCoords, stepSize, ySize, 2, dataType)
        coord_ds.GetRasterBand(1).WriteArray(np.reshape(lat[i:stepSize+i],(stepSize,1)).transpose())
        coord_ds.GetRasterBand(2).WriteArray(np.reshape(lon[i:stepSize+i],(stepSize,1)).transpose())
        
        coord_ds = None
        filename = instrument + '_' +satellite + '_' + level + '_SO2_' + date + '_tmp.tif'
        filenameOutput = filename[0:-8] + '.tif'
        data_ds = driver.Create(filename, stepSize, ySize, 1, dataType)
        band = np.reshape(data[i:stepSize+i],(stepSize,1)).transpose()
        band[band == fillValue] = -9999
        maxValue=np.max(ma.masked_equal(band,-9999))
        minValue=np.min(ma.masked_equal(band,-9999))
        data_ds.GetRasterBand(1).WriteArray(band)     
        data_ds = None
        window = str(stepSize)+'x'+str(ySize)
        processes.append((subprocess.Popen([workingDir + '/bin/remap', '-i', filename, '-o', filenameOutput, '-a', filenameCoords,'-q','-s', str(pixelSize),'-w',window ,'-f','80000','-n','-9999'], stdout=open(os.devnull, 'wb')), filenameOutput,timeStart, timeEnd,maxValue,minValue ))
        outFileList.append(filenameOutput)
        cnt += 1
#        print subprocess.Popen([workingDir + '/bin/remap', '-i', filename, '-o', filenameOutput, '-a', filenameCoords,'-q','-s', str(pixelSize),'-w',window ,'-f','80000','-n','-9999'], stdout=open(os.devnull, 'wb')), filenameOutput,timeStart, timeEnd,maxValue,minValue 
    numProcesses = cnt-1
    while processes:
        for p in processes:            
            if p[0].poll() != None:
                logging.debug( 'Finished remapping for ' + p[1])
                dst_ds = gdal.Open(p[1], GA_Update)      
                dst_ds.SetMetadataItem('GLOBAL_MAX', str(p[4]))
                dst_ds.SetMetadataItem('GLOBAL_MIN', str(p[5]))            
                timeStart = datetime.datetime.fromtimestamp(p[2])
                timeStart = timeStart.strftime('%Y-%m-%dT%H:%M:%SZ')
                timeEnd = datetime.datetime.fromtimestamp(p[3])
                timeEnd = timeEnd.strftime('%Y-%m-%dT%H:%M:%SZ')
                dst_ds.SetMetadataItem('TIME_START', timeStart)
                dst_ds.SetMetadataItem('TIME_END', timeEnd)
                     
                dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
                dst_ds.GetRasterBand(1).ComputeStatistics(False)
                                    
                dst_ds = None      
                processes.remove(p)          
            
        tt.sleep(0.1)
        
    os.system('rm ' + filenameCoords[0:11] + '*')
    os.system('rm ' + filename[0:11] + '*_tmp.tif')
    
    return outFileList
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s GOME_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
    createImgGOME_L2(fileAbsPath) 

    exit(0)

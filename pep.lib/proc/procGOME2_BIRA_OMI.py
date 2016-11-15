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

#TODO: change for handling of SUB data
#def extractProduct(lat, lon, time, data, dataAttributes, attributes):

def createImgGOME2_BIRA_OMI(fileAbsPath, pixelSize=0.25):
    filename = os.path.basename(fileAbsPath)
    instrument = filename.split('-')[0]
    product = filename.split('-')[1]
    sub_product = filename.split('-')[2]
    date_extracted = (filename.split('-')[3]).split('_')[0]
    level='L2'
    outFileList = []
    hdf = h5py.File(fileAbsPath, 'r')
    
    driver = gdal.GetDriverByName('GTiff')        

    lat = np.array(hdf['latitude'])
    lon = np.array(hdf['longitude'])
    time = np.array(hdf['Time'])
    data_2D = np.array(hdf['SO2 vcd'])
    data_3D = np.array(hdf['SO2 averaging kernel'])
    height = np.array(hdf['SO2 altitude grid'])
    time_computed = []
    for i in range(len(time)):
        time_computed.append(tt.mktime(datetime.strptime(date_extracted+'T'+str(int(time[i])).rjust(9,'0'),'%Y%m%dT%H%M%S%f').timetuple()))
    dataType = GDT_Float32
    if instrument == 'GOME2B': 
        stepSize = 1500
    else:
        stepSize = 4000
    no_data = -9999
    fillValue = -9999
    
    ySize = 1 
    
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    processes = []
    
    for i in range(0,len(lat),stepSize):
        if i + stepSize > len(lat):
            stepSize = len(lat)-i
        timeSlice = time_computed[i:stepSize+i]
        timeAvg = np.average(timeSlice)
        date = datetime.fromtimestamp(timeAvg).strftime('%Y%m%d.%H%M%S')
        timeStart = datetime.fromtimestamp(timeSlice[0]).strftime('%Y-%m-%dT%H:%M:%SZ')
        timeEnd = datetime.fromtimestamp(timeSlice[-1]).strftime('%Y-%m-%dT%H:%M:%SZ') 
        
        filenameCoords = 'GOME_Coords_' + date + '.tif'
        coord_ds = driver.Create(filenameCoords, stepSize, ySize, 2, dataType)
        coord_ds.GetRasterBand(1).WriteArray(np.reshape(lat[i:stepSize+i],(stepSize,1)).transpose())
        coord_ds.GetRasterBand(2).WriteArray(np.reshape(lon[i:stepSize+i],(stepSize,1)).transpose())
        coord_ds = None
        tmpOutFile_2D = instrument + '_' + product + '_' + level + '_2D_' + date + '_tmp.tif'
        filenameOutput_2D = tmpOutFile_2D[0:-8] + '.tif'
        data_ds = driver.Create(tmpOutFile_2D, stepSize, ySize, 1, dataType)
        #TODO: To convert from DU to ug/cm3
        band = np.reshape(data_2D[i:stepSize+i],(stepSize,1)).transpose()     
        band[band == fillValue] = no_data
        maxValue=np.max(ma.masked_equal(band,no_data))
        minValue=np.min(ma.masked_equal(band,no_data))
        data_ds.GetRasterBand(1).WriteArray(band)     
        data_ds = None
        window = str(stepSize)+'x'+str(ySize)
        
        upper_left = []
        lower_right = []
        upper_left.append(np.amax(lat[i:stepSize+i]))
        upper_left.append(np.amin(lon[i:stepSize+i]))
        lower_right.append(np.amin(lat[i:stepSize+i]))        
        lower_right.append(np.amax(lon[i:stepSize+i]))    

        workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
        if instrument == 'GOME2B':
            command_call = [workingDir + 'bin/remap', '-i', tmpOutFile_2D, '-l', str(upper_left[0]), str(upper_left[1]), '-e', str(lower_right[0])+','+ str(lower_right[1]), '-a', filenameCoords, '-s', str(pixelSize),'-w',str(window), '-n', str(no_data), '-q', '-o', filenameOutput_2D+ '_mask','-f','60000']
        else:
            command_call = [workingDir + 'bin/remap', '-i', tmpOutFile_2D, '-l', str(upper_left[0]), str(upper_left[1]), '-e', str(lower_right[0])+','+ str(lower_right[1]), '-a', filenameCoords, '-s', '0.1','-w',str(window), '-n', str(no_data), '-q', '-o', filenameOutput_2D+ '_mask','-f','50000']
        
        mask_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))
        # rremove filenameOutput_2D+'_mask','-f','60000' from command_call
        command_call.pop()
        command_call.pop()
        command_call.pop()
        command_call.append(filenameOutput_2D+'_remapped')
        command_call.append('-c')
        coord_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))        
        coord_process.wait()
        mask_process.wait()

        remap_ds = gdal.Open(filenameOutput_2D+'_remapped', gdal.GA_ReadOnly)
        transform_i = remap_ds.GetRasterBand(1).ReadAsArray().transpose()
        transform_j = remap_ds.GetRasterBand(2).ReadAsArray().transpose()
        mask_ds = gdal.Open(filenameOutput_2D + '_mask', gdal.GA_ReadOnly)
        mask = mask_ds.GetRasterBand(1).ReadAsArray().transpose()


        dst_ds = driver.Create(filenameOutput_2D, transform_j.shape[0], transform_j.shape[1], 1, gdal.GDT_Float32) 
        outData = np.ones([transform_j.shape[0], transform_j.shape[1]]) * no_data
        band = np.reshape(data_2D[i:stepSize+i],(stepSize,1)).transpose()
        for i in range(outData.shape[0]):
            for j in range(outData.shape[1]):
                outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]
        outData[mask==no_data] = no_data
        #starting from 0? so I add (+1)
        dst_ds.GetRasterBand(1).WriteArray(outData.transpose())

        #2D metadata
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
    
        # 3D
        heightLevels = []
        numBands = data_3D.shape[0]
        
        filenameOutput_3D = instrument + '_' + product + '_' + level + '_3D_' + date + '.tif' 
        dst_ds = driver.Create(filenameOutput_3D, transform_j.shape[0], transform_j.shape[1], numBands, gdal.GDT_Float32) 
        for l in range(numBands):
            outData = np.ones([transform_j.shape[0], transform_j.shape[1]]) * no_data
            band = np.reshape(data_3D[l,i:stepSize+i],(stepSize,1)).transpose()
            avg = np.average(height[l][i:stepSize+i])
            if avg < 0:
                avg = 0
            heightLevels.append(avg*1000)
            for i in range(outData.shape[0]):
                for j in range(outData.shape[1]):
                    outData[i, j] = band[ transform_j[i,j], transform_i[i,j]]

            outData[mask==no_data] = no_data
            #starting from 0? so I add (+1)
            dst_ds.GetRasterBand(l+1).SetNoDataValue(no_data)
            dst_ds.GetRasterBand(l+1).WriteArray(outData.transpose())
            dst_ds.GetRasterBand(l+1).ComputeStatistics(False)
    
        #3D metadata
        dst_ds.SetGeoTransform([upper_left[1], pixelSize, 0, upper_left[0], 0, -pixelSize])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('WGS84')
        dst_ds.SetProjection(srs.ExportToWkt())
        
        dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.max(band)))
        dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.min(band)))
         
        dst_ds.SetMetadataItem('TIME_END', timeEnd)
        dst_ds.SetMetadataItem('TIME_START', timeStart)
            
        dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(heightLevels)))
        dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(heightLevels).replace(' ', '')[1:-1])
            
        dst_ds = None
        
        outFileList.append(filenameOutput_2D)
        outFileList.append(filenameOutput_3D)
        os.system('rm ' + tmpOutFile_2D)
        os.system('rm ' + filenameOutput_2D + '_mask')
        os.system('rm ' + filenameOutput_2D + '_remapped')
        
    os.system('rm ' + filenameCoords[0:11] + '*')
    return outFileList
        

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s GOME_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
    createImgGOME2_BIRA_OMI(fileAbsPath) 

    exit(0)

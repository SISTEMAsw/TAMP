#!/usr/bin/env python

import os,sys, subprocess, math
from os.path import basename, dirname
import numpy as np
import gdal
import osr
import multiprocessing
import time
from gdalconst import GA_ReadOnly, GA_Update, GDT_Float32 
from datetime import datetime
import logging

#TODO: Refactoring!
def extactProduct(src_ds,index_band_hdf,prefix,sizeX,sizeY,bandList,outFileName_Coords,dateString, dateStart, dateEnd, optionalBand = None):
    subDsName = src_ds.GetSubDatasets()[index_band_hdf][0]
    subDs = gdal.Open( subDsName, GA_ReadOnly )
    driver = gdal.GetDriverByName( 'GTiff' )
    numBands = len(bandList)
    #dataType = subDs.GetRasterBand(1).DataType
    dataType = GDT_Float32
    #prefix = 'MOD07_Retrived_Temperature_profiles_'
    outFileName = prefix + dateString + '.tif'
    
    cpuCount = multiprocessing.cpu_count()
    filenameList = []
    remappedFileList = []
    
    for i in range(numBands):
        filename_sl = prefix + str(i+1).zfill(2)
        data_ds = driver.Create(filename_sl+'.tif', sizeX , sizeY, 1, dataType)
        band = subDs.GetRasterBand(bandList[i]+1).ReadAsArray()
        scale_factor = float(subDs.GetMetadata()['scale_factor'])
        offset = float(subDs.GetMetadata()['add_offset'])
        valid_range = subDs.GetMetadata()['valid_range']

        range_start = int(valid_range.split(', ')[0])
        range_end = int(valid_range.split(', ')[1])
        data_ds.GetRasterBand(1).WriteArray(scale_factor*(np.array(band)-offset))
        data_ds = None
        bandRemapped = filename_sl+'_remapped.tif'
        
        filenameList.append(filename_sl)
        remappedFileList.append(bandRemapped) 
        
    filenameList.reverse()
    finishedJobs = 0;
    activeJobs = 0;
    joblist = []
    
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    
    while finishedJobs < numBands:
        if activeJobs < cpuCount:
            if len(filenameList) > 0:
                fn = filenameList.pop()
                joblist.append(subprocess.Popen([workingDir + '/bin/remap', '-i', fn+'.tif', '-o', fn+'_remapped.tif', '-a', outFileName_Coords, '-q', '-s', '0.05','-n','-9999'], stdout=open(os.devnull, 'wb')))
                activeJobs += 1
            
        i = 0
        while i < activeJobs:
            if joblist[i].poll() != None:
                joblist.pop(i)
                finishedJobs += 1
                activeJobs -= 1
                logging.debug('Remapped '+prefix+' Band: %s of %s' %  (str(finishedJobs).zfill(2), str(numBands).zfill(2)))
            i += 1
                
        time.sleep(0.5)
    
    remap_ds = gdal.Open(remappedFileList[0], GA_Update)
    band = remap_ds.GetRasterBand(1).ReadAsArray()
    
        
    dst_ds = driver.Create(outFileName, band.shape[1], band.shape[0] , numBands, dataType)
    geotransform = remap_ds.GetGeoTransform()
        
    #keep corner coordinates
    if not geotransform is None:
        coord = [ remap_ds.RasterYSize*geotransform[5]+geotransform[3] ,geotransform[0], geotransform[3],remap_ds.RasterXSize*geotransform[1]+geotransform[0] ]

        dst_ds.SetGeoTransform(geotransform)
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('WGS84')
        dst_ds.SetProjection(srs.ExportToWkt())
            
    range_start = (range_start-offset)*scale_factor
    range_end = (range_end-offset)*scale_factor
   
 
    remap_ds = None
    
    for i in range(numBands):
        dst_ds.GetRasterBand(numBands-i).WriteArray(band)

        remap_ds = gdal.Open(remappedFileList[i], GA_Update)
 
        band = remap_ds.GetRasterBand(1).ReadAsArray()
        band[band==(scale_factor*(-9999-offset))]=-9999

        dst_ds.GetRasterBand(numBands-i).WriteArray(band)

        dst_ds.GetRasterBand(numBands-i).SetNoDataValue(-9999)
        
        dst_ds.GetRasterBand(numBands-i).ComputeStatistics(False)

        band = None
        remap_ds = None
        #remove temporary files
        os.system('rm '+ prefix + str(i+1).zfill(2)+'.*')
        os.system('rm '+ prefix + str(i+1).zfill(2)+'_*')        
    
    dst_ds.SetMetadataItem('GLOBAL_MIN', str(range_start))
    dst_ds.SetMetadataItem('GLOBAL_MAX', str(range_end))
    
    
    dst_ds.SetMetadataItem('TIME_START', dateStart)
    dst_ds.SetMetadataItem('TIME_END', dateEnd)
    
    del dst_ds
    return outFileName


def createImgMOD04(fileAbsPath):
    outFileList = []

    satelliteType = os.path.basename(fileAbsPath)[0:5]

    src_ds = gdal.Open( fileAbsPath, GA_ReadOnly )
    driver = gdal.GetDriverByName( 'GTiff' )
    fname = basename(fileAbsPath)
    dateTime = fname.split('.')
    dateString = datetime.strptime((dateTime[1][1:]+dateTime[2]),"%Y%j%H%M").strftime("%Y%m%d.%H%M%S")
    #Create Lat and Lon Tiff
    subDsName = src_ds.GetSubDatasets()[71][0]
    subDs = gdal.Open( subDsName, GA_ReadOnly )
    
    sizeY = subDs.RasterYSize
    sizeX = subDs.RasterXSize    
    dataType = subDs.GetRasterBand(1).DataType
    numBands = 2
    
    outFileName_Coords = satelliteType + '_coords_' + dateString + '.tif'
    dst_ds = driver.Create(outFileName_Coords, sizeX, sizeY, numBands, dataType)    
    band = subDs.GetRasterBand(1).ReadAsArray()
    if not np.all(band!=-999.):
        logging.warning(fileAbsPath +"has a corrupted Lat Lon bands. Skipped")
        return outFileList
    dst_ds.GetRasterBand(1).WriteArray(band)
    subDsName = src_ds.GetSubDatasets()[70][0]
    subDs = gdal.Open( subDsName, GA_ReadOnly )
    band = subDs.GetRasterBand(1).ReadAsArray()
    if not np.all(band!=-999.):
        logging.warning(fileAbsPath +"has a corrupted Lat Lon bands. Skipped")
        return outFileList
    dst_ds.GetRasterBand(2).WriteArray(band)
    dst_ds = None
    band = None 
    
    dateStart, dateEnd = getDateTime(fileAbsPath)
    
    logging.debug('Starting extraction of products')

    #Image_Optical_Depth_Land_And_Ocean
    outFileList.append(extactProduct(src_ds, 83, satelliteType + '_Image_Optical_Depth_Land_And_Ocean_', sizeX, sizeY, [0], outFileName_Coords, dateString, dateStart, dateEnd))
    
    #Land_Ocean_Quality_Flag
    outFileList.append(extactProduct(src_ds, 9, satelliteType + '_Land_Ocean_Quality_Flag_', sizeX, sizeY, [0], outFileName_Coords, dateString, dateStart, dateEnd))

    os.system('rm '+ outFileName_Coords);
    src_ds = None
    return outFileList


def getDateTime(fileAbsPath): 
    src_ds = gdal.Open( fileAbsPath, GA_ReadOnly )
    startDate = src_ds.GetMetadata()['RANGEBEGINNINGDATE'] 
    endDate = src_ds.GetMetadata()['RANGEENDINGDATE']   
    startTime = src_ds.GetMetadata()['RANGEBEGINNINGTIME']
    endTime = src_ds.GetMetadata()['RANGEENDINGTIME']
    startDateTime = datetime.strptime((startDate+startTime), "%Y-%m-%d%H:%M:%S.000000").strftime("%Y-%m-%dT%H:%M:%SZ")    
    endDateTime = datetime.strptime((endDate+endTime), "%Y-%m-%d%H:%M:%S.000000").strftime("%Y-%m-%dT%H:%M:%SZ")
    return startDateTime, endDateTime


if __name__ == '__main__':
    #fileAbsPath = '/media/moris/STORAGE/repository/VMANIP/technical/test_data/Ozone/Total_column/L3/ESACCI-OZONE-L3S-TC-MERGED-DLR_1M-20080901-fv0100.nc'
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s MODIS_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
 
    createImgMOD04(fileAbsPath)
    
    exit(0)

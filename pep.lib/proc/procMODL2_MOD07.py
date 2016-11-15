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
    
    if index_band_hdf == 15:
        optionalBandMin =  np.ma.masked_array(optionalBand, optionalBand == -9999).min()
        optionalBandMax = np.ma.masked_array(optionalBand, optionalBand == -9999).max()
        range_start = (0.622 * (6.112*pow(math.e,((17.67*(range_start-273.15))/((range_start-273.15) + 243.5)))) )/( (optionalBandMin) - (0.378 * (6.112*pow(math.e,((17.67*(range_start-273.15))    /((range_start-273.15) + 243.5))))))
        range_end = (0.622 * (6.112*pow(math.e,((17.67*(range_end-273.15))/((range_end-273.15) + 243.5)))) )/( (optionalBandMax) - (0.378 * (6.112*pow(math.e,((17.67*(range_end-273.15))    /((range_end-273.15) + 243.5))))))
    
    remap_ds = None
    
    for i in range(numBands):
        remap_ds = gdal.Open(remappedFileList[i], GA_Update)
        band = remap_ds.GetRasterBand(1).ReadAsArray()

        dst_ds.GetRasterBand(numBands-i).SetNoDataValue(-9999)
        
        #Surface_Temperature
        if index_band_hdf == 7:
            band[band<0]=-9999
            dst_ds.GetRasterBand(numBands-i).WriteArray(band)
        #Surface_Pressure
        elif index_band_hdf == 8:
            band[band<0]=-9999
            dst_ds.GetRasterBand(numBands-i).WriteArray(band)
        #Retrieved_Temperature_Profile
        elif index_band_hdf == 14:
            band[band<0]=-9999
            dst_ds.GetRasterBand(numBands-i).WriteArray(band)
        #Retrieved_Moisture_Profile
        if index_band_hdf == 15:
            #optionalBand = temperature_profile
            #band = (0.622 * (6.112*pow(math.e,((17.67*(band-273.15))/((band-273.15) + 243.5)))) )/( (optionalBand) - (0.378 * (6.112*pow(math.e,((17.67*(band-273.15))    /((band-273.15) + 243.5))))))
            band = 100*(pow(math.e,(17.625*(band-273.15))/(243.04+(band-273.15)))/pow(math.e,(17.625*(optionalBand-273.15))/(243.04+(optionalBand-273.15))))            
            #TODO: using masked arrays is the more elegant way
            band[band<0]=-9999
            band[band>200]=-9999
            
            dst_ds.GetRasterBand(numBands-i).WriteArray(band)
        
        dst_ds.GetRasterBand(numBands-i).ComputeStatistics(False)

        band = None
        remap_ds = None
        #remove temporary files
        os.system('rm '+ prefix + str(i+1).zfill(2)+'.*')
        os.system('rm '+ prefix + str(i+1).zfill(2)+'_*')        
    
    dst_ds.SetMetadataItem('GLOBAL_MIN', str(range_start))
    dst_ds.SetMetadataItem('GLOBAL_MAX', str(range_end))
    
    heightLevels = getAltitude()
    levels = str(heightLevels).replace(' ', '')[1:-1]
    
    dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(heightLevels)))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(levels))
    
    dst_ds.SetMetadataItem('TIME_START', dateStart)
    dst_ds.SetMetadataItem('TIME_END', dateEnd)
    
    del dst_ds
    return outFileName


def createImgMODIS(fileAbsPath):
    #LIST OF MOD07 DATASET
    # index     dim             long name                           Type
    # 0         [406x270]       Scan_Start_Time mod07               (64-bit floating-point)
    # 1         [406x270]       Solar_Zenith mod07                  (16-bit integer)
    # 2         [406x270]       Solar_Azimuth mod07                 (16-bit integer)
    # 3         [406x270]       Sensor_Zenith mod07                 (16-bit integer)
    # 4         [406x270]       Sensor_Azimuth mod07                (16-bit integer)
    # 5         [12x406x270]    Brightness_Temperature mod07        (16-bit integer)
    # 6         [406x270]       Cloud_Mask mod07                    (8-bit integer)
    # 7         [406x270]       Surface_Temperature mod07           (16-bit integer)
    # 8         [406x270]       Surface_Pressure mod07              (16-bit integer)
    # 9         [406x270]       Surface_Elevation mod07             (16-bit integer)
    # 10        [406x270]       Processing_Flag mod07               (8-bit integer)
    # 11        [406x270]       Tropopause_Height mod07             (16-bit integer)
    # 12        [20x406x270]    Guess_Temperature_Profile mod07     (16-bit integer)
    # 13        [20x406x270]    Guess_Moisture_Profile mod07        (16-bit integer)
    # 14        [20x406x270]    Retrieved_Temperature_Profile mod07 (16-bit integer)
    # 15        [20x406x270]    Retrieved_Moisture_Profile mod07    (16-bit integer)
    # 16        [20x406x270]    Retrieved_Height_Profile mod07      (16-bit integer)
    # 17        [406x270]       Total_Ozone mod07                   (16-bit integer)
    # 18        [406x270]       Total_Totals mod07                  (16-bit integer)
    # 19        [406x270]       Lifted_Index mod07                  (16-bit integer)
    # 20        [406x270]       K_Index mod07                       (16-bit integer)
    # 21        [406x270]       Water_Vapor mod07                   (16-bit integer)
    # 22        [406x270]       Water_Vapor_Direct mod07            (16-bit integer)
    # 23        [406x270]       Water_Vapor_Low mod07               (16-bit integer)
    # 24        [406x270]       Water_Vapor_High mod07              (16-bit integer)
    # 25        [406x270x10]    Quality_Assurance mod07             (8-bit integer)
    # 26        [406x270x5]     Quality_Assurance_Infrared mod07    (8-bit integer)
    # 27        [406x270]       Latitude                            (32-bit floating-point)
    # 28        [406x270]       Longitude                           (32-bit floating-point)

    satelliteType = os.path.basename(fileAbsPath)[0:5]

    src_ds = gdal.Open( fileAbsPath, GA_ReadOnly )
    driver = gdal.GetDriverByName( 'GTiff' )
    fname = basename(fileAbsPath)
    dateTime = fname.split('.')
    dateString = dateTime[1]+dateTime[2]
    #Create Lat and Lon Tiff
    subDsName = src_ds.GetSubDatasets()[28][0]
    subDs = gdal.Open( subDsName, GA_ReadOnly )
    
    sizeY = subDs.RasterYSize
    sizeX = subDs.RasterXSize    
    dataType = subDs.GetRasterBand(1).DataType
    numBands = 2
    
    outFileName_Coords = satelliteType + '_coords_' + dateString + '.tif'
    dst_ds = driver.Create(outFileName_Coords, sizeX, sizeY, numBands, dataType)    
    band = subDs.GetRasterBand(1).ReadAsArray()
    dst_ds.GetRasterBand(1).WriteArray(band)
    subDsName = src_ds.GetSubDatasets()[29][0]
    subDs = gdal.Open( subDsName, GA_ReadOnly )
    band = subDs.GetRasterBand(1).ReadAsArray()
    dst_ds.GetRasterBand(2).WriteArray(band)
    dst_ds = None
    band = None 
    
    outFileList = {}
    
    dateStart, dateEnd = getDateTime(fileAbsPath)
    
    logging.debug('Starting extraction of products')

    #Surface_pressure 
    outFileList['SURFACEPRESSURE'] = extactProduct(src_ds, 8, satelliteType + '_Surface_Pressure_', sizeX, sizeY, [0], outFileName_Coords, dateString, dateStart, dateEnd)
    
    #Surface_temperature 
    outFileList['TEMPERATURESURFACE'] = extactProduct(src_ds, 7, satelliteType + '_Surface_temperature_', sizeX, sizeY, [0], outFileName_Coords, dateString, dateStart, dateEnd)
    
    #Retrieved_temperature_profiles 
    bandList = range(0,20)
    outFileList['TEMPERATUREPROFILE'] = extactProduct(src_ds, 14, satelliteType + '_Retrieved_temperature_profiles_', sizeX, sizeY, bandList, outFileName_Coords, dateString, dateStart, dateEnd)

    #Specific_humidity 
    bandList = range(0,20)
    temperature_ds = gdal.Open(satelliteType + '_Retrieved_temperature_profiles_' + dateString + ".tif", GA_ReadOnly )
    temperature_band = temperature_ds.GetRasterBand(1).ReadAsArray()
    outFileList['SPECIFICHUMIDITY'] = extactProduct(src_ds, 15, satelliteType + '_Specific_Humidity_', sizeX, sizeY, bandList, outFileName_Coords, dateString, dateStart, dateEnd, temperature_band)
    del temperature_ds 
    temperature_band = None

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


def getAltitude():
    #used fixed pressure level
    #5.0         44799.7528162307
    #10.0        38953.39355475301
    #20.0        33107.034293275334
    #30.0        29687.133359567062
    #50.0        25378.56773272306
    #70.0        22540.58810592659
    #100.0       19532.208471245376
    #150.0       16112.3075375371
    #200.0       13685.849209767697
    #250.0       11803.741910693101
    #300.0       10265.948276059422
    #400.0       7839.489948290016
    #500.0       5957.38264921542
    #620.0       4143.022810866474
    #700.0       3119.4030224189523
    #780.0       2206.6740803953467
    #850.0       1481.7914948332623
    #920.0       814.306695135645
    #950.0       543.6573724162985
    #1000.0      111.0233877377401
    #p0 = p[14]
    #t0 = 288.15
    #g = 9.80665
    #r = 287.053
    #for i in range(len(height)):
    #    height[i] = -((r*t0)/(g))* math.log(p[i+1]/p0)
    height = [ 111.0233877377401,543.6573724162985,814.306695135645,1481.7914948332623,2206.6740803953467,3119.4030224189523,4143.022810866474,5957.38264921542,7839.489948290016,10265.948276059422,11803.741910693101,13685.849209767697,16112.3075375371,19532.208471245376,22540.58810592659,25378.56773272306,29687.133359567062,33107.034293275334,38953.39355475301,44799.7528162307]
#    height = [ 111.0233877377401,543.6573724162985,1481.7914948332623,3119.4030224189523,5957.38264921542,7839.489948290016,10265.948276059422,13685.849209767697,16112.3075375371,19532.208471245376]
    return height


if __name__ == '__main__':
    #fileAbsPath = '/media/moris/STORAGE/repository/VMANIP/technical/test_data/Ozone/Total_column/L3/ESACCI-OZONE-L3S-TC-MERGED-DLR_1M-20080901-fv0100.nc'
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s MODIS_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
 
    createImgMODIS(fileAbsPath)
    
    exit(0)

#!/usr/bin/env python

import os,sys, subprocess, math, datetime
from os.path import basename
import numpy as np
import numpy.ma as ma
import gdal
from gdalconst import *
from osgeo import ogr, osr

from pyhdf.HDF import *
from pyhdf.V   import *
from pyhdf.VS  import *
from pyhdf.SD  import *

def getCoordsULLR(fileAbsPath, start, stop):
    # coordinates every 10 pixels
    nodes = range(start, stop, 10)
    hdf = HDF(fileAbsPath)
    vs = hdf.vstart()

    ref = vs.find('Latitude')
    vd = vs.attach(ref)
    nrecs, intmode, fields, size, name = vd.inquire()
    latitude = np.array(vd.read(nrecs))

    ref = vs.find('Longitude')
    vd = vs.attach(ref)
    nrecs, intmode, fields, size, name = vd.inquire()
    longitude = np.array(vd.read(nrecs))

    lat=[]
    lon=[]
    for n in nodes:
        lat.append(latitude[n][0])
        lon.append(longitude[n][0])

    # Append the last pixel coordinates: it is 9 pixel distant from the
    # previous one, and not 10 px like the others!!!
    lat.append(latitude[stop-1][0])
    lon.append(longitude[stop-1][0])

    vs.end()

    coords=[]
    for x, y in zip(lat, lon):
        coords.append(x)
        coords.append(y)

    # Nodes are 101: 100 points with distance 10 px
    # and the last one with distance 9 px from the 990th
    return coords, len(nodes)+1

def getStartEndTime(fileAbsPath):
    hdf = HDF(fileAbsPath)
    vs = hdf.vstart()

    ref = vs.find('start_time')
    vd = vs.attach(ref)
    startTime = vd.read(1)[0][0]
    startDateTime = datetime.datetime(int(startTime[0:4]), int(startTime[4:6]), int(startTime[6:8]), int(startTime[8:10]), int(startTime[10:12]), int(startTime[12:14]))
    # startDateTime = startTime[0:4] + '-' + startTime[4:6] + '-' + startTime[6:8] + 'T' + startTime[8:10] + ':' + startTime[10:12] + ':' + startTime[12:14] + 'Z'

    ref = vs.find('end_time')
    vd = vs.attach(ref)
    endTime = vd.read(1)[0][0]
    endDateTime = datetime.datetime(int(endTime[0:4]), int(endTime[4:6]), int(endTime[6:8]), int(endTime[8:10]), int(endTime[10:12]), int(endTime[12:14]))
    # endDateTime = endTime[0:4] + '-' + endTime[4:6] + '-' + endTime[6:8] + 'T' + endTime[8:10] + ':' + endTime[10:12] + ':' + endTime[12:14] + 'Z'

    vs.end()

    return startDateTime, endDateTime

def getAdjustmentParams(fileAbsPath):
    hdf = HDF(fileAbsPath)
    vs = hdf.vstart()
    ref = vs.find('Radar_Reflectivity.valid_range')
    vd = vs.attach(ref)
    validRange = vd.read(1)[0][0]
    ref = vs.find('Radar_Reflectivity.factor')
    vd = vs.attach(ref)
    reflectivityFactor = vd.read(1)[0][0]
    vs.end()
    return validRange, reflectivityFactor

def extractProduct(fileAbsPath, parameter):
    # Get parameters in order to tune output image
    validRange, reflectivityFactor = getAdjustmentParams(fileAbsPath)

    # The original Reflectivity subdataset must be transposed: gdal_translate doesn't do that
    # gdal_translate -of GTiff -co COMPRESS=LZW 'HDF4_SDS:UNKNOWN:"/home/candini/Desktop/VMANIP/input/cloudsat/2013137113720_37520_CS_2B-GEOPROF_GRANULE_P_R04_E06.hdf":3' Reflectivity.tif
    src_ds = gdal.Open( fileAbsPath, GA_ReadOnly )
    subDsName = src_ds.GetSubDatasets()[6][0]
    subDs = gdal.Open( subDsName, GA_ReadOnly )
    band = subDs.GetRasterBand(1).ReadAsArray()
    transposedBand = np.transpose(band)
    dataType = subDs.GetRasterBand(1).DataType

    # Mask values out of validRange
    maskedBand = ma.masked_outside(transposedBand, validRange[0], validRange[1])
    # Divide every value for reflectivityFactor
    dividedMask = np.divide(maskedBand, reflectivityFactor)
    # Fill nodata values
    nodata = -9999
    img = dividedMask.filled(nodata)

    # Invert dimensions because a transposition is needed!
    sizeX = subDs.RasterYSize
    sizeY = subDs.RasterXSize
    numBands = subDs.RasterCount

    fname=basename(fileAbsPath)
    dateTime = fname.split('_')
    dateString = '_' + dateTime[0]
    outFileName = 'Cloudsat_' + parameter + dateString + '_tmp.tif'

    driver = gdal.GetDriverByName( 'GTiff' )
    dst_ds = driver.Create(outFileName, sizeX, sizeY, numBands, dataType)
    dst_ds.GetRasterBand(1).SetNoDataValue(nodata)
    dst_ds.GetRasterBand(1).WriteArray(img)

    dst_ds = None
    subDs = None
    src_ds = None

    return outFileName


def createMeansCloudsat(fileAbsPath, prevName, parameter):
    src_ds = gdal.Open( fileAbsPath, GA_ReadOnly )
    # Height subdataset
    subDsName = src_ds.GetSubDatasets()[3][0]
    subDs = gdal.Open( subDsName, GA_ReadOnly )
    band = subDs.GetRasterBand(1).ReadAsArray()
    transposedBand = np.transpose(band)[0:104,...]
    subDs = None
    src_ds = None

    size = 1000
    totImgNum =  int(math.ceil(transposedBand.shape[1]/float(size)))
    
    outFileList = []
    
    # Create chunks of the original image
    for idx, start in enumerate(range(0, transposedBand.shape[1], size)):
        if start == 0: # First chunk
            realStart = start
            stop = size
            sizeX = size
        elif (start-idx+size) >= transposedBand.shape[1]: # Last chunk
            realStart = start-idx # The first pixel of the new image must be the same of the previous one
            stop = transposedBand.shape[1]
            sizeX = stop - realStart
        else: # In the middle of whole image
            realStart = start-idx
            stop = (realStart)+size
            sizeX = size

        chunk = transposedBand[...,realStart:stop]

        means=[]
        for i, row in enumerate(chunk[...]):
            m = row.mean()
            if m >= 0:
                means.append(m)

        param = 'Reflectivity'
        brTyp = 'curtain'
        chunkNum = start/size
        chunkNumStr = '_' + str(chunkNum).zfill(4)
        outPathFname = prevName.replace('_tmp', chunkNumStr)
        
        dst_ds = gdal.Open(outPathFname, GA_Update)
        outFileList.append(outPathFname)
        
        coords, numNodes = getCoordsULLR(fileAbsPath, realStart, stop)
        coords = np.reshape(coords, (-1,2))
        lower_left = (coords[:,1][0], coords[:,0][0])
        upper_right = (coords[:,1][len(coords)-1], coords[:,0][len(coords)-1])
        
        pixelWidth = abs(coords[:,1][0] - coords[:,1][len(coords)-1])/sizeX
        pixelHeight = abs(coords[:,0][0] - coords[:,0][len(coords)-1])/sizeX
        
        dst_ds.SetGeoTransform([lower_left[0], pixelWidth, 0, upper_right[1], 0, -pixelHeight])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('WGS84')
        dst_ds.SetProjection(srs.ExportToWkt())
        
        colRowList = ''
        endRange = int(math.ceil((float(stop)-float(realStart))/10))
        for i in range(0, endRange):
            colRowList += str(i*10) + ' 0, '            
        colRowList += '999 0'
        
        outCoords = ''
        for i in range(0, len(coords)):
            outCoords += (str(coords[i][1]) + ' ' + str(coords[i][0]) + ', ')

        outCoords = outCoords[:-2]
        
        startDateTime, endDateTime = getStartEndTime(fileAbsPath)
        
        means.reverse()
        
        dst_ds.GetRasterBand(1).ComputeStatistics(False)
        
        dst_ds.SetMetadataItem('COORDINATES', outCoords)
        dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(means).replace(' ', '')[1:-1])
        dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(means)))        
        dst_ds.SetMetadataItem('NODES_POSITION', str(colRowList))
        dst_ds.SetMetadataItem('NODES_NUMBER', str(numNodes))
        dst_ds.SetMetadataItem('TIME_START', startDateTime.strftime("%Y-%m-%dT%H:%M:%SZ"))
        dst_ds.SetMetadataItem('TIME_END', endDateTime.strftime("%Y-%m-%dT%H:%M:%SZ"))
        dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.amax(band)))
        dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.amin(band)))
    
        dst_ds = None

    return outFileList


def cutImgCloudsat(prevName, numRows):
    inPathFname = prevName
    src_ds = gdal.Open( inPathFname, GA_ReadOnly )
    driver = gdal.GetDriverByName( 'GTiff' )
    band = src_ds.GetRasterBand(1).ReadAsArray()[0:numRows-1,...]

    size = 1000
    nodata = -9999

    # Create chunks of the original image
    for idx, start in enumerate(range(0, band.shape[1], size)):
        if start == 0: # First chunk
            realStart = start
            stop = size
            sizeX = size
        elif (start-idx+size) >= band.shape[1]: # Last chunk
            realStart = start-idx # The first pixel of the new image must be the same of the previous one
            stop = band.shape[1]
            sizeX = stop - realStart
        else: # In the middle of whole image
            realStart = start-idx
            stop = realStart+size
            sizeX = size

        chunk = band[...,realStart:stop]

        outPathFname = prevName.replace('_tmp', '_' + str(start/size).zfill(4))
        dst_ds = driver.Create(outPathFname, sizeX, numRows, src_ds.RasterCount, gdal.GDT_Float32)
        dst_ds.GetRasterBand(1).SetNoDataValue(nodata)
        dst_ds.GetRasterBand(1).WriteArray(chunk)
        dst_ds = None

    src_ds = None
    os.remove(prevName)

def createImgCloudsat(fileAbsPath):
    parameter = 'Reflectivity'

    tmpOutFile = extractProduct(fileAbsPath, parameter)
    cutImgCloudsat(tmpOutFile, 104)
    outFileList = createMeansCloudsat(fileAbsPath, tmpOutFile, parameter)
    
    return outFileList
    
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s Cloudsat_file \n' % sys.argv[0] )
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: File %s was not found!\n' % sys.argv[1])    
        
    fileAbsPath = sys.argv[1]
    createImgCloudsat(fileAbsPath)

    exit(0)
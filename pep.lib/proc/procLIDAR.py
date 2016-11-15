#!/usr/bin/env python

import sys
import os
import gdal
import numpy as np
from xml.etree import ElementTree as et
from osgeo import osr
from netCDF4 import Dataset

np.set_printoptions(threshold=np.nan)

def extractProduct(fileAbsPath, fileType):    
    with Dataset(fileAbsPath, 'r') as ncfile:
        ncfile = Dataset(fileAbsPath, 'r')
        data2d = np.array([[ncfile.variables[fileType][:]]])
        alti = ncfile.variables['Altitude'][:]
        date = str(ncfile.StartDate)
        startTime = str(ncfile.StartTime_UT).zfill(6)
        endTime = str(ncfile.StopTime_UT).zfill(6)
        station = str(ncfile.Location)
        lat = ncfile.Latitude_degrees_north
        lon = ncfile.Longitude_degrees_east
        elevation = str(ncfile.Altitude_meter_asl)
        wavelenth = str(ncfile.EmissionWavelength_nm)
    
    driver = gdal.GetDriverByName('GTiff')
    dataType = gdal.GDT_Float32
    startDateTime = date[0:4]+'-'+date[4:6]+'-'+date[6:8]+'T'+startTime[0:2]+':'+startTime[2:4]+':'+startTime[4:6]+'Z'
    endDateTime = date[0:4]+'-'+date[4:6]+'-'+date[6:8]+'T'+endTime[0:2]+':'+endTime[2:4]+':'+endTime[4:6]+'Z'
    outputFilename = 'LIDAR_' + station.replace(", ", "_") + "_" + wavelenth + 'nm_' + date + '.' + startTime + '_' + fileType +'.tif'
    dst_ds = driver.Create(outputFilename, 1, 1, len(alti), dataType)        

    for i in range(len(alti)):
        dst_ds.GetRasterBand(i+1).WriteArray(data2d[:,:,i])

    dst_ds.SetMetadataItem('TIME_START', startDateTime)
    dst_ds.SetMetadataItem('TIME_END', endDateTime)
    dst_ds.SetMetadataItem('GLOBAL_MAX', str(max(np.squeeze(data2d))))
    dst_ds.SetMetadataItem('GLOBAL_MIN', str(min(np.squeeze(data2d))))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(alti)))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(alti.tolist())[1:-1].replace(' ',''))

    pixelWidth = 0.4
    pixelHeight = 0.4

    #LDIAR has only one lat/lon, so we can use those values for the transformation  
    dst_ds.SetGeoTransform([lon, pixelWidth, 0, lat, 0, -pixelHeight])
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())

    dst_ds = None
    
    attributeValues = {}
    attributeValues['station'] = station
    attributeValues['lat'] = str(lat)
    attributeValues['lon'] = str(lon)
    attributeValues['elevation'] = elevation
    attributeValues['timeStart'] = startDateTime
    attributeValues['timeEnd'] = endDateTime
    attributeValues['sumData'] = str(sum(np.squeeze(data2d)))
    attributeValues['dateTime'] = date + '.' + startTime
    
    return [outputFilename, attributeValues]


def createXML(values):
    outFileXML = 'LIDAR_' + values['station'].replace(", ", "_") + "_" + values['dateTime'] + '_Extinction' + '.xml'
    root = et.Element("LIDAR")
    name = et.SubElement(root, "siteName")
    name.text = values['station']
    longi = et.SubElement(root, "siteLongitude")
    longi.text = values['lon']
    lati = et.SubElement(root, "siteLatitude")
    lati.text = values['lat']
    height = et.SubElement(root, "siteElevation")
    height.text = values['elevation']
    
    data = et.SubElement(root, "data")
    startT = et.SubElement(data, "timeStart")
    startT.text = values['timeStart']
    endT = et.SubElement(data, "timeEnd")
    endT.text = values['timeEnd']
    field = et.SubElement(data, "field")
    field.text = "AOD"
    value = et.SubElement(data, "value")
    value.text = values['sumData']

    tree = et.ElementTree(root)
    tree.write(outFileXML)
        
    return outFileXML


def createImgLIDAR_Backscatter(fileAbsPath):
    outputFilename = extractProduct(fileAbsPath, 'Backscatter')[0]
    
    return [outputFilename]



def createImgLIDAR_Extinction(fileAbsPath):        
    [outputFileTIF, attributes] = extractProduct(fileAbsPath, 'Extinction')
    outputFileXML = createXML(attributes)
    
    return [outputFileTIF, outputFileXML]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('\nUsage: %s LIDAR_input_file(s) \n' % sys.argv[0])
        
    files = sys.argv[1:]
    for file in files:
        if not os.path.exists(file):
            print '\nERROR: File %s was not found!\n' % file
            
        try:
	    fileType = os.path.basename(file)[13]
            if fileType == 'b':
                createImgLIDAR_Backscatter(os.path.abspath(file))
            elif fileType == 'e':
                createImgLIDAR_Extinction(os.path.abspath(file))
        except IndexError:
            print 'Could not open: ' + file

    exit(0)

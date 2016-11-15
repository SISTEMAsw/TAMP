#!/usr/bin/env python

import os, sys, subprocess
import gdal
import multiprocessing
import numpy as np
import time as tt
from netCDF4 import Dataset
from osgeo import osr
from os.path import dirname, basename

def createImgWRFCHEM_2D(fileAbsPath, pixelSize=0.015):
    ncfile = Dataset(fileAbsPath, 'r')    
    data = ncfile.variables['so2'][:]    
    time = ncfile.variables['Times'][:]
    lon = ncfile.variables['XLONG'][:]
    lat = ncfile.variables['XLAT'][:]
    ph = ncfile.variables['PH'][:]
    phb = ncfile.variables['PHB'][:]
    hgt = ncfile.variables['HGT'][:]   
    ncfile.close()
    
    xSize = data.shape[3]
    ySize = data.shape[2]
    numBands = data.shape[1]
    
    driver = gdal.GetDriverByName('GTiff')
    no_data = -9999
    
    dateStr = basename(fileAbsPath)[11:21]
    coordsFilename = 'WRF-CHEM_coords_' + dateStr + '.tif'
    coord_ds = driver.Create(coordsFilename, xSize, ySize, 2, gdal.GDT_Float32)
    coord_ds.GetRasterBand(1).WriteArray(lat[0])
    coord_ds.GetRasterBand(2).WriteArray(lon[0])
    coord_ds = None
        
    prefix = 'WRFCHEM_SO2' + basename(fileAbsPath)[6:11].upper()
    outFileList = []
    
    upper_left = []
    lower_right = []
    upper_left.append(np.amax(lat[0][:][:]))
    upper_left.append(np.amin(lon[0][:][:]))
    lower_right.append(np.amin(lat[0][:][:]))        
    lower_right.append(np.amax(lon[0][:][:]))
    
    tmpOutFile = prefix + dateStr + '_tmp.tif'    
    dst_ds = driver.Create(tmpOutFile, xSize, ySize, 1, gdal.GDT_Float32)
    dst_ds.GetRasterBand(1).WriteArray(np.squeeze(data[0][0][:][:]))
    dst_ds = None    
    
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    command_call = [workingDir + 'bin/remap', '-i', tmpOutFile, '-l', str(upper_left[0]), str(upper_left[1]), '-e', str(lower_right[0]), str(lower_right[1]), '-a', coordsFilename, '-s', str(pixelSize), '-n', str(no_data), '-q', '-o', tmpOutFile + '_mask']
    mask_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))
    command_call.pop()
    command_call.append(tmpOutFile + '_remapped')
    command_call.append('-c')
    coord_process = subprocess.Popen(command_call, stdout=open(os.devnull, 'wb'))        
    coord_process.wait()
    mask_process.wait()

    remap_ds = gdal.Open(tmpOutFile + '_remapped', gdal.GA_ReadOnly)
    transform_i = remap_ds.GetRasterBand(1).ReadAsArray().transpose()
    transform_j = remap_ds.GetRasterBand(2).ReadAsArray().transpose()
    mask_ds = gdal.Open(tmpOutFile + '_mask', gdal.GA_ReadOnly)
    mask = mask_ds.GetRasterBand(1).ReadAsArray().transpose()
        
    for t in range(0, len(time)):        
        dateStr = ''
        for i in range(0, len(time[t]) - 3):
            if time[t][i] == ':' or time[t][i] == '-' or time[t][i] == '_':
                continue
            dateStr += time[t][i]
        dateStr += '00'
        dateStr = dateStr[:8] + '.' + dateStr[8:]
        
        outFilename = prefix + dateStr + '.tif'
        dst_ds = driver.Create(outFilename, transform_j.shape[0], transform_j.shape[1], 1, gdal.GDT_Float32)
        
        heightLevels = [0]
        height = np.zeros((numBands, ySize, xSize))
        for i in range(numBands):
            height[i][:][:] = ((ph[t][i][:][:] + phb[t][i][:][:]) / 9.81) - hgt[t][:][:] 
            avg = np.average(height[i][:][:])
            if avg < 0:
                avg = 0
            heightLevels.append(avg)
        
        band = np.squeeze(data[t][0][:][:])
        data_out = np.ma.masked_equal(band,no_data)   
        data_out = data_out[:, :]*heightLevels[1]
        for i in range(numBands-1):
            band = np.squeeze(data[t][i+1][:][:])            
            data_tmp = np.ma.masked_equal(band,no_data)     
            #print band[10,10], heightLevels[i+2]-heightLevels[i+1], heightLevels[i+2],heightLevels[i+1]
            data_out += data_tmp[:, :]*(heightLevels[i+2]-heightLevels[i+1])
        data_out = np.ma.masked_equal(data_out ,no_data)

        data_out_remapped = np.ones([transform_j.shape[0], transform_j.shape[1]]) * no_data
        for i in range(data_out_remapped.shape[0]):
            for j in range(data_out_remapped.shape[1]):
                data_out_remapped[i, j] = data_out[transform_j[i,j], transform_i[i,j]]

        data_out_remapped[mask==no_data] = no_data

        dst_ds.GetRasterBand(1).SetNoDataValue(no_data)
        dst_ds.GetRasterBand(1).WriteArray(data_out_remapped.transpose())
        dst_ds.GetRasterBand(1).ComputeStatistics(False)
        #dst_ds.SetGeoTransform(geotransform)
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('WGS84')
        dst_ds.SetProjection(srs.ExportToWkt())

        dst_ds.SetGeoTransform([upper_left[1], pixelSize, 0, upper_left[0], 0, -pixelSize])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('WGS84')
        dst_ds.SetProjection(srs.ExportToWkt())
        
        dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.max(data)))
        dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.min(data)))
        
        date = dateStr[0:4] + '-' + dateStr[4:6] + '-' + dateStr[6:8]
        hours = dateStr[9:11]
        minutes = dateStr[11:13]
        seconds = '00'
        formatedDate = date + 'T' + hours + ':' + minutes + ':' + seconds + 'Z'            
        dst_ds.SetMetadataItem('TIME_END', formatedDate)
        dst_ds.SetMetadataItem('TIME_START', formatedDate)
            
        dst_ds = None            
        outFileList.append(outFilename)
        
    os.remove(coordsFilename)
    os.remove(tmpOutFile)
    os.remove(tmpOutFile + '_remapped')
    os.remove(tmpOutFile + '_mask')
    
    return outFileList


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('\nUsage: %s WRF-CHEM_file(s) \n' % sys.argv[0])

    files = sys.argv[1:]
    for f in files:
        if not os.path.exists(f):
            print '\nERROR: File %s was not found!\n' % f
            continue
    
        # use pixel size 0.1 for the large input files
        if basename(f)[7:10] == 'd01':
            createImgWRFCHEM_2D(f,0.1)
        else:
            createImgWRFCHEM_2D(f)
    
    exit(0)

#!/usr/bin/env python

import os, sys, subprocess
import gdal
import multiprocessing
import numpy as np
import time as tt
from netCDF4 import Dataset
from osgeo import osr
from os.path import basename

def extract_product(fileAbsPath, field, pixelSize=0.10):
    ncfile = Dataset(fileAbsPath, 'r')    
    data = ncfile.variables[field][:]    
    time = ncfile.variables['Times'][:]
    lon = ncfile.variables['XLONG'][:]
    lat = ncfile.variables['XLAT'][:]    
    if field != 'vashcol_sat_col':
        ph = ncfile.variables['PH'][:]
        phb = ncfile.variables['PHB'][:]
        hgt = ncfile.variables['HGT'][:]
        is_volume = True
    else:
        data = np.expand_dims(data, axis=1)
        is_volume = False            
    ncfile.close()
    
    xSize = data.shape[3]
    ySize = data.shape[2]
    numBands = data.shape[1]
    
    driver = gdal.GetDriverByName('GTiff')
    no_data = -9999
    
    if field == 'vashcol_sat_col' or field == 'vash_al':
        field = 'EYJA_' + field
    field = field.upper()
    dateStr = basename(fileAbsPath)[11:21]
    coordsFilename = 'WRF-CHEM_coords_' + field + dateStr + '.tif'
    coord_ds = driver.Create(coordsFilename, xSize, ySize, 2, gdal.GDT_Float32)
    coord_ds.GetRasterBand(1).WriteArray(lat[0])
    coord_ds.GetRasterBand(2).WriteArray(lon[0])
    coord_ds = None
        
    prefix = 'WRFCHEM_' + field + basename(fileAbsPath)[6:11].upper()
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
        dst_ds = driver.Create(outFilename, transform_j.shape[0], transform_j.shape[1], numBands, gdal.GDT_Float32)
        
        height = np.zeros([numBands, ySize, xSize])
        heightLevels = []
        
        for l in range(numBands):
            outData = np.ones([transform_j.shape[0], transform_j.shape[1]]) * no_data
            
            if is_volume:
                height[l][:][:] = ((ph[t][l][:][:] + phb[t][l][:][:]) / 9.81) - hgt[t][:][:]
                avg = np.average(height[l][:][:])
                if avg < 0:
                    avg = 0
                heightLevels.append(avg)
            
            for i in range(outData.shape[0]):
                for j in range(outData.shape[1]):
                    outData[i, j] = data[t, l, transform_j[i,j], transform_i[i,j]]

            outData[mask==no_data] = no_data
                    
            dst_ds.GetRasterBand(numBands - l).SetNoDataValue(no_data)
            dst_ds.GetRasterBand(numBands - l).WriteArray(outData.transpose())
            dst_ds.GetRasterBand(numBands - l).ComputeStatistics(False)

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
            
        if is_volume:
            dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(heightLevels)))
            dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(heightLevels).replace(' ', '')[1:-1])
            
        dst_ds = None
            
        outFileList.append(outFilename)
        
    os.remove(coordsFilename)
    os.remove(tmpOutFile)
    os.remove(tmpOutFile + '_remapped')
    os.remove(tmpOutFile + '_mask')
    
    return outFileList

def createImgWRFCHEM_SO2(fileAbsPath):
    return extract_product(fileAbsPath, 'so2')

def createImgWRFCHEM_ASH3D(fileAbsPath):
    return extract_product(fileAbsPath, 'vash_al')

def createImgWRFCHEM_ASHCOL(fileAbsPath):
    return extract_product(fileAbsPath, 'vashcol_sat_col')


if __name__ == '__main__':    
    if len(sys.argv) < 2:
        sys.exit('\nUsage: %s WRF-CHEM_file(s) \n' % sys.argv[0])
        
    files = sys.argv[1:]    
    fields = ['vash_al', 'vashcol_sat_col', 'so2']
    
    #number of concurrent processes, it's 3 in order to avoid running out of memory
    active_processes = 3
    active_jobs = []
    joblist = []
    
    for file in files:
        if not os.path.exists(file):
            print '\nERROR: File %s was not found!\n' % file
            continue
        
        if file[-6:] == 'vash3d':
            field = 'vash_al'
        elif file[-7:] == 'vashcol':
            field = 'vashcol_sat_col'
        else:
            field = 'so2'
        
        p = multiprocessing.Process(target=extract_product, args=(file, field))
        joblist.append((p, file, tt.time()))
    
    while joblist or active_jobs:
        for job in joblist:
            if len(active_jobs) < active_processes:                
                job[0].start()
                joblist.remove(job)
                active_jobs.append(job)
                continue                
            
        for job in active_jobs:
            if not job[0].is_alive():
                print 'Finished processing for {0}, took: {1:5.1f}s'.format(job[1], tt.time()-job[2])
                active_jobs.remove(job)
                continue
        tt.sleep(0.5)
    exit(0)
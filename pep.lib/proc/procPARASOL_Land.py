#!/usr/bin/env python

import os, sys
import struct
import subprocess
import gdal
import numpy as np
import logging 

def str2UTC(string):
    return string[:4] + '-' + string[4:6] + '-' + string[6:8] + 'T' + string[8:10] + ':' + string[10:12] + ':' + string[12:14] + 'Z'


def read_records_ls(datafile):
    fin = open(datafile, 'rb')    
    fin.seek(36)
    filename = fin.read(16)    
    fin.seek(52)
    recordsNumber = struct.unpack('>I', fin.read(4))[0]
    recordsLength = struct.unpack('>I', fin.read(4))[0]
    
    lines = []
    cols = []
    aot_865 = []    
    pos = 180
    oldRec = 1
    
    for i in range(2, recordsNumber+2):
        fin.seek(pos)                
        rec = struct.unpack('>I', fin.read(4))[0]
        
        if rec != oldRec + 1:
            rec = oldRec + 1
            fin.seek(pos)
            fin.read(3)
            pos -= 1
        
        size = struct.unpack('>H', fin.read(2))[0]        
        line = struct.unpack('>H', fin.read(2))[0]
        lines.append(line)
        col = struct.unpack('>H', fin.read(2))[0]
        cols.append(col)        
        pos += (2+1+4)
        aot = struct.unpack('>H', fin.read(2))[0]
        aot_865.append(aot)        
        pos -= 7
        pos += recordsLength                                
        oldRec = rec                
    return lines, cols, aot_865


def createImgPARASOL_Land(fileAbsPath, pixelSize = 0.15):
    leaderFile = fileAbsPath[0:-1] + 'L'
    leadFin = open(leaderFile)
    leadFin.seek(640)
    timeStart = leadFin.read(16)
    timeEnd = leadFin.read(16)
    
    workingDir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    #filename = 'PARASOL_' + os.path.basename(fileAbsPath)[2:4] + '_AOT_LAND_' + timeStart[0:8] + '.' + timeStart[8:-2] + '.tif'
    #filenameOutput = filename[:-4] + '_REMAPPED.tif'
    filename = 'PARASOL_' + os.path.basename(fileAbsPath)[2:4] + '_AOT_LAND_' + timeStart[0:8] + '.' + timeStart[8:-2] + '_tmp.tif'
    filenameOutput = filename[:-8] + '.tif'


    
    lines, cols, aot_865 = read_records_ls(fileAbsPath)
    lines = np.array(lines)
    lat = 90-((lines)-0.5)/6    
    cols = np.array(cols)
    N = np.rint(1080*np.cos(np.radians(lat)))
    lon = (180/N) * (cols-1080.5)
    
    rangeX = np.amax(lines) - np.amin(lines) + 1
    rangeY = np.amax(cols) - np.amin(cols) + 1
    offsetX = np.amin(lines)
    offsetY = np.amin(cols)
    
    if len(lines) < 5 or len(cols) < 5:
        raise Exception('Input file too small for remapping')
                
    data = np.zeros((rangeX,rangeY))
    data.fill(-9999)
    
    latOut = np.zeros((rangeX,rangeY))
    latOut.fill(-9999)
    
    lonOut = np.zeros((rangeX,rangeY))
    lonOut.fill(-9999)
    
    #remp the data and latitude/longitude to 2d
    for i in range(0, len(cols)):
        data[lines[i]-offsetX][cols[i]-offsetY] = aot_865[i] * (2*(10**-3)) #multiplying slope                
        latOut[lines[i]-offsetX][cols[i]-offsetY] = lat[i]
        lonOut[lines[i]-offsetX][cols[i]-offsetY] = lon[i]
                    
    lat_min = np.amin(lat)
    lat_max = np.amax(lat)
    lon_min = np.amin(lon)
    lon_max = np.amax(lon)

    #check if we cross the border
    if lon_max * lon_min < 0 and lon_max-lon_min > 270:
        lon_min = np.amin(lon[lon>0])
        lon_max = np.amax(lon[lon<0])
    
    for x in range(0, latOut.shape[0]):
        for y in range(0, latOut.shape[1]):
            if latOut[x][y] == -9999:
                latOut[x][y] = 90-((x+offsetX)-0.5)/6
                
                N = np.rint(1080*np.cos(np.radians(latOut[x][y])))
                lonOut[x][y] = (180/N) * (y+offsetY-1080.5)

                if abs(lonOut[x][y]) > 180:
                    lonOut[x][y] = -9999
                    latOut[x][y] = -9999
    
    filenameCoords = 'Coords_' + os.path.basename(fileAbsPath) + '.tif'
    
    driver = gdal.GetDriverByName('GTiff')    
    #print type(rangeX), type(rangeX)
    coord_ds = driver.Create(filenameCoords,int(rangeY), int(rangeX), 2, gdal.GDT_Float32)
    coord_ds.GetRasterBand(1).WriteArray(latOut)
    coord_ds.GetRasterBand(2).WriteArray(lonOut)
    coord_ds = None
    
    remap_ds = driver.Create(filename, int(rangeY), int(rangeX), 1, gdal.GDT_Float32)
    remap_ds.GetRasterBand(1).WriteArray(data)
    remap_ds = None

    subprocess.call([workingDir + '/bin/remap', '-i', filename, '-o', filenameOutput, '-a', filenameCoords, '-l', str(lat_max), str(lon_min), '-e', str(lat_min)+','+str(lon_max),'-s', str(pixelSize),'-n','-9999']  , stdout=open(os.devnull, 'wb'))
    os.remove(filenameCoords)
    os.remove(filename)
    
    dst_ds = gdal.Open(filenameOutput, gdal.GA_Update)
    dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
    dst_ds.GetRasterBand(1).ComputeStatistics(False)
        
    dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.max(data[data!=-9999])))
    dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.min(data[data!=-9999])))
    dst_ds.SetMetadataItem('TIME_END', str2UTC(timeEnd))
    dst_ds.SetMetadataItem('TIME_START', str2UTC(timeStart))
    
    return [filenameOutput]


if __name__ == '__main__':    
    if len(sys.argv) < 2:
        sys.exit('\nUsage: %s PARASOL_file(s) \n' % sys.argv[0] )
    
    files = sys.argv[1:]
    for file in files:
        if not os.path.exists(file):
            print '\nERROR: File %s was not found!\n' % file
            
        createImgPARASOL_Land(os.path.abspath(file))

    exit(0)

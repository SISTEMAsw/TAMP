#!/usr/bin/env python

import os, sys
import gdal
import datetime
import math
import numpy as np
from netCDF4 import Dataset
from osgeo import osr
from os.path import dirname, basename
import logging 

def createImgBASCOE(fileAbsPath):
    ncfile = Dataset(fileAbsPath, 'r')
    data = ncfile.variables['o3_vmr'][:]
    ap = ncfile.variables['ap'][:]
    bp = ncfile.variables['bp'][:]
    p0 = ncfile.variables['p0'][:]
    levels = ncfile.variables['levelist'][:]
    time = ncfile.variables['time'][:]
    lat = ncfile.variables['latitude'][:]
    lon = ncfile.variables['longitude'][:]
    temp = ncfile.variables['temperature'][:]
    z = ncfile.variables['z'][:]
    ncfile.close()
    
    boltzman = 1.38064852*(10**-23)
    avogadro = 6.022140857*(10**23)
    air_molmass = 28.9644
    Rgas = boltzman * avogadro
    Rair = 1000 * Rgas / air_molmass
    g0 = 9.80665
        
    xSize = data.shape[2]
    ySize = data.shape[1]
    num_bands = data.shape[0]
    
    gh = np.zeros((num_bands, ySize, xSize))  
    
    driver = gdal.GetDriverByName('GTiff')
    
    reference_date = datetime.datetime(2000,1,1)
    days = int(time[0])
    hours = (time[0] - int(days)) * 60
    minutes = (hours - int(hours)) * 60
    seconds = (minutes - int(minutes)) * 60
    time_offset = datetime.timedelta(days=days, hours=int(hours), minutes=int(minutes), seconds=int(seconds))
    start_time = reference_date + time_offset
    
    filename_out = 'BASCOE_' + start_time.strftime('%Y%m%d.%H%M%S') + '.tif'    
    dst_ds = driver.Create(filename_out, xSize, ySize, num_bands, gdal.GDT_Float32)
    
#VGRID_DESCRIPTION = "Staggered hybrid-p: 
#p(lon,lat,1:nlev) = 0.5*(ap(1:nlev)+ap(2:nlev+1)) + 0.5*(bp(1:nlev)+bp(2:nlev+1))*p0(lon,lat)";
    p = np.zeros((num_bands, ySize, xSize))
    #p_avg = np.zeros((num_bands))
    #h = np.zeros((num_bands))
    #ap = np.flipud(ap)
    #bp = np.flipud(bp)
        
    for i in range(0, num_bands):
        dst_ds.GetRasterBand(num_bands-i).WriteArray(np.flipud(np.fliplr(data[i,:,:])))
        dst_ds.GetRasterBand(num_bands-i).SetNoDataValue(-9999)
        if num_bands <= 100:
            dst_ds.GetRasterBand(num_bands-i).ComputeStatistics(False)
        p[i,:,:] = 0.5*(ap[i]+ap[i+1]) + 0.5*(bp[i]+bp[i+1]) * p0[:,:]
        #p[i,:,:] = 0.5*(sum(ap[0:i])+sum(ap[1:i+1])) + 0.5*(sum(bp[0:i])+sum(bp[1:i+1])) * p0[:,:]                      
        
        #make average and convert it to millibars
        #p_avg[i] = np.average(p[:,:,i])/100
        #h[i] = ((1-math.pow((p_avg[i]/1013.25),0.190284)) * 145366.45) * 0.3048
        
    gh[num_bands-1,:,:] = (z + (temp[num_bands-1,:,:] * np.log(p0/p[num_bands-1,:,:]) * Rair))/g0    
#    print np.average(temp[num_bands-1,:,:] * np.log(p0/p[num_bands-1,:,:]) * Rair)    
#    print num_bands-1, gh[num_bands-1], h[num_bands-1]
#    print np.average(z)
    
#    print '%2d gh: %8.2f   p: %8.2f   temp: %3.2f   log(p): %2.4f' % (86, np.average(gh[num_bands-1,:,:]), np.average(p[num_bands-1,:,:]), np.average(temp[num_bands-1,:,:]), np.average(np.log(p0/p[num_bands-1,:,:])))
    
    for j in range(num_bands-1-1,-1,-1):
        thkness = (0.5*(temp[j+1,:,:]+temp[j,:,:]) * np.log(p[j+1,:,:]/p[j,:,:]) * Rair/g0)
        gh[j,:,:] = gh[j+1,:,:] + thkness
        #print '%2d gh: %8.2f   p: %8.2f   temp: %3.2f   log(p): %2.4f' % (j, np.average(gh[j,:,:]), np.average(p[j,:,:]), np.average(0.5*(temp[j+1,:,:]+temp[j,:,:])), np.average(np.log(p[j+1,:,:]/p[j,:,:]))) 
        
    h = np.average(gh, axis=(1,2))    
    
    lower_left = [-90, -180]
    upper_right = [90, 180]
    
    pixelHeight = abs((lower_left[0]-upper_right[0]) / float(ySize))
    pixelWidth = abs((lower_left[1]-upper_right[1]) / float(xSize))
    
    dst_ds.SetGeoTransform([lower_left[1], pixelWidth, 0, upper_right[0], 0, -pixelHeight])
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS('WGS84')
    dst_ds.SetProjection(srs.ExportToWkt())  
        
    dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.max(data)))
    dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.min(data)))
    dst_ds.SetMetadataItem('TIME_START', start_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
    dst_ds.SetMetadataItem('TIME_END', start_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
    dst_ds.SetMetadataItem('VERTICAL_LEVELS', str(h.tolist()).replace(' ', '')[1:-1])
    dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(num_bands))
    
    dst_ds = None
    
    return [filename_out]


if __name__ == '__main__':    
    if len(sys.argv) < 2:
        sys.exit('\nUsage: %s BASCOE_file(s) \n' % sys.argv[0] )
    
    files = sys.argv[1:]
    for file in files:
        if not os.path.exists(file):
            print '\nERROR: File %s was not found!\n' % file
            continue
            
        createImgBASCOE(os.path.abspath(file))

    exit(0)

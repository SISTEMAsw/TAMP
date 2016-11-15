#!/usr/bin/env python

import sys, os
import gdal
import numpy as np
from gdalconst import GDT_Float32
from osgeo import osr
import logging 
#import FLEXPART module
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append("%s/../lib/FLEXPART" % script_dir)

import read_header as rh
import read_grid as rg

def createImgFLEXPART(inputPath):
    driver = gdal.GetDriverByName('GTiff')
    
    H = rh.Header(inputPath)
    #H.fill_backward(nspec=(0,1))
    
    lower_left = [H.outlon0, H.outlat0]
    upper_right = [int(H.outlon0 + (H.dxout*H.numxgrid)), int(H.outlat0 + (H.dyout*H.numygrid))]    
    heightLevels = H.outheight
    timestamps = H.available_dates
    
    outFileList = []
        
    for t in timestamps:
        G = rg.read_grid(H,date=t)
        grid = G[(0, t)]
        
        volume = grid.grid[:,:] * 112/35
        
        xSize = volume.shape[0]
        ySize = volume.shape[1]
        numBands = volume.shape[2]
        
        filename = 'FLEXPART_SO2_' + t[:8] + '.' + t[8:] + '.tif'
        dst_ds = driver.Create(filename, xSize, ySize, numBands, GDT_Float32)
        
        for i in range(numBands):            
            band = volume[:,:,i].squeeze().transpose()
            band = np.flipud(band)            
            dst_ds.GetRasterBand(i+1).WriteArray(band)
            
            dst_ds.GetRasterBand(i+1).SetNoDataValue(-9999)
            dst_ds.GetRasterBand(i+1).ComputeStatistics(False)
    
        pixelWidth = abs((lower_left[0]-upper_right[0]) / xSize)
        pixelHeight = abs((lower_left[1]-upper_right[1]) / ySize)
    
        dst_ds.SetGeoTransform([lower_left[0], pixelWidth, 0, upper_right[1], 0, -pixelHeight])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('WGS84')
        dst_ds.SetProjection(srs.ExportToWkt())
    
        time = t[:4] + '-' + t[4:6] + '-' + t[6:8] + 'T' + t[8:10] + ':' + t[10:12] + ':' + t[12:14] + 'Z'
        dst_ds.SetMetadataItem('TIME_START', time)
        dst_ds.SetMetadataItem('TIME_END', time)
        
        dst_ds.SetMetadataItem('GLOBAL_MIN', str(np.amin(volume[:])))
        dst_ds.SetMetadataItem('GLOBAL_MAX', str(np.amax(volume[:])))
        
        levels = str()
        for l in heightLevels:
            levels += str(l) + ','
        levels = levels[:-1]
        
        dst_ds.SetMetadataItem('VERTICAL_LEVELS', levels)
        dst_ds.SetMetadataItem('VERTICAL_LEVELS_NUMBER', str(len(heightLevels)))        
        
        dst_ds = None  
        
        outFileList.append(filename)
        logging.debug('Finished processing for ' + t)
        
    return outFileList
        
if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('\nUsage: %s FLEXPART_directory \n' % sys.argv[0])
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('\nERROR: Path %s was not found\n' % sys.argv[0])
    
    inputPath = sys.argv[1]    
    createImgFLEXPART(inputPath)
    
    exit(0)

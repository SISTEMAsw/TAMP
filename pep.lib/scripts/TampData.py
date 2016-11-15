#!/usr/bin/env python

# TAMP-Project:    pep.lib 
# Version:         0.02
# Date:            2016-01-29
# Description:     This module manage and manipulate the data get by mwcs. Store data as array.
#                  Function available are: min, max, std, spatial average, temporal average,
#                  unit conversion, subtract, add
# Author:          Moris Pozzati
#
# ChangeLog:       2016-07-07    Added get_as_tiff() 
# 
#

import os
import numpy as np
import numpy.ma as ma
import gdal
from gdalconst import *
import subprocess
import random
import string
from ConfigParser import SafeConfigParser
import logging  

remapper = os.path.dirname(os.path.realpath(__file__))+'/../bin/remap'
installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

class TampData:
    
    def __init__(self,filename):
        self.filename = filename
        dataset = gdal.Open( filename, GA_ReadOnly )
        if not dataset is None:
            geotransform = dataset.GetGeoTransform()
            if not geotransform is None:
                self.pixel_size = geotransform[1]
            band = dataset.GetRasterBand(1)
            self.no_value = band.GetNoDataValue()
            self.dataset = dataset       
            self.data = None
            self.output_geotransform = geotransform
            self.output_projection = dataset.GetProjection()
            self.output_RasterXSize = dataset.RasterXSize
            self.output_RasterYSize = dataset.RasterYSize
            self.output_DataType = dataset.GetRasterBand(1).DataType
            self.output_numBands = dataset.RasterCount
            
    def __band_in_ds(self):
        return self.dataset.RasterCount

    def get_no_data_value(self):
        return self.no_value
    
    def get_pixel_size(self):
        return self.pixel_size
        
    def load_data(self):
        band = self.dataset.GetRasterBand(1)
        data = band.ReadAsArray()
        data = data[:, :, np.newaxis]
        for i in range(self.__band_in_ds()-1):
            band = self.dataset.GetRasterBand(i+2)
            data = np.dstack((data,band.ReadAsArray())) 
        self.data = ma.masked_equal(data,self.no_value)    
        data = None
        band = None  
    
    def get_data(self):
        return self.data    

    def __remap_bands(self,i,pixel_size,ur_lat,ll_lon,ll_lat,ur_lon):
        #define tmp filename 
        filename_sl = os.path.splitext(self.filename)[0]+'_'+ str(i).zfill(2)+'.tif'
        remapped_sl =  os.path.splitext(self.filename)[0]+'_'+ str(i).zfill(2)+'_remapped.tif'
        #extract band
        band = self.dataset.GetRasterBand(i).ReadAsArray()
        #create new tif
        driver = gdal.GetDriverByName( 'GTiff' )
        data_ds = driver.Create(filename_sl, self.dataset.RasterXSize , self.dataset.RasterYSize, 1, self.dataset.GetRasterBand(1).DataType, ['COMPRESS=LZW'])
        data_ds.SetGeoTransform(self.dataset.GetGeoTransform())
        data_ds.SetProjection(self.dataset.GetProjection())
        band = self.dataset.GetRasterBand(i).ReadAsArray()
        data_ds.GetRasterBand(1).WriteArray(band)
        band = None
        data_ds = None
        #remap new tiff
        FNULL = open(os.devnull, 'w')
        subprocess.call([remapper,'-i',filename_sl,'-o',remapped_sl,'-l',str(ur_lat),str(ll_lon),'-e',str(ll_lat)+','+str(ur_lon),'-s',str(pixel_size),'-n',str(self.no_value)],stdout=FNULL,stderr=FNULL)
        #load data from remapped band
        remapped_ds = gdal.Open( remapped_sl, GA_ReadOnly )
        band = remapped_ds.GetRasterBand(1)
        self.output_geotransform = remapped_ds.GetGeoTransform() 
        self.output_projection = remapped_ds.GetProjection()
        self.output_RasterXSize = remapped_ds.RasterXSize
        self.output_RasterYSize = remapped_ds.RasterYSize
        self.output_DataType = remapped_ds.GetRasterBand(1).DataType
        if os.path.isfile(filename_sl):
            os.remove(filename_sl)
        if os.path.isfile(remapped_sl):
            os.remove(remapped_sl)
        return  band.ReadAsArray()

    
    def remap_in_grid(self,pixel_size,ur_lat,ll_lon,ll_lat,ur_lon):
        data =self.__remap_bands(1,pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
        data = data[:, :, np.newaxis]
        for i in range(self.__band_in_ds()-1):
            band = self.__remap_bands(i+2,pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
            data = np.dstack((data,band))         
        self.data = ma.masked_equal(data,self.no_value) 
        return None

    def __randomfilename(self):
        #LOAD CONFIGURATION
        try:
            parser = SafeConfigParser()
            parser.read("%s/../etc/pep_lib.ini" % installation_dir)
            tmp_dir = parser.get("Fs","tmpdir")
        except Exception as e:
            logging.error( "I am unable to load configuration")
            logging.error(str(e))
            logging.error('Using default tmp dir /tmp/')
            tmp_dir = '/tmp/' 
        return tmp_dir+''.join(random.choice(string.lowercase) for i in range(20))+'.tif'

    def get_as_tiff(self,data = None):
        #TODO: maybe the shape len, now, is ever 3
        try:
            if data is None:
                data = self.data
            # lo shape[2] e' il numero di bande
            if len(data.shape) == 3:
                nbands = data.shape[2] 
            else:
                nbands = 1
            driver = gdal.GetDriverByName( 'GTiff' )
            data_ds_filename = self.__randomfilename()
            data_ds = driver.Create(data_ds_filename, self.output_RasterXSize , self.output_RasterYSize, nbands, self.output_DataType)
            data_ds.SetGeoTransform(self.dataset.GetGeoTransform())
            data_ds.SetProjection(self.dataset.GetProjection())
            if len(data.shape) == 3:
                for i in range(nbands):
                     data_ds.GetRasterBand(i+1).WriteArray(data[:,:,i])
                     data_ds.GetRasterBand(i+1).SetNoDataValue(-9999)
            else:
                logging.debug(str(data.shape))
                logging.debug(str(self.output_RasterXSize))
                logging.debug(str(self.output_RasterYSize))
                data_ds.GetRasterBand(1).WriteArray(data)
                data_ds.GetRasterBand(1).SetNoDataValue(-9999)
            data_ds = None
            return  data_ds_filename
        except Exception as e: 
            logging.error( "Unable to create geotiff")
            logging.error(str(e))
            raise
        return None 
    
def min_data(tamp_data):
    return np.ma.min(tamp_data.get_data())    
    
def max_data(tamp_data):
    return np.ma.max(tamp_data.get_data())    

def std(tamp_data):
    return ma.std(tamp_data.get_data())    
    
def spatial_average(tamp_data):
    return ma.average(tamp_data.get_data())
  
def temporal_average(tamp_data):
    #very old: return ma.average(ma.average(tamp_data.get_data(),axis=0),axis=0)
    #TODO maybe there is an error in num bands
    # old: return tamp_data.get_as_tiff(ma.average(tamp_data.get_data(),axis=2))
    # I think that tamp_data is already a a temporal average because mwcs don't return multi band tiff. this is the solution for me:
    return tamp_data.get_as_tiff()

def unit_conversion(tamp_data,offset,gain):
    return tamp_data.get_as_tiff(((tamp_data.get_data()+offset)*gain).filled())
    
def subtract(tamp_data_1,tamp_data_2,ur_lat,ll_lon,ll_lat,ur_lon):
    pixel_size = min(tamp_data_1.get_pixel_size(),tamp_data_2.get_pixel_size())
    tamp_data_1.remap_in_grid(pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
    tamp_data_2.remap_in_grid(pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
    return tamp_data_1.get_as_tiff((np.subtract(tamp_data_1.get_data(),tamp_data_2.get_data())).filled())

def add(tamp_data_1,tamp_data_2,ur_lat,ll_lon,ll_lat,ur_lon):
    pixel_size = min(tamp_data_1.get_pixel_size(),tamp_data_2.get_pixel_size())
    tamp_data_1.remap_in_grid(pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
    tamp_data_2.remap_in_grid(pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
    return  tamp_data_1.get_as_tiff((np.add(tamp_data_1.get_data(),tamp_data_2.get_data())).filled())

def correlation(tamp_data_1,tamp_data_2,ur_lat,ll_lon,ll_lat,ur_lon):
    logging.error(tamp_data_1.output_RasterXSize)
    logging.error(tamp_data_2.output_RasterXSize)
    pixel_size = min(tamp_data_1.get_pixel_size(),tamp_data_2.get_pixel_size())
    logging.debug('Remap tamp_data_1')
    tamp_data_1.remap_in_grid(pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
    logging.debug('Remap tamp_data_2')
    tamp_data_2.remap_in_grid(pixel_size,ur_lat,ll_lon,ll_lat,ur_lon)
    mask = (tamp_data_1.get_data().mask == True) | (tamp_data_2.get_data().mask == True)
    data_result = np.subtract(tamp_data_1.get_data()[:,:,0],tamp_data_2.get_data()[:,:,0])
    data_result_masked = ma.masked_array(data_result,mask)
    return  data_result_masked.mean(), data_result_masked.std(), data_result_masked.min(), data_result_masked.max()

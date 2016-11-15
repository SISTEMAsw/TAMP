#!/usr/bin/env python

# TAMP-Project:    pep.lib
# Version:         0.01
# Date:            2016-04-26
# Description:     "Pollemon" test 
# Author:          Moris Pozzati
#
# ChangeLog:
# 
#
from WcsRequest import *
import TampData
import datetime
import logging
import sys,os
import numpy as np
import gdal
from gdalconst import *


class Pollemon:
    def __init__(self,coverage1,coverage2,ll_lat,ur_lat,ll_lon,ur_lon,t_s,t_e):
        wcs_server = 'http://meeo-dar-05'
        self.c1,self.c2 = None, None
        self.data1,self.data2 = None, None
        self.start_date = datetime.datetime.fromtimestamp(t_s).replace(hour=0,minute=0,second=0)
        self.start_timestamp = (self.start_date - datetime.datetime(1970, 1, 1)).total_seconds()
        self.end_timestamp = self.start_timestamp  
        self.c1 = WcsRequest(coverage1)
        self.c1.set_wcs_server(wcs_server)
        self.c1.set_subset_x(ll_lon,ur_lon)
        self.c1.set_subset_y(ll_lat,ur_lat)
        self.c2 = WcsRequest(coverage2)
        self.c2.set_wcs_server(wcs_server)
        self.c2.set_subset_x(ll_lon,ur_lon)
        self.c2.set_subset_y(ll_lat,ur_lat)   
        self.ll_lat = ll_lat
        self.ur_lat = ur_lat
        self.ll_lon = ll_lon
        self.ur_lon = ur_lon
        self.t_s = t_s
        self.t_e = t_e
        self.coverage1 = coverage1
        self.coverage2 = coverage2
        logging.debug('Pollemon object crated')

    def get_next(self):
        logging.debug('Try to get next element')
        if self.end_timestamp < self.t_e:
            self.end_date = self.start_date+datetime.timedelta(days=1)-datetime.timedelta(seconds=1)
            self.end_timestamp = (self.end_date - datetime.datetime(1970, 1, 1)).total_seconds()
            self.c1.set_subset_t(self.start_timestamp,self.end_timestamp)
            self.c2.set_subset_t(self.start_timestamp,self.end_timestamp)            
            try:
                try:
                    self.data1 = TampData.TampData(self.c1.get_result())
                    self.RasterXSize = self.data1.dataset.RasterXSize
                    self.RasterYSize = self.data1.dataset.RasterYSize
                    self.DataType = self.data1.dataset.GetRasterBand(1).DataType
                    self.GeoTransform = self.data1.dataset.GetGeoTransform()
                    self.Projection = self.data1.dataset.GetProjection()
                    if not self.GeoTransform is None:
                        self.pixel_size = self.GeoTransform[1]
                    logging.debug('New element: c1 acquired')
                except Exception as e:
                    logging.debug(e)
                    logging.debug('No element: c1 unavailable')
                    raise
                try:     
                    self.data2 = TampData.TampData(self.c2.get_result())
                    logging.debug('New element: c2 acquired')
                except Exception as e:
                    logging.debug(e)
                    logging.debug('No element: c2 unavailable')
                    raise     
                self.data1.load_data()
                self.data2.load_data()            
            except Exception as e:
                logging.debug(e)
                logging.debug('Error to acquire element(s)')
                pass
            logging.info('All elements acquired for: %s' % self.start_date.strftime('%Y-%m-%d'))
            self.start_date = self.start_date+datetime.timedelta(days=1)
            self.start_timestamp = (self.start_date - datetime.datetime(1970, 1, 1)).total_seconds()
            self.c1.clean()
            self.c2.clean()
            return True
        else:
            logging.warning('No elements acquired for: %s' % self.start_date.strftime('%Y-%m-%d'))
            return False

    def difference(self,no_value=-9999):
        logging.debug('Compute Difference') 
        logging.debug('Data1 shape: %s' % str(self.data1.get_data()[:,:,0].shape))
        logging.debug('Data2 shape: %s' % str(self.data2.get_data()[:,:-1,0].shape))
        #self.data1.remap_in_grid(self.pixel_size,self.ur_lat,self.ll_lon,self.ll_lat,self.ur_lon)
        #self.data2.remap_in_grid(self.pixel_size,self.ur_lat,self.ll_lon,self.ll_lat,self.ur_lon)
        #self.RasterXSize = self.data2.dataset.RasterXSize
        #self.RasterYSize = self.data2.dataset.RasterYSize
        #self.DataType = self.data2.dataset.GetRasterBand(1).DataType
        #self.GeoTransform = self.data2.dataset.GetGeoTransform()
        #logging.debug('Data1 shape: %s' % str(self.data1.get_data().shape))
        #logging.debug('Data2 shape: %s' % str(self.data2.get_data().shape))        
        mask = (self.data1.get_data().mask == True) | (self.data2.get_data().mask == True)
        self.data_result = np.subtract(self.data1.get_data()[:,:,0],self.data2.get_data()[:,:,0])
        np.ma.set_fill_value(self.data_result,-9999)
        logging.debug(self.data_result)
        
    def write_results(self,outputdir,new_coverage_name,no_value=-9999):
        try:
            logging.debug('Creating Tiff') 
            output_filename = outputdir+'/'+new_coverage_name+'_'+self.end_date.strftime('%Y%m%d')+'_4326.tif'
            driver = gdal.GetDriverByName( 'GTiff' )
            logging.debug('Tiff Size %s %s' %(self.RasterXSize,self.RasterYSize))
            data_ds = driver.Create(output_filename, self.RasterXSize , self.RasterYSize, 1, self.DataType)
            data_ds.SetGeoTransform(self.GeoTransform)
            data_ds.SetProjection(self.Projection)
            data_ds.GetRasterBand(1).SetNoDataValue(no_value)
            logging.debug(self.data_result.shape)
            data_ds.GetRasterBand(1).WriteArray(self.data_result.filled())
            #logging.debug(data_ds.GetRasterBand(1).ReadAsArray())
            band = None
            data_ds = None
            logging.info('New Tiff available: %s' % output_filename)
        except Exception as e:
            logging.debug(e)
            logging.error('Error to write %s' % output_filename)
            if os.path.isfile(self.filename):
                os.remove(output_filename)
            pass     

def statistics(input_dir):
    logging.info("file\tavg\tstd\tmin\tmax")
    file_list = os.listdir(input_dir)
    for input_file in file_list:
        data = TampData.TampData(input_dir+'/'+input_file)
        data.load_data()    
        TampData.min_data(data)
        logging.info("%s\t%f\t%f\t%f\t%f" %(input_file,TampData.spatial_average(data),TampData.std(data),TampData.min_data(data),TampData.max_data(data)))

                
if __name__ == "__main__":    
    log_level = 10
    logging.basicConfig(
     stream= sys.stdout,
     level= log_level,
     format='%(levelname)s\t| %(asctime)s | %(message)s'
    )
    logging.debug('Start Pollemon')    
    #pollemonObj = Pollemon('ZAMG_2MTEMPUPDATED_4326_025','TG_MEANTEMPK_4326_025',36,73,-10,30,1263686400,1372520800)
    #while pollemonObj.get_next():    
    #    pollemonObj.difference()
    #    pollemonObj.write_results('/home/moris/pollemon_updated','POLLEMON_UPDATED')
    statistics('/home/moris/pollemon_updated/')

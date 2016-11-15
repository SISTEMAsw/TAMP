#!/usr/bin/env python

# TAMP-Project:    pep.lib 
# Version:         1.0
# Date:            2016-10-03
# Description:     Ground Measurament Class Managemtn
# Author:          Moris Pozzati
#
# ChangeLog:
#                  2016-01-29 v0.01
#                  first release
#
#                  2016-10-03 v1.0
#                  select product from WCS coverage (measurement_unit and application field)
#                  
# 
import psycopg2
import datetime
from datetime import timedelta
import time
from  WcsRequest import *
from  TampData import *
import numpy as np
import logging 

class GroundData:

    def __init__(self, coverage):
        try:
            self.__sql_connect("tamp")
            query = "SELECT measurement_unit, application FROM data_ingestion_collectiontable WHERE \"coverageID\" like '%s'" % coverage
            logging.debug(query)
            self.cur.execute(query)
            data = self.cur.fetchall()
            mu = data[0][0]
            a = data[0][1]
            self.__sql_disconnect()
            self.collection = "p.measurement_unit like '%s' AND p.product like '%s'" % (mu,a)
        except Exception as e:
            logging.error('GroundData initialization problem')
            logging.error(str(e))
        self.subset_lat = ""
        self.subset_lon = ""
        self.subset_t = ""
        
        
    def set_subset_lon(self,min_lon,max_lon):
        if min_lon is not None and max_lon is not None:
            self.subset_lon = " AND (s.longitude BETWEEN %s AND %s) " %(min_lon,max_lon)
            
    def set_subset_lat(self,min_lat,max_lat):
        if min_lat is not None and max_lat is not None:
            self.subset_lat = " AND (s.latitude BETWEEN %s AND %s) " %(min_lat,max_lat)
    
    def set_subset_t(self,t_s,t_e): 
        if t_s is not None:
            self.subset_t = " AND m.observation_time_start <= '%s' AND m.observation_time_end >= '%s' " %(t_e,t_s)
 

    def __sql_connect(self,dbname="groundbased"):
        try:
            self.conn = psycopg2.connect( "dbname='%s' user='%s' host='%s' password='%s'" %(dbname,"tamp","vtpip.zamg.ac.at","tampuser"))
            self.cur = self.conn.cursor()
            #print "DB connection OK"
        except Exception as e:
            logging.error("I am unable to connect to the database")
            raise

    def __sql_disconnect(self):
        self.cur.close()
        self.conn.close()


    def load_data(self):
        self.__sql_connect()
        query="SELECT * FROM measurements as m, products as p, stations as s WHERE s.id = m.stations_id AND p.id = m.observed_field AND %s %s %s %s  AND value <> -9999999 " %(self.collection,self.subset_lat,self.subset_lon,self.subset_t)
        logging.debug(query)
        self.cur.execute( query )
        self.data = self.cur.fetchall()
        logging.debug(len(self.data))
        self.__sql_disconnect()

    def get_data(self):
        return self.data
 

    def get_WCS_correlation(self,coverage, spatial_degs_tollerance, temporal_mins_tollerance):
        res = [] 
        for data_row in self.data:
            c1= WcsRequest(coverage)
            c1.set_subset_x(float(data_row[13])-spatial_degs_tollerance,float(data_row[13])+spatial_degs_tollerance)
            c1.set_subset_y(float(data_row[12])-spatial_degs_tollerance,float(data_row[12])+spatial_degs_tollerance)
            c1.set_subset_t(time.mktime((data_row[2]-timedelta(minutes=temporal_mins_tollerance)).timetuple()),time.mktime((data_row[3]+timedelta(minutes=temporal_mins_tollerance)).timetuple()))
            try:
                data1 = TampData(c1.get_result())
                data1.load_data()
                #res.append(np.ma.average(data1.get_data()))
                res.append([data_row[2].strftime('%Y-%m-%dT%H:%M:%S'),float(data_row[5]),float(np.ma.average(data1.get_data())),float(data_row[5])-float(np.ma.average(data1.get_data()))])
                #print "WCS:\t%f\tDB:\t%f" %(np.ma.average(data1.get_data()),data_row[5])
                #print "%s;%f;%f;%f" %(data_row[2].strftime('%Y-%m-%dT%H:%M:%S'),data_row[5],np.ma.average(data1.get_data()),float(data_row[5])-float(np.ma.average(data1.get_data())))
            except Exception as e:
                logging.error("No Correlation between ground data and wcs data")
                logging.error(str(e))
                #raise
        #print res
        return res

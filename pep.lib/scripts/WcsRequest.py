#!/usr/bin/env python

# TAMP-Project:    pep.lib
# Version:         0.01
# Date:            2016-01-15
# Description:
# Author:          Moris Pozzati
#
# ChangeLog:       2016-01-15 v0.01
#                  first version
#
#                  2016-01-15 v0.02
#                  in clean(), added None check and None set
# 
#
import urllib2
import cgi
import os
import logging 
from ConfigParser import SafeConfigParser

installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

class WcsRequest:   
    def __init__(self, coverage):
        self.coverage = "&CoverageId=%s" %(coverage)
        self.subset_x = ""
        self.subset_y = ""
        self.subset_t = ""
        self.format = '&format=image/tiff'
        self.wcs_server = 'http://vtdas-dave.zamg.ac.at'
        self.filename = None
        
    def set_as_XML(self):
        #XML requests are non implemented
        self.format = ""
    
    def set_as_tiff(self):
        self.format = '&format=image/tiff'
        
    def set_subset_x(self,ll_lon,ur_lon):
        if ll_lon is not None and ur_lon is not None:
            self.subset_x = "&subset=Long(%s,%s)" %(ll_lon,ur_lon)
            
    def set_subset_y(self,ll_lat,ur_lat):
        if ll_lat is not None and ur_lat is not None:
            self.subset_y = "&subset=Lat(%s,%s)" %(ll_lat,ur_lat)
    
    def set_subset_t(self,t_s,t_e = None): 
        if t_s is not None:
            if t_e is not None:
                self.subset_t = "&subset=t(%s,%s)" %(t_s,t_e)
            else:
                self.subset_t = "&subset=t(%s,%s)" %(t_s,t_s)
    
    def set_wcs_server(self,wcs_server):
        self.wcs_server = wcs_server 
                
    def __wcs_query(self):
        wcs_query = '%s/wcs?service=WCS&Request=GetCoverage&version=2.0.0%s%s%s%s%s' %(self.wcs_server,self.coverage,self.subset_x,self.subset_y,self.subset_t,self.format)
        logging.debug(wcs_query)
        return wcs_query
        
    def get_result(self):
        #print self.filename
        if self.filename is None:
            try:
                logging.debug("WCS Query: %s" % self.__wcs_query())
                req = urllib2.Request(self.__wcs_query())
                res = urllib2.urlopen(req)
                logging.debug("Query executed")
                #get filename  of tiff
                _, params = cgi.parse_header(res.headers.get('Content-Disposition', ''))
                filename = params['filename']
                #get data from request result
                wcs_data = res.read()
                #save result in tmp dir
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
        
                filename=tmp_dir+filename
                if filename != None:
                    tif = open( filename, "w")
                    tif.write( wcs_data )
                    tif.close()
                else:
                    raise
            except:
                logging.debug( "No WCS query result or WCS query result is empty")
                raise
            self.filename = filename  
        return self.filename    
    
    def clean(self):
        if self.filename is not None and os.path.isfile(self.filename):
            os.remove(self.filename)
            self.filename = None

    def clean2(self):
        if self.filename is not None: 
            self.filename = None



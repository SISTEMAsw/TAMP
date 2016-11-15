#!/usr/bin/env python

# TAMP-Project:    pep.lib
# Version:         1.0
# Date:            2016-10-03
# Description:     This library groups functionality used to provide results "on-the-fly" between wcs data and ground db data
# Author:          Moris Pozzati
#
# ChangeLog:       2016-07-07 v0.01   
#                  Splitted from tampProcessingUtilities.py
#
#                  2016-10-03 v1.0
#                  removed -g option for correlation between gd and wcs
# 
#

import sys
import os
import getopt
import TampData
import GroundData
import FilesystemData
from  WcsRequest import WcsRequest
import numpy
import logging
import argparse
from datetime import datetime,timedelta
from ConfigParser import SafeConfigParser

installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) 
numpy.set_printoptions(threshold=numpy.nan)


def get_wcs_data(coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e = None):
    data,c = None,None
    try:
        if all(x is not None for x in  [coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s]):
            c= WcsRequest(coverage)
            c.set_subset_x(ll_lon,ur_lon)
            c.set_subset_y(ur_lat,ll_lat)
            if t_e is not None:
                c.set_subset_t(t_s,t_e)
            else:
                c.set_subset_t(t_s)
            data = TampData.TampData(c.get_result())
            data.load_data()
            c.clean()
    except:
        data = None
        pass
    return data

def get_ground_data(coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e):
    gd = None
    try:
        gd = GroundData.GroundData(coverage)
        gd.set_subset_lat(ll_lat,ur_lat)
        gd.set_subset_lon(ll_lon,ur_lon)
        gd.set_subset_t(t_s,t_e)
        gd.load_data()
        logging.debug(gd)
    except:
        gd = None
        pass 
    return gd

def get_gd_WCS_correlation(gd,coverage, spatial_degs_tolerance, temporal_mins_tolerance):
    data = None
    if gd is not None:
        try:
            data = gd.get_WCS_correlation(coverage, spatial_degs_tolerance, temporal_mins_tolerance) 
        except:
            raise
            logging.error("No Correlation between ground data and wcs data")
    return data

def get_WCS_WCS_correlation(coverage1,coverage2,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e):
    res = []
    current_timestamp = t_s
    next_date = datetime.fromtimestamp(t_s).replace(hour=0,minute=0,second=0)+timedelta(days=1)-timedelta(seconds=1)
    next_timestamp = (next_date - datetime(1970, 1, 1)).total_seconds()
    while  next_timestamp < t_e:
        try:
            data1 = get_wcs_data(coverage1,ur_lat,ll_lat,ll_lon,ur_lon,current_timestamp,next_timestamp)
            data2 = get_wcs_data(coverage2,ur_lat,ll_lat,ll_lon,ur_lon,current_timestamp,next_timestamp)
            if None not in [data1,data2]:
                res.append((datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%dT%H:%M:%S'),datetime.fromtimestamp(next_timestamp).strftime('%Y-%m-%dT%H:%M:%S'),TampData.correlation(data1,data2,ur_lat,ll_lon,ll_lat,ur_lon)))
        except Exception as e:
            logging.error(str(e))
            pass       
        current_timestamp = next_timestamp+1    #timedelta(days =1)  = 86400 secs 
        next_timestamp = next_timestamp+86400
    try:
        data1 = get_wcs_data(coverage1,ur_lat,ll_lat,ll_lon,ur_lon,current_timestamp,t_e)
        data2 = get_wcs_data(coverage2,ur_lat,ll_lat,ll_lon,ur_lon,current_timestamp,t_e)
        if None not in [data1,data2]:
            res.append((datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%dT%H:%M:%S'),datetime.fromtimestamp(next_timestamp).strftime('%Y-%m-%dT%H:%M:%S'),TampData.correlation(data1,data2,ur_lat,ll_lon,ll_lat,ur_lon)))
    except Exception as e:
        logging.error(str(e))
        pass
    return res

if __name__ == "__main__":

    #LOAD CONFIGURATION
    try:
        parser = SafeConfigParser()
        parser.read("%s/../etc/pep_lib.ini" % installation_dir)
    except Exception as e:
        print "I am unable to load configuration"
        print str(e)

    #set logger
    logging.basicConfig(
     #stream= sys.stdout,
     filename=installation_dir+"/../log/tampDataAssessmentUtilities.log",
     level= int(parser.get("Logger","loglevel")),
     format='%(levelname)s\t| %(asctime)s | %(message)s'
    )

    parser = argparse.ArgumentParser(prog=sys.argv[0],description='Utility used to provide results "on-the-fly" between wcs data and ground db data',epilog='SISTEMA GmbH  <http://www.sistema.at>')
    parser_function = parser.add_argument_group('Required function')
    parser_function.add_argument(dest='function',metavar='FUNCTION',choices=['correlation'],help='Available functions are: correlation' )
    parser_coverage = parser.add_argument_group('Coverage required options')
    parser_coverage.add_argument('-c',dest='coverage',default=None,required=True,help='CoverageID to search in wcs server')    
    parser_coverage.add_argument('-o',dest='second_coverage',default=None,help='Second coverageID to search in wcs server')
    parser_coverage.add_argument('-u',dest='ur_lat',default=None,type=float,required=True,help='Upper latitude')
    parser_coverage.add_argument('-d',dest='ll_lat',default=None,type=float,required=True,help='Lower latitude')
    parser_coverage.add_argument('-l',dest='ll_lon',default=None,type=float,required=True,help='Far west latitude')
    parser_coverage.add_argument('-r',dest='ur_lon',default=None,type=float,required=True,help='Far east latitude')
    parser_coverage.add_argument('-s',dest='t_s',default=None,type=int,required=True,help='Start time/date expressed in Unix Timestamp')
    parser_coverage.add_argument('-e',dest='t_e',default=None,type=int,help='End time/date expressed in Unix Timestamp')
    parser_correlation= parser.add_argument_group('Function \'correlation\' optional arguments')
    parser_correlation.add_argument('--spatialtolerance',metavar='degree',type=float,default=1,help='Apply the spatialtolerance in correlation function, default 1 degree')
    parser_correlation.add_argument('--temporaltolerance',metavar='mins',type=int,default=60,help='Apply the temporaltolerance in correlation function, default 60 mins')  
    args = parser.parse_args()
    
    #data1,c1 = __get_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
    #data2,c2 = __get_data(args.other_coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)

    try:   
        logging.debug(args.function)     
        if 'correlation' ==  args.function:
            if args.second_coverage and None not in [args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e]:
                print get_WCS_WCS_correlation(args.coverage,args.second_coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            elif None not in [args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e]:
                gd = get_ground_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,datetime.fromtimestamp(args.t_s).strftime('%Y-%m-%d %H:%M:%S'),datetime.fromtimestamp(args.t_e).strftime('%Y-%m-%d %H:%M:%S'))
                if all( x is not None for x in [gd,args.coverage,args.spatialtolerance,args.temporaltolerance]):
                    print get_gd_WCS_correlation(gd,args.coverage, args.spatialtolerance, args.temporaltolerance)
                else:
                    logging.warning('WCS returns no data')

             
    except:
        raise
        logging.error('Unexpected error ')
        
    ##cleaning FS
    #try:
    #    if c1 is not None: 
    #        c1.clean() 
    #        c1 = None
    #    if c2 is not None:       
    #        c2.clean() 
    #        c2 = None
    #    if data1 is not None:
    #        data1 = None   
    #    if data2 is not None:
    #        data2 = None       
    #except:
    #    raise
    #    logging.error('Unexpected error in clean procedure')
    #    sys.exit(4) 
    #    

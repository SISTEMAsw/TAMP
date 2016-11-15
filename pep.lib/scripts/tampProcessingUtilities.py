#!/usr/bin/env python

# TAMP-Project:    pep.lib
# Version:         0.02
# Date:            2016-01-15
# Description:     This library groups functionality used to provide results "on-the-fly" from wcs data 
# Author:          Moris Pozzati
#
# ChangeLog:       2016-05-31    added argparse
#                  2016-07-07    Moved groundbased function on tampDataAssessmentUtilities.py
# 
#

import sys,os,shutil
import getopt
import TampData
import GroundData
import FilesystemData
from  WcsRequest import WcsRequest
import numpy
import logging
import argparse
import psycopg2
import paramiko
import random
import string
import glob
from datetime import datetime,timedelta
from ConfigParser import SafeConfigParser


installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) 
numpy.set_printoptions(threshold=numpy.nan)

def __load_conf():
     #LOAD CONFIGURATION
    try:
        parser = SafeConfigParser()
        parser.read("%s/../etc/pep_lib.ini" % installation_dir)
    except Exception as e:
        print "I am unable to load configuration"
        print str(e)
        raise
    return parser

def __get_data(coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e = None):
    return get_wcs_data(coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e)

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
    except:
        data = None
        c = None
        pass
    return data,c

def get_3D_LIDAR_data(coverage, lidar_coverage, t_s, t_e, spatial_tolerance=1.1, temporal_tolerance=43200):
    # find stations in bb
    # get coords of station
    # wcs on the 3d collection of station coords
    # create geotiff (like LIDAR) from model data
    
    # TODO: add tolerance
    # TODO: maybe automatically search collections
    # TODO: just 1x1xh or 6x6xh?

    c1 = WcsRequest(lidar_coverage)
#    c1.set_subset_x(ll_lon, ur_lon)
#    c1.set_subset_y(ll_lat, ur_lat)
    c1.set_subset_t(t_s, t_e)
    """
    ll_lon -= spatial_tolerance
    ll_lat -= spatial_tolerance
    ur_lon += spatial_tolerance
    ur_lat += spatial_tolerance
    """
    timestring = '%Y-%m-%d %H:%M:%S'
    
    try:        
        src_ds = gdal.Open(c1.get_result(), GA_ReadOnly)
        ds = gdal.Open(c1.get_result())
        width = ds.RasterXSize
        height = ds.RasterYSize
        gt = ds.GetGeoTransform()
        lidar_ll_lon = gt[0] - spatial_tolerance
        lidar_ll_lat = gt[3] + width*gt[4] + height*gt[5] - spatial_tolerance
        lidar_ur_lon = gt[0] + width*gt[1] + height*gt[2] + spatial_tolerance
        lidar_ur_lat = gt[3] + spatial_tolerance
                
        """
        if lidar_ll_lat < ll_lat or lidar_ll_lon < ll_lon or lidar_ur_lat > ur_lat or lidar_ur_lon > ur_lat:
            print 'LIDAR is outside of the bounding box'
            raise Exception
        """
    except:
        print "No LIDAR data found"
        raise
    
    c2 = WcsRequest(coverage)
    """
    c2.set_subset_x(ll_lon, ur_lon)
    c2.set_subset_y(ll_lat, ur_lat)
    """
    c2.set_subset_x(lidar_ll_lon, lidar_ur_lon)
    c2.set_subset_y(lidar_ll_lat, lidar_ur_lat)
    c2.set_subset_t(t_s, t_e)
    
    try:
        data2 = TampData.TampData(c2.get_result())
        data2.load_data()
        res = data2.get_data()
        res = np.average(np.average(res,axis=0),axis=0)
    except:
        print "Found LIDAR, but no BASCOE"
        raise
    print 'Found correlation'
    return res

def spatialAverage(coverage,ll_lat,ll_lon,ur_lat,ur_lon,t_s):
    data1,c1 = __get_data(coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s)
    if data1 is not None:
        try:
            res = TampData.spatial_average(data1)
            c1.clean()
            return res
        except:
            logging.error("Computation Error")
    else:
        logging.warning("WCS returns no data")

def temporalAverage(coverage,ll_lat,ll_lon,ur_lat,ur_lon,t_s,t_e):
    data1,c1 = __get_data(coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e)
    if data1 is not None:
        try:
            res = TampData.temporal_average(data1)
            c1.clean()
            return res
        except:
            logging.error("Computation Error")
    else:
        logging.warning("WCS returns no data")

def conversion(offset,gain,coverage,ll_lat,ll_lon,ur_lat,ur_lon,t_s,t_e):
    data1,c1 = __get_data(coverage,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e)
    if all( x is not None for x in [data1,offset,gain]):
        try:
            res = TampData.unit_conversion(data1,offset,gain)
            c1.clean()
            return res
        except:
            logging.error("Computation Error")
    else:
        logging.warning("WCS returns no data")
       
def add(coverage1,coverage2,ll_lat,ll_lon,ur_lat,ur_lon,t_s,t_e):
    data1,c1 = __get_data(coverage1,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e)
    data2,c2 = __get_data(coverage2,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e)
    if all( x is not None for x in [data1,data2,ur_lat,ll_lon,ll_lat,ur_lon]):
        try:
            res =  TampData.add(data1, data2, ur_lat,ll_lon,ll_lat,ur_lon)
            c1.clean()
            c2.clean()
            return res
        except:
            logging.error("Computation Error")
            raise
    else:
        logging.warning("WCS returns no data")

def subtract(coverage1,coverage2,ll_lat,ll_lon,ur_lat,ur_lon,t_s,t_e):
    data1,c1 = __get_data(coverage1,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e)
    data2,c2 = __get_data(coverage2,ur_lat,ll_lat,ll_lon,ur_lon,t_s,t_e)
    if all( x is not None for x in [data1,data2,ur_lat,ll_lon,ll_lat,ur_lon]):
        try:
            res = TampData.subtract(data1, data2, ur_lat,ll_lon,ll_lat,ur_lon)
            c1.clean()
            c2.clean()
            return res
        except:
            logging.error("Computation Error")
    else:
        logging.warning("WCS returns no data")

def downloadcollection(config):
    with open(config,'r') as inf:
        dict_coll = eval(inf.read())
    destination = dict_coll['workingDir']    
    coverage = dict_coll['inputCollectionName']
    ll_lon = dict_coll['min_lon']
    ur_lon = dict_coll['max_lon']
    ur_lat = dict_coll['max_lat']
    ll_lat = dict_coll['min_lat']
    t_s = (datetime.strptime(dict_coll['start_date'],'%Y-%m-%d') - datetime(1970, 1, 1)).total_seconds()
    t_e = (datetime.strptime(dict_coll['end_date'],'%Y-%m-%d') - datetime(1970, 1, 1)).total_seconds()

    res = []
    try:
        if not os.path.exists(destination):
            logging.debug('Destination dir don\'t exixts. Creating it')
            os.makedirs(destination)
    except:
        logging.error('Impossible to create destination dir '+destination)
        return res
    parser = __load_conf()
    try:
        conn = psycopg2.connect( "dbname='%s' user='%s' host='%s' password='%s'" %(parser.get("db","name"),parser.get("db","user"),parser.get("db","host"),parser.get("db","pass")))
        cur = conn.cursor()
    except Exception as e:
        log.error("I am unable to connect to db")
        log.debug(str(e))
        return res
    #prepare wcs request
    c= WcsRequest(coverage)
    c.set_subset_x(ll_lon,ur_lon)
    c.set_subset_y(ur_lat,ll_lat)
    #set first timeframe
    current_timestamp = t_s
    next_date = datetime.fromtimestamp(t_s).replace(hour=0,minute=0,second=0)+timedelta(days=1)-timedelta(seconds=1)
    next_timestamp = (next_date - datetime(1970, 1, 1)).total_seconds()
    while  next_timestamp < t_e:
        logging.debug("next_timestamp=%s" %next_timestamp)
        try:
            c.set_subset_t(current_timestamp,next_timestamp)
            tif = c.get_result()
            logging.debug(tif)
            if None not in [tif]:
                shutil.move(tif,destination+'/'+os.path.basename(tif))
                res.append(os.path.normpath(destination+'/'+os.path.basename(tif)))
            #c.clean2()
        except Exception as e:
            logging.warning(str(e))
            pass    
        c.clean2() 
        #set next timeframe
        current_timestamp = next_timestamp+1
        next_timestamp = next_timestamp+86400
    try:
        #get last timeframe
        tif = c.set_subset_t(current_timestamp,t_e)
        if None not in [tif]:
            shutil.move(tif,destination+'/'+os.path.basename(tif))
            res.append(os.path.normpath(destination+'/'+os.path.basename(tif)))
    except Exception as e:
        logging.warning(str(e))
        pass  
    ## creating procConf.txt 
    #if res != []:
    #    query = "SELECT name,source,application,\"group\",uploaded_by_id,status,\"IO\",\"coverageID\",measurement_unit,access,ipr,max_value,min_value from data_ingestion_collectiontable where \"coverageID\" like '"+coverage+"' "
    #    logging.debug(query)
    #    cur.execute( query )
    #    data = cur.fetchall()
    #    t =(('inputCollectionName',data[0][0]),
    #        ('source',data[0][1]),
    #        ('max_lat',max(ur_lat,ll_lat)),
    #        ('max_lon',max(ll_lon,ur_lon)),
    #        ('min_lat',min(ur_lat,ll_lat)),
    #        ('min_lon',min(ll_lon,ur_lon)),
    #        ('start_date',datetime.fromtimestamp(t_s).strftime('%Y-%m-%d')),
    #        ('end_date',datetime.fromtimestamp(t_e).strftime('%Y-%m-%d')),
    #        ('application',data[0][2]),
    #        ('group',data[0][3]),
    #        ('uploaded_by_id',data[0][4]),
    #        ('IO',data[0][5]), 
    #        ('coverageID',data[0][6]), 
    #        ('measurement_unit',data[0][7]), 
    #        ('access',data[0][9]), 
    #        ('ipr',data[0][9]), 
    #        ('max_value',data[0][10]), 
    #        ('min_value',data[0][11]))
    #    
    #    out_dict = dict((x, y) for x, y in t)
    #    out_file = open(destination+'/procConf.txt',"w")
    #    out_file.write(str(out_dict))
    #    out_file.close()
    return res  
    
def uploadcollection(conf,source):  
    parser = __load_conf()
    try:
        conn = psycopg2.connect( "dbname='%s' user='%s' host='%s' password='%s'" %(parser.get("db","name"),parser.get("db","user"),parser.get("db","host"),parser.get("db","pass")))
        cur = conn.cursor()
    except Exception as e:
        log.error("I am unable to connect to db")
        log.debug(str(e))
        return res
    logging.info("Upload product to vtdas server")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(parser.get("vtdas","host"), username=parser.get("vtdas","user"), password=parser.get("vtdas","pass"))
    sftp = ssh.open_sftp()
    remote_path = parser.get("vtdas","location")+os.path.basename(os.path.normpath(source))+'_'+''.join(random.choice(string.lowercase) for i in range(5))+'/'
    sftp.mkdir(remote_path)
    sftp.chdir(remote_path)
    #load dictionary
    #for txt_description in glob.glob(source+"*procConf.txt"):
    with open(conf,'r') as inf:
        dict_coll = eval(inf.read())
    #put file on vtpip
    for product in glob.glob(source+"/*.tif"):
        try:
            logging.debug('Put local %s to remote  %s' %(product,remote_path+os.path.basename(product)))
            sftp.put(product,remote_path+os.path.basename(product))
        except Exception as e:
            logging.warning(str(e))
    sftp.close()
    ssh.close()
    logging.info("Product uploaded")
    logging.debug("Add row to vtpip db")
    conn = psycopg2.connect( "dbname='%s' user='%s' host='%s' password='%s'" %(parser.get("db","name"),parser.get("db","user"),parser.get("db","host"),parser.get("db","pass")))    
    cur = conn.cursor()
    try:
        other_info = ''
        query = "INSERT INTO data_ingestion_collectiontable(name, source, max_lat, max_lon, min_lat, min_lon, start_date,end_date,application,"+\
                "location,other_info,status, \"IO\", \"coverageID\",measurement_unit,access,ipr,max_value,min_value) VALUES "
        query = "%s ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (query,dict_coll['outputCollectionName'],dict_coll['source'],dict_coll['max_lat'],dict_coll['max_lon'],dict_coll['min_lat'],dict_coll['min_lon'],dict_coll['start_date'],dict_coll['end_date'],dict_coll['application'],remote_path,other_info,'processed','O','',dict_coll['measurement_unit'],dict_coll['access'],dict_coll['ipr'],dict_coll['max_value'],dict_coll['min_value'])
        logging.debug("uploadcollection insert query:  %s" %(query))
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
        logging.info("uploadcollection done!")
    except Exception as e:
        logging.error("Error to insert coverage on data_ingestion_collectiontable")
        logging.debug(str(e))
    return

if __name__ == "__main__":

    ini_parser = __load_conf()

    #set logger
    logging.basicConfig(
     #stream= sys.stdout,
     filename=installation_dir+"/../log/tampProcessingUtilities.log",
     level= int(ini_parser.get("Logger","loglevel")),
     format='%(levelname)s\t| %(asctime)s | %(message)s'
    )

    parser = argparse.ArgumentParser(prog=sys.argv[0],description='Utility used to provide results "on-the-fly" from wcs data',epilog='SISTEMA GmbH  <http://www.sistema.at>')
    parser_function = parser.add_argument_group('Required function')
    parser_function.add_argument(dest='function',metavar='FUNCTION',choices=['spatialAverage','temporalAverage','conversion','add','subtract','uploadcollection','downloadcollection'],help='Available functions are: spatialAverage, temporalAverage, conversion, add, subtract,uploadcollection,downloadcollection')
    
    parser_coverage = parser.add_argument_group('Coverage required options')
    parser_coverage.add_argument('-c',dest='coverage',default=None,help='CoverageID to search in wcs server')    
    parser_coverage.add_argument('-o',dest='second_coverage',default=None,help='Second coverageID to search in wcs server, used in band combination function (add, subtract)')
    #parser_coverage.add_argument('-g',dest='ground_product',default=None,help='Ground product to search in DB, used in correlation function')
    parser_coverage.add_argument('-u',dest='ur_lat',default=None,type=float,help='Upper latitude')
    parser_coverage.add_argument('-d',dest='ll_lat',default=None,type=float,help='Lower latitude')
    parser_coverage.add_argument('-l',dest='ll_lon',default=None,type=float,help='Far west latitude')
    parser_coverage.add_argument('-r',dest='ur_lon',default=None,type=float,help='Far east latitude')
    parser_coverage.add_argument('-s',dest='t_s',default=None,type=int,help='Start time/date expressed in Unix Timestamp')
    parser_coverage.add_argument('-e',dest='t_e',default=None,type=int,help='End time/date expressed in Unix Timestamp')
    
    parser_convert = parser.add_argument_group('Function \'convert\' optional arguments. (Result = (coverage_ID+offset)*gain)')
    parser_convert.add_argument('--gain',metavar='val',type=float,default=1,help='Apply the gain in conversion function, default 1')
    parser_convert.add_argument('--offset',metavar='val',type=float,default=0,help='Apply the offset in conversion function, default 0')
    
    parser_downloadcollection = parser.add_argument_group('Function \'downloadcollection\' and \'uploadcollection\' arguments.')   
    #parser_downloadcollection.add_argument('--destination',dest='destination',metavar='path', help='valid path where collection will be downloaded')
    parser_downloadcollection.add_argument('--conf',dest='conf',metavar='conf_file', help='collection configuration file')

    parser_uploadcollection = parser.add_argument_group('Function \'uploadcollection\' arguments.')
    parser_uploadcollection.add_argument('--source',dest='source',metavar='path', help='valid path of folder that contains tiff and ')
    #parser_uploadcollection.add_argument('-u',dest='measurement_unit',metavar='value', help='measurement unit for new collection')
    #parser_uploadcollection.add_argument('--min',dest='min',metavar='value',type=float, help='min for new collection')
    #parser_uploadcollection.add_argument('--max',dest='max',metavar='value',type=float, help='max for new collection')
    #parser_uploadcollection.add_argument('--collectionname',dest='collectionname',metavar='value', help='collectionName for new collection')
    #parser_uploadcollection.add_argument('--applicationfield',dest='applicationfield',metavar='value', help='applicationField for new collection')  
    #parser_uploadcollection.add_argument('--collectionSource',dest='collectionSource',metavar='value', help='collectionSource for new collection')
    
    args = parser.parse_args()
    
    #data1,c1 = __get_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
    #data2,c2 = __get_data(args.second_coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
    data1,c1 = None, None
    data2,c2 = None, None

    try:   
        if 'spatialAverage' ==  args.function:
            data1,c1 = __get_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            if data1 is not None:
                print TampData.spatial_average(data1)      
            else:
                logging.warning('WCS returns no data')

        elif 'temporalAverage' == args.function:
            data1,c1 = __get_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            if data1 is not None:
                print TampData.temporal_average(data1)
            else:
                logging.warning('WCS returns no data')

        elif 'conversion' ==  args.function: 
            data1,c1 = __get_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            if all( x is not None for x in [data1,args.offset,args.gain]):
                print TampData.unit_conversion(data1,args.offset,args.gain)
            else: 
                logging.warning('WCS returns no data or offset/gain are not setted')

        elif 'add' ==  args.function:
            data1,c1 = __get_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            data2,c2 = __get_data(args.second_coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            if all( x is not None for x in [data1,data2]):
                print TampData.add(data1, data2, args.ur_lat,args.ll_lon,args.ll_lat,args.ur_lon)
            else:
                logging.warning('WCS returns no data')
  
        elif 'subtract' == args.function:
            data1,c1 = __get_data(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            data2,c2 = __get_data(args.second_coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e)
            if all( x is not None for x in [data1,data2]):
                print TampData.subtract(data1, data2, args.ur_lat,args.ll_lon,args.ll_lat,args.ur_lon)
            else:
                logging.warning('WCS returns no data')
                
        elif 'downloadcollection' == args.function:
            #if all( x is not None for x in [args.coverage,args.ur_lat,args.ll_lon,args.ll_lat,args.ur_lon,args.t_s,args.t_e,args.destination ]):
            #    print downloadcollection(args.coverage,args.ur_lat,args.ll_lat,args.ll_lon,args.ur_lon,args.t_s,args.t_e,args.destination)
            if all( x is not None for x in [args.conf]):
                print downloadcollection(args.conf)
            else:
                logging.warning('Missing collection configuration file') 
        elif 'uploadcollection' == args.function:
            if all( x is not None for x in [args.conf,args.source]): 
                uploadcollection(args.conf,args.source) 
            else:
                logging.warning('Missing argument') 
    except Exception as e:
        logging.error('Unexpected error ')
        logging.error(str(e))
        raise 
    #cleaning FS
    try:
        if c1 is not None: 
            c1.clean() 
            c1 = None
        if c2 is not None:       
            c2.clean() 
            c2 = None
        if data1 is not None:
            data1 = None   
        if data2 is not None:
            data2 = None       
    except:
        raise
        logging.error('Unexpected error in clean procedure')
        sys.exit(4) 
        

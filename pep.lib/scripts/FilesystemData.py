#!/usr/bin/env python

# TAMP-Project:    pep.lib
# Version:         0.02
# Date:            2016-02-11
# Description:     This library groups functionality used to reprocess entire collection
# Author:          Moris Pozzati
#
# ChangeLog:       2016-05-31
#                  added argparse
#                    
#                  2016-07-08
#                  fixed issues 
#                  

import os,sys,getopt,fnmatch
import psycopg2
import gdal
from gdalconst import *
import numpy as np
from numpy import ma 
import logging
import argparse
from ConfigParser import SafeConfigParser
import parser 

installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

# function implemented to create 2D WRFCHEM from 3D WRFCHEM
def twodize(input_file_list,outputdir,label = '2D'):
    its_ok = False
    logging.info('Apply 2Dize')
    for filename in input_file_list:
        try:
            #build new filename 
            new_filename = outputdir+'/'+os.path.basename(filename)[:-19]+label+'_'+os.path.basename(filename)[-19:]
            logging.debug("INPUT: %s" %(filename))
            logging.debug("OUTPUT %s" %(new_filename))
            #processing all tiff
            dataset = gdal.Open( filename, GA_ReadOnly )
            driver = gdal.GetDriverByName( 'GTiff' )
            if dataset is not None:
                data_ds = driver.Create(new_filename, dataset.RasterXSize , dataset.RasterYSize, 1, dataset.GetRasterBand(1).DataType)
                data_ds.SetGeoTransform(dataset.GetGeoTransform())
                data_ds.SetProjection(dataset.GetProjection())
                metadata = dataset.GetMetadata()
                if 'VERTICAL_LEVELS' in metadata:
                    del metadata['VERTICAL_LEVELS']
                if 'VERTICAL_LEVELS_NUMBER' in metadata:
                    del metadata['VERTICAL_LEVELS_NUMBER']
                data_ds.SetMetadata(metadata)
                metadata = dataset.GetMetadata()
                level = np.concatenate((np.array([0]),[float(i) for i in metadata['VERTICAL_LEVELS'].split(',')]))
                band = dataset.GetRasterBand(1)
                no_value = band.GetNoDataValue()
                data = ma.masked_equal(band.ReadAsArray(),no_value)
                data = data[:, :]*level[1]
                for i in range(dataset.RasterCount-1):
                    band = dataset.GetRasterBand(i+2)
                    data_tmp = ma.masked_equal(band.ReadAsArray(),no_value)
                    data = data + data_tmp[:, :]*(level[i+2]-level[i+1])
                #data = data / (10000000*2.69*1.06) 
                data = ma.masked_equal(data,no_value)
                #update metadata max and min
                maxValue = np.max(ma.masked_equal(data,-9999))
                minValue = np.min(ma.masked_equal(data,-9999))
                data_ds.SetMetadataItem('GLOBAL_MAX', str(maxValue))
                data_ds.SetMetadataItem('GLOBAL_MIN', str(minValue))
                #writhe band on geotiff
                data_ds.GetRasterBand(1).SetNoDataValue(no_value)
                data_ds.GetRasterBand(1).WriteArray(data)
                band = None
                data_ds = None
                dataset = None 
                its_ok = True
        except:
            logging.error("Error Processing: %s" %(filename))
            pass
    if not its_ok:
        logging.error("Error Processing ALL File: %s" %(filename))
        raise Exception('Error','Nothing processed')


# function implemented for generic unit conversion
def convert(input_file_list,outputdir,label='CONVERTED',gain=1,offset=1):
    its_ok = False
    logging.info('Apply convert')
    for filename in input_file_list:
        try:
            #build new filename 
            new_filename = outputdir+'/'+os.path.basename(filename)[:-19]+label+'_'+os.path.basename(filename)[-19:]
            logging.debug("INPUT: %s" %(filename))
            logging.debug("OUTPUT %s" %(new_filename))
            #processing all tiff
            dataset = gdal.Open( filename, GA_ReadOnly )
            driver = gdal.GetDriverByName( 'GTiff' )
            if dataset is not None:
                maxValue,minValue = None, None
                data_ds = driver.Create(new_filename, dataset.RasterXSize , dataset.RasterYSize, dataset.RasterCount, dataset.GetRasterBand(1).DataType)
                data_ds.SetGeoTransform(dataset.GetGeoTransform())
                data_ds.SetProjection(dataset.GetProjection())
                metadata = dataset.GetMetadata()
                data_ds.SetMetadata(metadata)
                metadata = dataset.GetMetadata()
                for i in range(dataset.RasterCount):
                    band = dataset.GetRasterBand(i+1)
                    no_value = band.GetNoDataValue()
                    data_tmp = ma.masked_equal(band.ReadAsArray(),no_value)
                    maxValue = max(maxValue,np.max(ma.masked_equal(data_tmp,-9999)))
                    minValue = min(minValue,np.min(ma.masked_equal(data_tmp,-9999)))
                    data = (data_tmp+offset)*gain
                    data_ds.GetRasterBand(i+1).WriteArray(data)
                    data_ds.GetRasterBand(i+1).SetNoDataValue(no_value)
                    band = None
                data_ds.SetMetadataItem('GLOBAL_MAX', str(maxValue))
                data_ds.SetMetadataItem('GLOBAL_MIN', str(minValue))
                data_ds = None
            dataset = None 
            its_ok = True
        except:
            logging.error("Error Processing: %s" %(filename))
            pass
    if not its_ok:
        logging.error("Error Processing ALL File: %s" %(filename))
        raise Exception('Error','Nothing processed')


# function implemented to add in DB new colection created from existing collection
# Used for DAS.ING ingester.py 
# call this function to create new row whit reprocessing status
# other_info is a string in this format:
# "function=name_function;label=label_val;param1=0;...;paramN=foo;"
def add_coverage(coverage_ID,new_name,measurement_unit,other_info):
    installation_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    #LOAD CONFIGURATION
    try:
        parser = SafeConfigParser()
        parser.read("%s/../etc/pep_lib.ini" % installation_dir)
    except:
        logging.error("I am unable to load configuration")
        loging.debug(str(e))
        return
    try:
        new_dict = dict(e.split('=') for e in other_info.split(';'))
        new_dict['function']
        new_dict['label']
    except:
        logging.error("other_info param is not a string in a valid format")

    conn = psycopg2.connect( "dbname='%s' user='%s' host='%s' password='%s'" %(parser.get("db","name"),parser.get("db","user"),parser.get("db","host"),parser.get("db","pass")))    
    cur = conn.cursor()
    query = "SELECT * from data_ingestion_collectiontable where \"coverageID\" like '%s'" %(coverage_ID)
    logging.debug("add_coverage select query:  %s" %(query))
    cur.execute( query )
    data = cur.fetchall()
    try:
        val = ['' if v is None else v for v in data[0]]
        query = "INSERT INTO data_ingestion_collectiontable(name, source, max_lat, max_lon, min_lat, min_lon, start_date,end_date,application,"+\
                "\"group\", location,other_info,uploaded_by_id,status, \"IO\", \"coverageID\",measurement_unit,access,ipr,max_value,min_value) VALUES "
        query = "%s ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%s,'%s','%s','%s','%s','%s','%s','%s','%s')" % (query,new_name,val[2],val[3],val[4],val[5],val[6],val[7],val[8],val[9],val[10],val[11],other_info,val[13],'reprocess','O',val[16],measurement_unit,val[18],val[19],val[20],val[21])
        logging.debug("add_coverage insert query:  %s" %(query))
        cur.execute(query)
        conn.commit()
    except Exception as e:
        raise
        logging.error("Error to insert coverage on data_ingestion_collectiontable")
        logging.debug(str(e))
    cur.close()
    conn.close()

# wrap function used to choose reprocesing function
# dict_args is a dictionary, pass  the entries used by required function 
def reprocessing(inputdir,outputdir,dict_args = None , product_id = None):
    #newRef=os.fork()
    #if newRef != 0:
    #    logging.info('New process started with pid '+str(newRef))
    #    return  
    #logging.debug('Child process starting')
    #check input param
    if not (dict_args and type( dict_args ) == dict):
        logging.error('No dict_args passed. Impossible to define function,label and params')
        raise Exception('Error','No dict_args passed') 
    if inputdir is None or not os.path.exists(inputdir):
        logging.error("Reprocessing: Invalid inputdir") 
        raise Exception('Error','Invalid inputdir')
    #create outputDir
    if not os.path.exists(outputdir):
        logging.debug('creating %s' %outputdir)
        try:
            os.makedirs(outputdir)
        except:
            logging.error("Reprocessing: Impossible to make outputdir")
            raise
    #search tif in inputDir
    matches = []
    for root, dirnames, filenames in os.walk(inputdir):
        for filename in fnmatch.filter(filenames, '*.tif'):
            matches.append(os.path.join(root, filename))
    if product_id:
        label = dict_args['label']+'_'+str(product_id)
    else:
        label = dict_args['label']
            
    #processing
    if dict_args['function'] == 'verticalIntegration':
        twodize(matches,outputdir,label)
    elif dict_args['function'] == 'convert':
        convert(matches,outputdir,label,float(dict_args['gain']),float(dict_args['offset']))
    else:
        logging.error("Reprocessing: Unrecognized function")
        raise Exception('Error','Unrecognized function')

if __name__ == "__main__":
    #LOAD CONFIGURATION
    try:
        parser = SafeConfigParser()
        parser.read("%s/../etc/pep_lib.ini" % installation_dir)
        #set logger
        logging.basicConfig(
         #stream= sys.stdout,
         filename=installation_dir+"/../log/FilesystemData.log",
         level= int(parser.get("Logger","loglevel")),
         format='%(levelname)s\t| %(asctime)s | %(message)s'
        )
    except Exception as e:
        print "I am unable to load configuration"
        print str(e)

    parser = argparse.ArgumentParser(prog=sys.argv[0],description='Utility used to reprocess entire collections on filesystem',epilog='SISTEMA GmbH  <http://sistema.at>')
    parser.add_argument('--standalone',help='Execute the module stand-alone, without going through ingester in das_ing',action='store_true')
    
    parser_required = parser.add_argument_group('Required Arguments')
    parser_required.add_argument('-f',dest='function',metavar='func',required=True, choices=['verticalIntegration', 'convert'], help='available functions are: verticalIntegration, convert')
    parser_required.add_argument('-l',dest='label',metavar='label',required=True, help='new label to attach to new filename')

    parser_ingester = parser.add_argument_group('Required Arguments if NOT executed stand-alone')
    parser_ingester.add_argument('-c',dest='coverage_ID',metavar='coverage',help='Coverage_ID in data_ingestion_collectiontable')
    parser_ingester.add_argument('-n',dest='new_name',metavar='name',help='New name for data_ingestion_collectiontable')
    parser_ingester.add_argument('-u',dest='measurement_unit',metavar='value', help='measurement unit for new collection')


    parser_standalone = parser.add_argument_group('Required Arguments if executed stand-alone')
    parser_standalone.add_argument('-i',dest='inputdir',metavar='dir',help='directory where search tif recoursively')    
    parser_standalone.add_argument('-o',dest='outputdir',metavar='dir',help='directory where put results, Created if not exists')
 
    parser_standalone_convert = parser.add_argument_group('function \'convert\' optional arguments (Result = (coverage_ID+offset)*gain) ')
    parser_standalone_convert.add_argument('--gain',metavar='val',type = float,default='1',help='apply the gain in conversion function, default 1')
    parser_standalone_convert.add_argument('--offset',metavar='val',default='0',type = float,help='apply the offset in conversion function, default 0')
   
    args = parser.parse_args()
    #logging.debug(args)
    if args.standalone:
        reprocessing(args.inputdir,args.outputdir,vars(args))
    else:
        other_info="function="+args.function+";label="+args.label+";gain="+str(args.gain)+";offset="+str(args.offset)
        add_coverage(args.coverage_ID,args.new_name,args.measurement_unit,other_info)



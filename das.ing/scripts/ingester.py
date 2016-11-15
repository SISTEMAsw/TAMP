#!/usr/bin/env python

# TAMP-Project:    ingester.py
# Version:         0.01
# Date:            2016-01-12
# Description:
# Author:          Moris Pozzati
#
# ChangeLog:
# 
#

import sys, time, io, os 
import logging
import psycopg2
import paramiko
import shutil
import subprocess
import zipfile
import re
from ConfigParser import SafeConfigParser
from zipfile import BadZipfile
import glob

#IMPORT MODULE IN LIB
#installation_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("%s/../lib" % installation_dir)
sys.path.append("%s/../../pep.lib/proc" % installation_dir)
sys.path.append("%s/../../pep.lib/scripts" % installation_dir)


import FilesystemData
from daemon import Daemon
from fileIdentifier import identifyFile
from ground2db import ground2db
from procAERONET import extractAERONETData
from procEVDC import extractEVDCData
from procEEA import extractEEAData
from procALARO import createImgALARO
from procAROME import createImgAROME
from procAURA_L2 import createImgAURA_L2_SO2
from procAURA_L2 import createImgAURA_L2_AEROSOL
from procAURA_L3 import createImgAURA_L3
from procBASCOE import createImgBASCOE
from procCAMS import createImgCAMS
from procCloudsat import createImgCloudsat
from procFLEXPART import createImgFLEXPART
from procGOME_L2 import createImgGOME_L2
from procBIRA_AK_OMI_GOME2 import createImgBIRA_AK_OMI_GOME2
from procLIDAR import createImgLIDAR_Backscatter
from procLIDAR import createImgLIDAR_Extinction
from procLIDAR_Bira import createImgLIDAR_Bira
from procMACC import createImgMACC
from procMODL2_MOD04 import createImgMOD04
from procMODL2_MOD07 import createImgMODIS
from procOSIRIS_L2 import createImgOSIRIS
from procPARASOL_Land import createImgPARASOL_Land
from procPARASOL_Sea import createImgPARASOL_Sea
from procSENTINEL_L2 import createImgSENTINEL_L2
from procSCISAT import createImgSCISAT
from procWRFCHEM import createImgWRFCHEM_SO2
from procWRFCHEM import createImgWRFCHEM_ASH3D
from procWRFCHEM import createImgWRFCHEM_ASHCOL

parser = None
log = None
conn = None
cur = None


def initialization():
    global parser
    global log
    global conn
    global cur

    #LOAD CONFIGURATION
    try:
        parser = SafeConfigParser()
        parser.read("%s/../etc/das_ing.ini" % installation_dir)
    except Exception as e:
        log.error("I am unable to load configuration")
        log.debug(str(e))
        raise
    
    #SET LOGGER
    log_level = 20 
    log_level = int(parser.get("Logger","loglevel"))
    logging.basicConfig(
     # to mantain this order for python 2.6
     #stream= sys.stdout,
     filename=installation_dir+"/../log/das_ing.log",
     level= log_level,
     format='%(levelname)s\t| %(asctime)s | %(message)s'
    )
    log = logging.getLogger(__name__)
    
    #INITIALIZE DB CONNECTION
    try:
        conn = psycopg2.connect( "dbname='%s' user='%s' host='%s' password='%s'" %(parser.get("db","name"),parser.get("db","user"),parser.get("db","host"),parser.get("db","pass")))
        cur  = conn.cursor()
        log.debug("DB connection OK")
    except Exception as e:
        log.error("I am unable to connect to the database")
        log.debug(str(e))
        raise

def db_check_new_product(status,retrieved_field='location'):
    try:
        query="select id,\"%s\" from data_ingestion_collectiontable where status = '%s'" % (retrieved_field,status)
        cur.execute( query )
        data = cur.fetchall()
        product_id = data[0][0]
        field = data[0][1]
    except Exception as e:
        #log.debug(str(e))
        return None, None
    log.info("Find %s to manage. id: %s , %s: %s" %(field,product_id,retrieved_field,field))
    return product_id,field

def find_other_info(product_id):
    query="select other_info from data_ingestion_collectiontable where id = %s" % (product_id)
    cur.execute( query )
    data = cur.fetchall()
    return dict(e.split('=') for e in data[0][0].split(';'))

def download_product(product_location,product_basename):
    log.info("Download product from vtpip server")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(parser.get("vtpip","host"), username=parser.get("vtpip","user"), password=parser.get("vtpip","pass"))
    sftp = ssh.open_sftp()
    product_local = "%s/%s" %(parser.get("Common","inData"),product_basename)
    log.debug("Remote Path: %s/%s\nLocal Path: %s" %(parser.get("vtpip","location"),product_location,product_local))
    sftp.get("%s/%s" %(parser.get("vtpip","location"),product_location) ,product_local)
    sftp.close()
    ssh.close()
    log.info("Product downloaded")
    log.debug("location: %s" %(product_local))
    return product_local

def remove_remote_product(product_location):
    log.info("Remove product from vtpip server")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(parser.get("vtpip","host"), username=parser.get("vtpip","user"), password=parser.get("vtpip","pass"))
    sftp = ssh.open_sftp()
    log.debug("%s/%s" %(parser.get("vtpip","location"),product_location))
    sftp.remove("%s/%s" %(parser.get("vtpip","location"),product_location))
    sftp.close()
    ssh.close() 
    log.info("Product removed from vtpip")
    return


def db_change_product_status(product_id,status):
    try:
        query="Update data_ingestion_collectiontable set status = '%s' where id=%s" % (status,product_id)
        log.debug(query)
        cur.execute( query )
        conn.commit()
    except Exception as e:
        log.debug(str(e))
        log.error("Impossible to update product status")

def db_change_product_location(product_id,location):
    try:
        query="Update data_ingestion_collectiontable set location = '%s' where id=%s" % (location,product_id)
        log.debug(query)
        cur.execute( query )
        conn.commit()
    except Exception as e:
        log.debug(str(e))
        log.error("Impossible to update product location")

def db_change_product_coverage(product_id,coverage_id):
    try:
        query="Update data_ingestion_collectiontable set \"coverageID\" = '%s' where id=%s" % (coverage_id,product_id)
        log.debug(query)
        cur.execute( query )
        conn.commit()
    except Exception as e:
        log.debug(str(e))
        log.error("Impossible to update product coverage_id")

def db_update_name(product_id,name):
    try:
        query = "select name from data_ingestion_collectiontable where id=%s" % (product_id)
        cur.execute( query )
        data = cur.fetchall()
        current_name = data[0][0]
        query="Update data_ingestion_collectiontable set name  = '%s %s' where id=%s" % (current_name,name,product_id)
        log.debug(query)
        cur.execute( query )
        conn.commit()
    except Exception as e:
        log.debug(str(e))
        log.error("Impossible to update product name")

def db_insert_row(source_id,status,location,coverage_id ="\"coverageID\"",name= "name" ):
    try:
        query = "insert into data_ingestion_collectiontable"+\
                " (name,source,max_lat,max_lon,min_lat,min_lon,start_date,end_date,application,\"group\",location,"+\
                "other_info,uploaded_by_id,status,\"IO\",\"coverageID\",measurement_unit,access,ipr,max_value,min_value)"+\
                " (select "+name+",source,max_lat,max_lon,min_lat,min_lon,start_date,end_date,application,\"group\",'"+location+\
                "',other_info,uploaded_by_id,'"+status+"',\"IO\","+coverage_id+",measurement_unit,access,ipr,max_value,min_value"+\
                " from data_ingestion_collectiontable where id = "+ str(source_id)+")"
        log.debug(query)
        cur.execute( query )
        conn.commit()
    except Exception as e:
        log.debug(str(e))
        log.error("Impossible to create new row with location "+location+" from product id " +source_id )
   
def run_processing(product_id,product_local):
    
    log.info("Processing starts for %s" % product_local)
    inDataLocation = parser.get("Common", "inData")
    inBasketLocation = parser.get("Common", "inBasket")
    processLocation = parser.get("Common", "processDir")
    groundMeasureLocation = parser.get("Common", "groundMeasurements")
    
    #this part is for local testing
    """
    inBasketLocation = "/das-dave_data/inBasket/"
    processLocation = "/tmp/"
    groundMeasureLocation = '/das-dave_data/groundMeasurements/'
    """
    
    savedPath = os.getcwd()    
    tmpDir = processLocation + '/TAMP_tmp/'
        
    if not os.path.isdir(tmpDir):
        os.mkdir(tmpDir)    
    os.chdir(tmpDir)
    log.debug(tmpDir)
    outPath = ''
    outPath_list = []
    omit_FLEXPART_files = []
    try:
        with zipfile.ZipFile(product_local, 'r') as zip:
            zip.extractall()
            product_local = zip.namelist()
     
            #omit the files attached to FLEXPART, just need the directory           
            regex_FLEXPART = re.compile('(.*dates)|(.*header)|(.*receptor_conc)|(.*grid_conc_[0123456789]{14}_[0123456789]{3})')
            omit_FLEXPART_files = [m.group(0) for l in zip.namelist() for m in [regex_FLEXPART.search(l)] if m]    
    except BadZipfile:
        product_local = [product_local]
     
    product_local = [file for file in product_local if not os.path.isdir(file)]
     
    regex_PARASOL_data = re.compile('.*P[123]L[123]T[BRLO]G[1ABC][0123456789]{3}[0123456789]{3}[A-Z]D')
    for i in product_local:    
        inFile = open(i)
        inFile.seek(36)
        PARASOL_filename = inFile.read(16)
        inFile.close()
        if regex_PARASOL_data.match(i):
            PARASOL_leader_filename = i[:-1] + 'L' 
            try:
                product_local.remove(PARASOL_leader_filename)
            except Exception as e:
                pass
     
    if omit_FLEXPART_files:
        product_local = [os.path.dirname(os.path.abspath(omit_FLEXPART_files[0]))]

    for i in product_local:
        try:
            i = os.path.abspath(i)
            fileType = identifyFile(i)
    
            if fileType == 'AERONET':
                file_list = extractAERONETData(i)
            elif fileType == 'EVDC':
                file_list = extractEVDCData(i)
            elif fileType == 'EEA':
                file_list = extractEEAData(i)
            elif fileType == 'ALARO':
                file_list = createImgALARO(i)
            elif fileType == 'AROME':
                file_list = createImgAROME(i)
            elif fileType == 'AURA_L2_AEROSOL':
                file_list = createImgAURA_L2_AEROSOL(i)
            elif fileType == 'AURA_L2_SO2':
                file_list = createImgAURA_L2_SO2(i)
            elif fileType == 'AURA_L3':
                file_list = createImgAURA_L3(i)
            elif fileType == 'BASCOE':
                file_list = createImgBASCOE(i)
            elif fileType == 'CAMS':
                file_list = createImgCAMS(i)
            elif fileType == 'CLOUDSAT':
                file_list = createImgCloudsat(i)
            elif fileType == 'FLEXPART':
                file_list = createImgFLEXPART(i)
            elif fileType == 'GOME_L2':
                file_list = createImgGOME_L2(i)
            elif fileType == 'BIRA_AK_OMI_GOME2':
                file_list = createImgBIRA_AK_OMI_GOME2(i)
            elif fileType == 'LIDAR_BACKSCATTER':
                file_list = createImgLIDAR_Backscatter(i)
                os.remove(i)
            elif fileType == 'LIDAR_EXTINCTION':
                file_list = createImgLIDAR_Extinction(i)
                os.remove(i)
            elif fileType == 'LIDAR_BIRA':
                file_list = createImgLIDAR_Bira(i)
            elif fileType == 'MACC':
                file_list = createImgMACC(i)
            elif fileType == 'MOD04':
                file_list = createImgMOD04(i)
            elif fileType == 'MOD07':
                file_list = createImgMODIS(i)
            elif fileType == 'OSIRIS_L2':
                file_list = createImgOSIRIS(i)
            elif fileType == 'PARASOL_LAND':
                file_list = createImgPARASOL_Land(i)
            elif fileType == 'PARASOL_SEA':
                file_list = createImgPARASOL_Sea(i)
            elif fileType == 'SENTINEL_L2':
                file_list = createImgSENTINEL_L2(i)
            elif fileType == 'SCISAT_L2':
                file_list = createImgSCISAT(i)
            elif fileType == 'WRFCHEM_SO2':
                file_list = createImgWRFCHEM_SO2(i)
            elif fileType == 'WRFCHEM_ASH3D':
                file_list = createImgWRFCHEM_ASH3D(i)
            elif fileType == 'WRFCHEM_ASHCOL':
                file_list = createImgWRFCHEM_ASHCOL(i)
            else:
                log.error('Not valid processor found for: %s' %i)
                #db_change_product_status(product_id,'Error_Processor_not_found')
                continue
        
            if file_list:
                #input files are MOD07
                if type(file_list) is dict:
                    for key in file_list:
                        outPath = inBasketLocation + '/' + fileType + '_' +key + '/'
                        if not os.path.exists(outPath):
                            log.debug('mkdir '+outPathXML)
                            os.mkdir(outPath)       
                        tifFile = file_list[key]
                        log.debug('mv '+tmpDir + tifFile+' '+outPath + tifFile)
                        shutil.move(tmpDir + tifFile, outPath + tifFile)
                        
                elif type(file_list) is list:
                    # product whit TIF and XML (LIDAR_EXTINCTION)          
                    if fileType == 'LIDAR_EXTINCTION':
                        tifFile = file_list[0]
                        outPath= inBasketLocation + '/' + fileType + '/'
                        if not os.path.exists(outPath):
                            log.debug('mkdir '+outPath)
                            os.mkdir(outPath)
                        log.debug('mv '+tmpDir + tifFile+' '+outPath + tifFile)
                        shutil.move(tmpDir + tifFile, outPath + tifFile)
                        xmlFile = file_list[1]
                        outPathXML = groundMeasureLocation + '/' + fileType + '/'
                        if not os.path.exists(outPathXML):
                            log.debug('mkdir '+outPathXML)
                            os.mkdir(outPathXML)
                        log.debug('mv '+tmpDir + xmlFile+' '+outPath + xmlFile)
                        shutil.move(tmpDir + xmlFile, outPathXML + xmlFile)
                        outPath_list.append(outPathXML)

                    # product with TIF OR XML
                    else:
                        if fileType == 'AERONET' or fileType == 'EVDC' or fileType == 'GROUND_SO2' or fileType == 'EEA':
                            #XML (AERONET,EVDC,GROUND_SO2,EEA)
                            outPath = groundMeasureLocation + '/' + fileType + '/'
                        else:
                            #TIFF (OTHER)
                            outPath = inBasketLocation + '/' + fileType + '/'
                        # TIF XML common parts
                        if not os.path.exists(outPath):
                            log.debug('mkdir '+outPath)
                            os.mkdir(outPath)
                        for unkFile in file_list:
                            log.debug('mv '+tmpDir + unkFile+' '+outPath + unkFile)
                            shutil.move(tmpDir + unkFile, outPath + unkFile) 
                log.debug('check if append '+outPath+' to outputPath_list')
                if outPath not in outPath_list:
                    log.debug('append '+outPath+' to outputPath_list')
                    outPath_list.append(outPath) 
        except Exception as e:
            log.error('Error Processing: %s' %i)
            log.error(str(e))
            pass
    #preparing list or output dir processed. tif in 'processing' status, groundmeasurement in 'Available'
    p = [(x,'p') for x in list(set(outPath_list)) if not x.startswith(groundMeasureLocation)]   
    gm = [(x,'gm') for x in list(set(outPath_list)) if x.startswith(groundMeasureLocation)]
    s = p+gm
    if len(s) == 0:
        db_change_product_status(product_id,'Error_Processor_not_found')
    while len(s) > 1:
        #if a sigle dataset produces multiple folder, rows added in db
        product  = s.pop()
        if product[1] == 'gm':
            try:
                for xml_file in glob.glob(product[0]+"*.xml"):           
                    log.debug(xml_file) 
                    ground2db(xml_file)
                status = 'Available'
                db_insert_row(product_id,status,product[0],coverage_id="concat(name,'_ground_measurements')")
            except Exception as e:
                log.error('Error during ground2db')
                log.error(str(e))
                db_insert_row(product_id,'Processing_Error',product[0])
        else:
            status = 'processed'
            db_insert_row(product_id,status,product[0])
    if len(s) == 1:
        product  = s.pop()
        if product[1] == 'gm':
            try:
                for xml_file in glob.glob(product[0]+"*.xml"):            
                    log.debug(xml_file)
                    ground2db(xml_file)
                status = 'Available'
                db_change_product_coverage(product_id,"concat(name,'_ground_measurements')")
            except Exception as e:
                log.error('Error during ground2db')
                log.error(str(e))
                db_change_product_status(product_id,'Processing_Error')
        else:
            status = 'processed'
        db_change_product_status(product_id,status)
        db_change_product_location(product_id,product[0])
    log.info("Processing ends for %s" % product_local)

def run_mwcs(product_location,product_id):
    log.info('Start mwcs ingestion for product %s' % product_location )  
    coverage_id = 'ERROR'
    loader = parser.get("Loader", "loader")
    std_out = subprocess.check_output(['python',loader,'-m','-d',product_location,'-p','*.tif'])
    coverage_id_list = [] 
    res = []
    mwcs_dir = os.path.normpath(parser.get("Common", "mwcs"))+'/'
    for line in std_out.split('\n'): 
        if '[ OK ]' in line:
            log.debug(line.split())
            coverage_id_list.append(line.split()[-1])
    multiple= (True if len(coverage_id_list) >1 else False)
    while len(coverage_id_list) > 1:
        #if a sigle collection produces multiple coverage, rows added in db
        coverage_id = coverage_id_list.pop()
        db_insert_row(product_id,'mwcs_processed',mwcs_dir+"_".join(coverage_id.split("_")[:-2]),"'"+coverage_id+"'",name = "concat(name,' ','"+"_".join(coverage_id.split("_")[:-2])+"')")
        #db_update_name(product_id,"_".join(coverage_id.split("_")[:-2]))
    if len(coverage_id_list) == 1:
        coverage_id = coverage_id_list.pop()
        db_change_product_status(product_id,'mwcs_processed')
        db_change_product_location(product_id,mwcs_dir+"_".join(coverage_id.split("_")[:-2]))
        #db_change_product_coverage(product_id,"'"+coverage_id+"'"
        db_change_product_coverage(product_id,coverage_id)
        if multiple:
            db_update_name(product_id,"_".join(coverage_id.split("_")[:-2]))
    log.info('mwcs successfully performed for %s' % product_location)   

def dave_sync(product_id,product_location): #product_basename,mwcs_dir,mwcs_list):
    log.info('Start Dave Sync for product %s' % product_location )
    command_line_process = subprocess.Popen(
        ["sh",installation_dir+"/sync_collection.sh",product_location, os.path.basename(product_location)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    log.debug(str(command_line_process))
    log.debug("Start communicate")
    process_output, process_error =  command_line_process.communicate()
    log.debug("End communicate")
    log.debug("Exit Code:  " +str(command_line_process.returncode))
    for line in process_output.split('\n'):
        log.debug(line)
    if len(process_error.split('\n')) > 1:
        #ignoring error if try insert a collection that already exists.
        if re.match(r'ERROR: The name (.*) is already used by another range type! Import of range type #1 aborted!',process_error.split('\n')[0]) and\
           re.match(r'CommandError: The identifier (.*) is already in use.',process_error.split('\n')[1]):
            pass
        else:
            for line in process_error.split('\n'):
                log.error(line)
            return False
    db_change_product_status(product_id,'Available')
    log.info('Syncronization successfully performed for %s' % product_location)
    return True

    
def run_error(product_location):
    if os.path.isfile(product_location):
        log.info("Move %s to %s" %(product_location,parser.get("Common","errorBasket")))
        shutil.move(product_location,parser.get("Common","errorBasket")+"/"+os.path.basename(product_location))
    
def run_remove(product_location):
    try:
        log.info("Remove %s " %(product_location))
        os.remove(product_location)
    except Exception as e:
        log.debug(str(e))
        log.error("Impossible to remove %s" %(product_location))
    
class MyDaemon(Daemon):
    def run(self):
        initialization()
        log.info('Start Ingester')
        mwcs_dir = parser.get("Common", "mwcs") 
        inBasketLocation = parser.get("Common", "inBasket")
        while True:
            
            #1st step (Case A): download a product from vt-pip and ingest it with corect processor
            product_id,product_remote_location = db_check_new_product('uploading')
            if product_remote_location is not None:
                product_basename = os.path.basename(product_remote_location)
                #Download
                try:
                    product_location = download_product(product_remote_location,product_basename)
                    remove_remote_product(product_remote_location)
                    if not os.path.isfile(product_location):
                        raise
                    db_change_product_location(product_id,product_location)    
                except Exception as e:
                    log.error('Error during download %s' %product_basename)
                    log.debug(str(e))
                    db_change_product_status(product_id,'Download_Error')
                    continue
                #Processing
                try:
                    db_change_product_status(product_id,'processing')
                    run_processing(product_id,product_location)
                except Exception as e:
                    #raise
                    log.error('Error during Processing for id %s in %s' %(product_id,product_location))
                    log.debug(str(e))
                    db_change_product_status(product_id,'Processing_Error')
                    run_error(product_basename)
                    continue
                #Remove downloaded product
                try:
                    run_remove(product_location)
                except Exception as e:
                    log.warning('Error during the removal of %s' %product_basename)
                    log.debug(str(e))
                    continue     
                               
            #1st step (Case B): process a product from existing collection (Using TAMP functionality)
            product_id,coverage_ID = db_check_new_product('reprocess','coverageID')
            if coverage_ID is not None:
                product_location = "%s/%s" %(mwcs_dir,'_'.join(coverage_ID.split('_')[:-2]))
                if os.path.isdir(product_location):
                    try:
                        outputdir = inBasketLocation+'/'+str(product_id)+'/'
                        FilesystemData.reprocessing(product_location,outputdir,find_other_info(product_id),product_id)
                        db_change_product_status(product_id,'processed')
                        db_change_product_location(product_id,outputdir)
                    except Exception as e:
                        log.error('Error during reprocessing for id %s in %s' %(product_id,product_location))
                        log.debug(str(e))
                        db_change_product_status(product_id,'Processing_Error')
                        
            #2nd step: run a processed collection on mwcs
            product_id,product_location = db_check_new_product('processed')                   
            if product_location is not None:
                try:
                    run_mwcs(product_location,product_id)
                except Exception as e:
                    log.error('Error during mwcs processing for id %s in %s' %(product_id,product_location))
                    log.debug(str(e))
                    db_change_product_status(product_id,'mwcs_Error')
                    continue
                    
            #3rd step: sync collection on DAVE
            product_id,product_location = db_check_new_product('mwcs_processed')                   
            if product_location is not None:
                if  not dave_sync(product_id,product_location):
                    log.error('Error during Syncronization for id %s in %s' %(product_id,product_location))
                    db_change_product_status(product_id,'Sync_Error')
                    continue       
                                 
            #4th step: waiting for new run
            time.sleep(int(parser.get("Common","interval")))

if __name__ == "__main__":
    daemon = MyDaemon("%s/../run/ingestion.pid" % installation_dir )

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'status' == sys.argv[1]:
            if daemon.status() == 0:
                sys.stdout.write('Not Running!\n')
            else:
                sys.stdout.write('Running!\n')
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)

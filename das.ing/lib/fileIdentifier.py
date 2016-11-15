#!/usr/bin/env python

import os, sys
import pygrib
import gdal
import h5py
import netCDF4
import re
import logging

from pyhdf.HDF import HDF
from pyhdf.SD import SD
from collections import OrderedDict

#set path to the FLEXPART library
flexpart_lib = os.path.dirname(os.path.realpath(__file__)) + '/../../pep.lib/lib/FLEXPART/'
sys.path.append(flexpart_lib)
import read_header as rh


def identifyFile(fileAbsPath):
    """Identifies, which filetype the given file is
    
    Args:
        fileAbsPath  absolute path the file
    Returns:
        type of the file, if the input file is a known filetype, None otherwise
    """
  
    fileTypes = (('AURA_L2_SO2', isAURA_L2_SO2), ('AURA_L2_AEROSOL', isAURA_L2_AEROSOL), ('AURA_L3', isAURA_L3), 
                 ('BIRA_AK_OMI_GOME2', isGOME2_BIRA_OMI), ('GOME_L2', isGOME_L2), ('LIDAR_EXTINCTION', isLIDAR_EXTINCTION),
                 ('LIDAR_BACKSCATTER', isLIDAR_BACKSCATTER), ('BASCOE', isBASCOE), ('WRFCHEM_SO2', isWRFCHEM_SO2),
                 ('CAMS', isCAMS), ('MACC', isMACC), ('WRFCHEM_ASH3D', isWRFCHEM_ASH3D), ('WRFCHEM_ASHCOL', isWRFCHEM_ASHCOL),
                 ('AERONET', isAERONET), ('CLOUDSAT', isCloudsat), ('EVDC', isEVDC), ('FLEXPART', isFLEXPART), ('MOD04', isMOD04),
                 ('MOD07', isMOD07), ('EEA', isEEA), ('LIDAR_BIRA', isLIDAR_BIRA), ('ALARO', isALARO), ('AROME', isAROME),
                 ('SENTINEL_L2',isSENTINEL_L2), ('PARASOL_LAND', isPARASOL_LAND), ('PARASOL_SEA', isPARASOL_SEA),
                 ('SCISAT_L2',isSCISAT_L2),('OSIRIS_L2',isOSIRIS_L2))
    fileTypes = OrderedDict(fileTypes)
    
    for fileType, function in fileTypes.iteritems():
        try:
            if function(fileAbsPath):
                return fileType
        except Exception as e:
            pass
    return None


def isAERONET(fileAbsPath):
    with open(fileAbsPath) as inFile:
        lines = inFile.read().split('\n')            
        preamble = lines[2].split(',')
                   
        identifierName = preamble[0].split('=')[0]
        identifierLong = preamble[1].split('=')[0]
        identifierLat = preamble[2].split('=')[0]
        indetifierElev = preamble[3].split('=')[0]
                
    if identifierName == 'Location' and identifierLong == 'long' and identifierLat == 'lat' and indetifierElev == 'elev':
        return True
    
    
def isALARO(fileAbsPath):
    filename = os.path.basename(fileAbsPath)
       
    if filename[0:5] == 'ALARO':
        with pygrib.open(fileAbsPath) as inFile:
            inFile.select(name='Specific humidity',typeOfLevel='isobaricInhPa')
            inFile.select(name='Temperature',typeOfLevel='isobaricInhPa')
            inFile.select(name='Temperature',typeOfLevel='surface')
            inFile.select(name='Surface pressure',typeOfLevel='surface')
        return True
    
    
def isAROME(fileAbsPath):
    filename = os.path.basename(fileAbsPath)    
    
    if filename[0:5] == 'AROME':
        with pygrib.open(fileAbsPath) as inFile:
            inFile.select(name='Specific humidity',typeOfLevel='isobaricInhPa')
            inFile.select(name='Temperature',typeOfLevel='isobaricInhPa')
            inFile.select(name='Temperature',typeOfLevel='surface')
            inFile.select(name='Surface pressure',typeOfLevel='surface')
        return True
    
    
def isAURA_L2_AEROSOL(fileAbsPath):
    with h5py.File(fileAbsPath, 'r') as inFile:    
        inFile['/HDFEOS/SWATHS/ColumnAmountAerosol/Geolocation Fields/Latitude'].attrs['MissingValue']
        inFile['/HDFEOS/SWATHS/ColumnAmountAerosol/Geolocation Fields/Longitude'].attrs['MissingValue']
        inFile['/HDFEOS/SWATHS/ColumnAmountAerosol/Geolocation Fields/Time']
        inFile['/HDFEOS/SWATHS/ColumnAmountAerosol/Data Fields/AerosolOpticalThicknessMW']
        dataAttributes = inFile['/HDFEOS/SWATHS/ColumnAmountAerosol/Data Fields/AerosolOpticalThicknessMW'].attrs
        attributes = inFile['/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES'].attrs
        attributes['InstrumentName']
        attributes['ProcessLevel']
        dataAttributes['_FillValue']
    return True

    
def isAURA_L2_SO2(fileAbsPath):
    with h5py.File(fileAbsPath, 'r') as inFile:
        inFile['/HDFEOS/SWATHS/OMI Total Column Amount SO2/Geolocation Fields/Latitude'].attrs['MissingValue']
        inFile['/HDFEOS/SWATHS/OMI Total Column Amount SO2/Geolocation Fields/Longitude'].attrs['MissingValue']
        inFile['/HDFEOS/SWATHS/OMI Total Column Amount SO2/Geolocation Fields/Time']
        inFile['/HDFEOS/SWATHS/OMI Total Column Amount SO2/Data Fields/SO2indexP1']
        dataAttributes = inFile['/HDFEOS/SWATHS/OMI Total Column Amount SO2/Data Fields/SO2indexP1'].attrs
        attributes = inFile['/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES'].attrs
        attributes['InstrumentName']
        attributes['ProcessLevel']
        dataAttributes['_FillValue']
    return True
    
    
def isAURA_L3(fileAbsPath):
    with h5py.File(fileAbsPath, 'r') as inFile:
        inFile['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/Latitude']
        inFile['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/Longitude']
        inFile['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/Time']
        inFile['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/ColumnAmountSO2_PBL']
        dataAttributes = inFile['/HDFEOS/GRIDS/OMI Total Column Amount SO2/Data Fields/ColumnAmountSO2_PBL'].attrs
        attributes = inFile['/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES'].attrs    
        attributes['InstrumentName']
        attributes['ProcessLevel']
        attributes['StartUTC']
        attributes['EndUTC']
        attributes['GranuleYear']
        attributes['GranuleMonth']
        attributes['GranuleDay']
        dataAttributes['_FillValue']
    return True


def isBASCOE(fileAbsPath):
    with netCDF4.Dataset(fileAbsPath, 'r') as inFile:
        inFile.variables['o3_vmr'][:]
        inFile.variables['ap'][:]
        inFile.variables['bp'][:]
        inFile.variables['p0'][:]
        inFile.variables['levelist'][:]
        inFile.variables['time'][:]
        inFile.variables['latitude'][:]
        inFile.variables['longitude'][:]
        inFile.variables['temperature'][:]
        inFile.variables['z'][:]
    return True


def isCAMS(fileAbsPath):
    with netCDF4.Dataset(fileAbsPath, 'r') as inFile:
        inFile.variables['so2_conc'][:]
        inFile.variables['latitude'][:]
        inFile.variables['longitude'][:]
        inFile.variables['time'][:]
    return True
    
    
def isCloudsat(fileAbsPath):
    with HDF(fileAbsPath) as hdf:
        vs = hdf.vstart()
            
        lat = vs.find('Latitude')
        lon = vs.find('Longitude')
        start = vs.find('start_time')
        end = vs.find('end_time')
        off = vs.find('Roll_offset.offset')
        range = vs.find('Radar_Reflectivity.valid_range')
        factor = vs.find('Radar_Reflectivity.factor')
        
    if (lat * lon * start * end * off * range * factor) != 0:
        return True
    
    
def isEEA(fileAbsPath):
    inFile = open(fileAbsPath)
    lines = inFile.readlines()
    inFile.close()
    for line in lines:
        values = line.split()
        if len(values) == 3:
            for value in values:
                float(value)
        else:
            raise Exception('Not the right amount of columns')
    return True
    
    
def isEVDC(fileAbsPath):
    inFile = SD(fileAbsPath)
    inFile.attributes(True)['DATA_LOCATION'][0]
    inFile.select('LATITUDE.INSTRUMENT')[0]
    inFile.select('LONGITUDE.INSTRUMENT')[0]
    inFile.select('ALTITUDE.INSTRUMENT')[0] 
    return True


def isFLEXPART(fileAbsPath):
    if os.path.exists(fileAbsPath + '/header'):
        return True


def isGOME_L2(fileAbsPath):
    with h5py.File(fileAbsPath, 'r') as inFile:
        inFile['/GEOLOCATION/LatitudeCentre']
        inFile['/GEOLOCATION/LongitudeCentre']
        inFile['/GEOLOCATION/Time']
        inFile['/TOTAL_COLUMNS/SO2']
        dataAttributes = inFile['/TOTAL_COLUMNS/SO2'].attrs
        dataAttributes['FillValue']
        metadata = inFile['/META_DATA'].attrs
        metadata['SatelliteID']
        metadata['InstrumentID']
        metadata['ProcessingLevel']
    return True


def isGOME2_BIRA_OMI(fileAbsPath):
    with h5py.File(fileAbsPath, 'r') as inFile:
        inFile['latitude']
        inFile['longitude']
        inFile['Time']
        inFile['SO2 vcd']
        inFile['SO2 averaging kernel']
        inFile['SO2 altitude grid']
    return True


def isLIDAR_EXTINCTION(fileAbsPath):
    with netCDF4.Dataset(fileAbsPath, 'r') as inFile:
        inFile.variables['Altitude'][:]
        inFile.variables['Extinction'][:]
        inFile.StartDate
        inFile.StartTime_UT
        inFile.StopTime_UT
        inFile.Location
        inFile.Longitude_degrees_east
        inFile.Latitude_degrees_north
        inFile.Altitude_meter_asl
        inFile.EmissionWavelength_nm
    if os.path.basename(fileAbsPath)[13] == 'e':
        return True
    
    
def isLIDAR_BACKSCATTER(fileAbsPath):
    with netCDF4.Dataset(fileAbsPath, 'r') as inFile:
        inFile.variables['Altitude'][:]
        inFile.variables['Backscatter'][:]
        inFile.StartDate
        inFile.StartTime_UT
        inFile.StopTime_UT
        inFile.Location
        inFile.Longitude_degrees_east
        inFile.Latitude_degrees_north
        inFile.Altitude_meter_asl
        inFile.EmissionWavelength_nm
    if os.path.basename(fileAbsPath)[13] == 'b':
        return True
    
    
def isLIDAR_BIRA(fileAbsPath):
    with open(fileAbsPath) as inFile:
        lines = inFile.readlines()
        lines = lines[41:len(lines)]
    
        if not lines:
            raise Exception('File has less than 42 lines')
    
        for line in lines:
            #check if it is a header or a data line
            values = line.split()
            if len(values) == 14 or len(values) == 10:
                for value in values:
                    float(value)
            else:
                raise Exception('Neither a header nor a data line')
    return True


def isMACC(fileAbsPath):
    with netCDF4.Dataset(fileAbsPath, 'r') as infile:
        infile.variables['time'][:]
        infile.variables['latitude'][:]
        infile.variables['longitude'][:]
        infile.variables['tcso2'][:]
        infile.variables['tcso2']._FillValue
        infile.variables['tcso2'].add_offset
        infile.variables['tcso2'].scale_factor
    return True

    
def isMOD07(fileAbsPath):
    with SD(fileAbsPath) as inFile:
        inFile.select('Skin_Temperature')
        inFile.select('Surface_Pressure')
        inFile.select('Retrieved_Moisture_Profile')
        inFile.select('Retrieved_Temperature_Profile')
        inFile.select('Latitude')
        inFile.select('Longitude')
    return True

def isMOD04(fileAbsPath):
    inFile = SD(fileAbsPath) 
    inFile.select('Image_Optical_Depth_Land_And_Ocean')
    inFile.select('Land_Ocean_Quality_Flag')
    inFile.select('Latitude')
    inFile.select('Longitude')
    return True

def isOSIRIS_L2(fileAbsPath):
    ncfile = netCDF4.Dataset(fileAbsPath, 'r')
    ncfile.variables['ozone_concentration'][:]
    ncfile.variables['latitude'][:] 
    ncfile.variables['longitude'][:]
    ncfile.variables['altitude'][:]
    return True

def isPARASOL_LAND(fileAbsPath):
    inFile = open(fileAbsPath)
    inFile.seek(36)
    filename = inFile.read(16)
    inFile.close()
    if re.match('.*P[123]L[123]TLG[1ABC][0123456789]{3}[0123456789]{3}[A-Z]D', filename):
        return True
    

def isPARASOL_SEA(fileAbsPath):
    inFile = open(fileAbsPath)
    inFile.seek(36)
    filename = inFile.read(16)
    inFile.close()  
    if re.match('.*P[123]L[123]TOG[1ABC][0123456789]{3}[0123456789]{3}[A-Z]D', filename):
        return True


def isSENTINEL_L2(fileAbsPath):
    with h5py.File(fileAbsPath, 'r') as inFile:
        inFile['PRODUCT']['latitude']
        inFile['PRODUCT']['longitude']
        inFile['PRODUCT']['so2_vertical_column']
        inFile['PRODUCT']['so2_slant_column_corrected']
        inFile['PRODUCT']['SUPPORT_DATA']['DETAILED_RESULTS']['processing_quality_flags']
        inFile['PRODUCT']['latitude'].attrs['_FillValue'][0]
    return True

def isSCISAT_L2(fileAbsPath):
    ncfile = netCDF4.Dataset(fileAbsPath, 'r')
    ncfile.groups['ACE-FTS-v2.2'].latitude
    ncfile.groups['ACE-FTS-v2.2'].longitude
    ncfile.groups['ACE-FTS-v2.2'].start_time
    ncfile.groups['ACE-FTS-v2.2'].end_time
    ncfile.groups['ACE-FTS-v2.2'].groups['Data-L2_1km_grid'].variables['O3'][:]
    ncfile.groups['ACE-FTS-v2.2'].groups['Data-L2_1km_grid'].variables['z'][:]
    ncfile.close()
    return True


def isWRFCHEM_SO2(fileAbsPath):    
    with netCDF4.Dataset(fileAbsPath, 'r') as inFile:
        inFile.variables['so2'][:]
        inFile.variables['Times'][:]
        inFile.variables['XLONG'][:]
        inFile.variables['XLAT'][:]
        inFile.variables['PH'][:]
        inFile.variables['PHB'][:]
        inFile.variables['HGT'][:]
    return True


def isWRFCHEM_ASH3D(fileAbsPath):
    with netCDF4.Dataset(fileAbsPath, 'r') as inFile:
        inFile.variables['vash_al'][:]
        inFile.variables['Times'][:]
        inFile.variables['XLONG'][:]
        inFile.variables['XLAT'][:]
        inFile.variables['PH'][:]
        inFile.variables['PHB'][:]
        inFile.variables['HGT'][:]
    return True

def isWRFCHEM_ASHCOL(fileAbsPath):
    with netCDF4.Dataset(fileAbsPath, 'r') as inFile:
        inFile.variables['vashcol_sat_col'][:]
        inFile.variables['Times'][:]
        inFile.variables['XLONG'][:]
        inFile.variables['XLAT'][:]
    return True

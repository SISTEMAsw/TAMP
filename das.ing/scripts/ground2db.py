#!/usr/bin/env python

from xml.etree import ElementTree as et
import datetime
import psycopg2
import sys
import os
import time
from ConfigParser import SafeConfigParser
import logging 

#connection = "dbname='groundbased' user='tamp' host='localhost' port='3333' password='tampuser'"

#filePath = "test_new.xml"
installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

def databaseCon():  # Opens db connection
    installation_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    parser = SafeConfigParser()
    parser.read("%s/../etc/das_ing.ini" % installation_dir)
    logging.debug("connecting...")
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" % (parser.get("proc", "name"), parser.get("proc", "user"), parser.get("proc", "host"), parser.get("proc", "pass")))
    #conn = psycopg2.connect(connection)

    return conn


def insertProduct(conn, value):  # Insert new product
    query = """INSERT INTO products (product) VALUES ('{}');""".format(value)
    cur = conn.cursor()
    try:
        cur.execute(query)
    except Exception as e:
        logging.error("Can't INSERT to products {}".format(e))
        raise
        #sys.exit("Can't INSERT to products\n{}".format(e))
    try:
        conn.commit()
    except Exception as e:
        logging.error("{}".format(e))
        raise
        #sys.exit("{}".format(e))
    logging.debug( "Added product: {}".format(value))
    time.sleep(1)
    searchProductID(conn, value)


def searchProductID(conn, value):  # checks product -> returns ID when found
    conn.rollback()
    query = """SELECT id, product FROM products WHERE product='{}';""".format(value)
    cur = conn.cursor()
    try:
        cur.execute(query)
    except Exception as e:
        logging.error("Can't SELECT from products {}".format(e))
        raise
        #sys.exit("Can't SELECT from products\n{}".format(e))

    rows = cur.fetchall()
    if not rows:  # if no ID is found -> make new DB entry
        insertProduct(conn, value)
    else:
        id = rows[0][0]
        return id


def insertStation(conn, station, latitude, longitude, height):  # inserts new station
    query = """INSERT INTO stations (name, latitude, longitude, height) VALUES ('{}', {}, {}, {});""".format(station, latitude, longitude, height)
    #print query
    cur = conn.cursor()
    try:
        cur.execute(query)
    except Exception as e:
        logging.error("Can't INSERT to station {}".format(e))
        raise
        #sys.exit("Can't INSERT to station\n{}".format(e))
    try:
        conn.commit()
    except Exception as e:
        logging.error("{}".format(e))
        raise
        #sys.exit("{}".format(e))
    logging.debug("Added station: {}".format(station))
    time.sleep(1)
    searchStationID(conn, station, latitude, longitude, height)


def searchStationID(conn, station, latitude, longitude, height):  # checks station -> returns ID
    query = """SELECT id, name FROM stations WHERE name='{}';""".format(station)
    cur = conn.cursor()
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        logging.error("Can't SELECT from stations {}".format(e))
        raise
        #sys.exit("Can't SELECT from stations\n{}".format(e))
    if not rows:  # if no station ID is found -> make new DB entry
        insertStation(conn, station, latitude, longitude, height)
    else:
        id = rows[0][0]
        return id


def checkDuplicate(conn, data):
    query = """SELECT id FROM measurements WHERE stations_id='{}' and observed_field='{}' and value='{}' and
                observation_time_start='{}' and observation_time_end='{}';""".format(data['station'], data['product'], data['value'], data['timeStart'], data['timeEnd'])
    cur = conn.cursor()
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        logging.error("Can't SELECT from stations {}".format(e))
        raise
        #sys.exit("Can't SELECT from stations\n{}".format(e))
    if rows:  # if no station ID is found -> make new DB entry
        return True
    else:
        return False


def addMeasurements(conn, dataList):  # add the list to the database
    cur = conn.cursor()
    try:
       # for data in dataList:
       logging.debug("Adding measurements, this could take some time ...")
       cur.executemany("""INSERT INTO measurements (stations_id, observed_field, value, observation_time_start, observation_time_end)
       VALUES(%(station)s, %(product)s, %(value)s, %(timeStart)s, %(timeEnd)s);""", dataList)
    except Exception as e:
        logging.error("Can't INSERT to measurements {}".format(e))
        raise
        #sys.exit("Can't INSERT to measurements\n{}".format(e))
    try:
        conn.commit()
    except Exception as e:
        logging.error("{}".format(e))
        raise
        #sys.exit("{}".format(e))
    logging.debug( "Added {} measurements".format(len(dataList)))


def ground2db(filePath):
    try:
        tree = et.parse(filePath)
        root = tree.getroot()
        station = root.find('siteName').text
        longitude = root.find('siteLongitude').text
        latitude = root.find('siteLatitude').text
        height = root.find('siteElevation').text

    except Exception as e:
        logging.error("{} - Not a valid XML file".format(e))
        raise
        #sys.exit("{} - Not a valid XML file".format(e))

    conn = databaseCon()
    stationID = searchStationID(conn, station, latitude, longitude, height)
    if not stationID:
        stationID = searchStationID(conn, station, latitude, longitude, height)
    productDat = root.find('data').find('field').text
    productID = searchProductID(conn, productDat)
    if not productID:
        productID = searchProductID(conn, productDat)
    dataList = []
    formatDate = "%Y-%m-%dT%H:%M:%SZ"
    try:
        for child in root.findall('data'):
            data = {}
            data['station'] = stationID
            data['timeStart'] = datetime.datetime.strptime(child.find('timeStart').text, formatDate)
            data['timeEnd'] = datetime.datetime.strptime(child.find('timeEnd').text, formatDate)
            if child.find('field').text != productDat:
                data['product'] = searchProductID(conn, child.find('field').text)
            else:
                data['product'] = productID
            if child.find('value').text == 'N/A':
                data['value'] = -9.999
            else:
                data['value'] = child.find('value').text
            duplicate = checkDuplicate(conn, data)
            if not duplicate:
                dataList.append(data)
    except Exception as e:
        logging.error("{} not found!".format(e))
        raise 
        #sys.exit("{} not found!".format(e))

    if dataList:
        addMeasurements(conn, dataList)
        try:
            conn.commit()
        except Exception as e:
            logging.error( "{}".format(e))
    else:
        logging.warning("Measurements already in the database")

    conn.close()
    logging.debug( "Everything done!")

if __name__ == '__main__':

    #LOAD CONFIGURATION
    try:
        parser = SafeConfigParser()
        parser.read("%s/../etc/das_ing.ini" % installation_dir)
    except Exception as e:
        print "I am unable to load configuration"
        print str(e)

    #set logger
    logging.basicConfig(
     stream= sys.stdout,
     #filename=installation_dir+"/../log/tampProcessingUtilities.log",
     level= int(parser.get("Logger","loglevel")),
     format='%(levelname)s\t| %(asctime)s | %(message)s'
    )

    if len(sys.argv) != 2:
        sys.exit("*Usage for a single XML file: ground2db.py filename\n")

    if not sys.argv[1].endswith('.xml'):
        sys.exit("{} is not a XML file".format(sys.argv[1]))

    else:
        try:
            ground2db(sys.argv[1])
        except:
            pass

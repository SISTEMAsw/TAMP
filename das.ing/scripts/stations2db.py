#!/usr/bin/env python

import psycopg2
import sys

#inputfile = 'stats_au.txt'
foundDBstations = []
connection = "dbname='groundbased' user='tamp' host='localhost' port='3333' password='tampuser'"


def databaseCon():  # Opens db connection
    try:
        conn = psycopg2.connect(connection)
        return conn
    except Exception as e:
        print
        sys.exit("Unable to connect!\n{}".format(e))


# Search for stations -------------------------------------------------------------------------
def searchStationID(conn, station_list):  # checks if station is already in the DB
    found = True
    query = """SELECT name, longitude, latitude, height, "stationCode" FROM stations WHERE name='{}';""".format(station_list["station"])
    cur = conn.cursor()
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        sys.exit("Can't SELECT from stations\n{}".format(e))
    if not rows:  # if no station is found -> false
         found = False
    else:
        print "**Station {} found**".format(station_list["station"])
        foundstation = {}
        foundstation["station"] = rows[0][0]
        foundstation["longitude"] = float(rows[0][1])
        foundstation["latitude"] = float(rows[0][2])
        foundstation["height"] = float(rows[0][3])
        foundstation["stationCode"] = rows[0][4]
        foundDBstations.append(foundstation)
    return found


# Insert stations --------------------------------------------------------------------------------
def insertStations(conn, station_list):  # add the list to the database
    cur = conn.cursor()
    try:
         print "Adding stations, this could take some time ..."
         cur.executemany("""INSERT INTO stations (name, latitude, longitude, height, "stationCode")
         VALUES(%(station)s, %(latitude)s, %(longitude)s, %(height)s, %(stationCode)s);""", station_list)
    except Exception as e:
        sys.exit("Can't INSERT to stations\n{}".format(e))


# Update stations ---------------------------------------------------------------------------------

def updateStation(conn, list):
    cur = conn.cursor()
    try:
         print "Updating stations, this could take some time ..."
         cur.executemany("""UPDATE stations SET name = %(station)s, latitude = %(latitude)s, longitude =  %(longitude)s, height= %(height)s, "stationCode" =%(stationCode)s
         WHERE name =%(station)s;""", list)
    except Exception as e:
        sys.exit("Can't Update stations\n{}".format(e))
    print "Everything done <3"

def prepareUpdateStation(conn, list):
    j=0
    update_list = []
    for station in list:
        print "\nUpdate station {}?".format(foundDBstations[j]["station"])
        print "stationCode: {}\nlongitude: {}\nlatitude: {}\nheight: {}".format(foundDBstations[j]["stationCode"],
                                                                                foundDBstations[j]["longitude"],
                                                                                foundDBstations[j]["latitude"],
                                                                                foundDBstations[j]["height"])
        print "\nWith station {}?".format(station["station"])
        print "stationCode: {}\nlongitude: {}\nlatitude: {}\nheight: {}".format(station["stationCode"],
                                                                                station["longitude"],
                                                                                station["latitude"],
                                                                                station["height"])
        update = raw_input("\n(Y)Yes, (N)No\n")
        if update == 'Y' or update == 'y' or update == 'yes':
            update_list.append(station)
        else:
            print "Skipped"
        j += 1
    updateStation(conn, update_list)

# Main --------------------------------------------------------------------------------------------
def stations2db(inputfile):
    stations = []
    foundstations = []
    i = 0
    try:
        file = open(inputfile, 'r')
    except Exception as e:
        print
        sys.exit("File not found\n")

    conn = databaseCon()

    try:
        for line in file:
            line = line.replace(",", "")
            line = line.replace("\n", "")
            line_split = line.split(" ")
            line_split[1] = line_split[1].replace("_", " ")
            station_list = {}
            station_list["stationCode"] = line_split[0]
            station_list["station"] = line_split[1]
            if not line_split[2]:
                station_list["latitude"] = 0
            else:
                station_list["latitude"] = float(line_split[2])
            if not line_split[3]:
                station_list["longitude"] = 0
            else:
                station_list["longitude"] = float(line_split[3])
            if not line_split[4]:
                station_list["height"] = 0
            else:
                station_list["height"] = float(line_split[4])
            found = searchStationID(conn, station_list)
            if not found:
                stations.append(station_list)
            else:
                i += 1
                foundstations.append(station_list)
    except Exception as e:
        print sys.exit("reading {}".format(e))

    if stations:
        insertStations(conn, stations)
        try:
            conn.commit()
        except Exception as e:
            sys.exit("{}".format(e))
    else:
        print "\nNothing to add!"

    print "\nAdded {} stations\nSkipped {}\n".format(len(stations), i)

    # If user wants to update the skipped stations
    if i > 0:
        falseflag = 0
        while falseflag == 0:
            skipping = raw_input("Update skipped stations?\n(Y)Yes - with comparison of each station\n(A)Yes all - Just update all skipped stations, I know what I am doing\n(N)No\n".format(len(stations), i))
            if skipping == 'Y' or skipping == 'Yes' or skipping == 'YES' or skipping == 'y':
                prepareUpdateStation(conn, foundstations)
                falseflag = 1
            elif skipping == 'N' or skipping == 'No' or skipping == 'NO' or skipping == 'n':
                print "Everything done <3"
                falseflag = 1
            elif skipping == 'A' or skipping == 'a':
                updateStation(conn, foundstations)
                falseflag = 1
            else:
                print "Not a valid input!"
    else:
        print "Everything done <3"


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit("*Usage for a single text file: stations2db.py filename\n")

    elif not sys.argv[1].endswith('.txt'):
        sys.exit("{} is not a text file".format(sys.argv[1]))

    else:
        stations2db(sys.argv[1])
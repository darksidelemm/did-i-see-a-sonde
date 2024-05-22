#!/usr/bin/env python
#
#   Utility functions to help with analysing Sondehub Data
#
#   Copyright (C) 2021  Mark Jessop <vk5qi@rfhead.net>
#   Released under GNU GPL v3 or later
#
import json
import logging
import glob
import math
import os.path
from math import radians, degrees, sin, cos, atan2, sqrt, pi
import numpy as np
import xml.etree.ElementTree as ET


def position_info(listener, balloon):
    """
    Calculate and return information from 2 (lat, lon, alt) tuples

    Copyright 2012 (C) Daniel Richman; GNU GPL 3

    Returns a dict with:

     - angle at centre
     - great circle distance
     - distance in a straight line
     - bearing (azimuth or initial course)
     - elevation (altitude)

    Input and output latitudes, longitudes, angles, bearings and elevations are
    in degrees, and input altitudes and output distances are in meters.
    """

    # Earth:
    # radius = 6371000.0
    radius = 6364963.0  # Optimized for Australia :-)

    (lat1, lon1, alt1) = listener
    (lat2, lon2, alt2) = balloon

    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)

    # Calculate the bearing, the angle at the centre, and the great circle
    # distance using Vincenty's_formulae with f = 0 (a sphere). See
    # http://en.wikipedia.org/wiki/Great_circle_distance#Formulas and
    # http://en.wikipedia.org/wiki/Great-circle_navigation and
    # http://en.wikipedia.org/wiki/Vincenty%27s_formulae
    d_lon = lon2 - lon1
    sa = cos(lat2) * sin(d_lon)
    sb = (cos(lat1) * sin(lat2)) - (sin(lat1) * cos(lat2) * cos(d_lon))
    bearing = atan2(sa, sb)
    aa = sqrt((sa ** 2) + (sb ** 2))
    ab = (sin(lat1) * sin(lat2)) + (cos(lat1) * cos(lat2) * cos(d_lon))
    angle_at_centre = atan2(aa, ab)
    great_circle_distance = angle_at_centre * radius

    # Armed with the angle at the centre, calculating the remaining items
    # is a simple 2D triangley circley problem:

    # Use the triangle with sides (r + alt1), (r + alt2), distance in a
    # straight line. The angle between (r + alt1) and (r + alt2) is the
    # angle at the centre. The angle between distance in a straight line and
    # (r + alt1) is the elevation plus pi/2.

    # Use sum of angle in a triangle to express the third angle in terms
    # of the other two. Use sine rule on sides (r + alt1) and (r + alt2),
    # expand with compound angle formulae and solve for tan elevation by
    # dividing both sides by cos elevation
    ta = radius + alt1
    tb = radius + alt2
    ea = (cos(angle_at_centre) * tb) - ta
    eb = sin(angle_at_centre) * tb
    elevation = atan2(ea, eb)

    # Use cosine rule to find unknown side.
    distance = sqrt((ta ** 2) + (tb ** 2) - 2 * tb * ta * cos(angle_at_centre))

    # Give a bearing in range 0 <= b < 2pi
    if bearing < 0:
        bearing += 2 * pi

    return {
        "listener": listener,
        "balloon": balloon,
        "listener_radians": (lat1, lon1, alt1),
        "balloon_radians": (lat2, lon2, alt2),
        "angle_at_centre": degrees(angle_at_centre),
        "angle_at_centre_radians": angle_at_centre,
        "bearing": degrees(bearing),
        "bearing_radians": bearing,
        "great_circle_distance": great_circle_distance,
        "straight_distance": distance,
        "elevation": degrees(elevation),
        "elevation_radians": elevation,
    }



def getDensity(altitude):
    """ 
	Calculate the atmospheric density for a given altitude in metres.
	This is a direct port of the oziplotter Atmosphere class
	"""

    # Constants
    airMolWeight = 28.9644  # Molecular weight of air
    densitySL = 1.225  # Density at sea level [kg/m3]
    pressureSL = 101325  # Pressure at sea level [Pa]
    temperatureSL = 288.15  # Temperature at sea level [deg K]
    gamma = 1.4
    gravity = 9.80665  # Acceleration of gravity [m/s2]
    tempGrad = -0.0065  # Temperature gradient [deg K/m]
    RGas = 8.31432  # Gas constant [kg/Mol/K]
    R = 287.053
    deltaTemperature = 0.0

    # Lookup Tables
    altitudes = [0, 11000, 20000, 32000, 47000, 51000, 71000, 84852]
    pressureRels = [
        1,
        2.23361105092158e-1,
        5.403295010784876e-2,
        8.566678359291667e-3,
        1.0945601337771144e-3,
        6.606353132858367e-4,
        3.904683373343926e-5,
        3.6850095235747942e-6,
    ]
    temperatures = [288.15, 216.65, 216.65, 228.65, 270.65, 270.65, 214.65, 186.946]
    tempGrads = [-6.5, 0, 1, 2.8, 0, -2.8, -2, 0]
    gMR = gravity * airMolWeight / RGas

    # Pick a region to work in
    i = 0
    if altitude > 0:
        while altitude > altitudes[i + 1]:
            i = i + 1

    # Lookup based on region
    baseTemp = temperatures[i]
    tempGrad = tempGrads[i] / 1000.0
    pressureRelBase = pressureRels[i]
    deltaAltitude = altitude - altitudes[i]
    temperature = baseTemp + tempGrad * deltaAltitude

    # Calculate relative pressure
    if math.fabs(tempGrad) < 1e-10:
        pressureRel = pressureRelBase * math.exp(
            -1 * gMR * deltaAltitude / 1000.0 / baseTemp
        )
    else:
        pressureRel = pressureRelBase * math.pow(
            baseTemp / temperature, gMR / tempGrad / 1000.0
        )

    # Add temperature offset
    temperature = temperature + deltaTemperature

    # Finally, work out the density...
    speedOfSound = math.sqrt(gamma * R * temperature)
    pressure = pressureRel * pressureSL
    density = densitySL * pressureRel * temperatureSL / temperature

    return density


def seaLevelDescentRate(descent_rate, altitude):
    """ Calculate the descent rate at sea level, for a given descent rate at altitude """

    rho = getDensity(altitude)
    return math.sqrt((rho / 1.225) * math.pow(descent_rate, 2))


def get_sonde_file_list(folder="."):
    """ Use glob to recurse through our sonde data store and return a list of all sondes files """
    return glob.glob(os.path.join(folder,"*/*/*.json"))


def load_summary_file(filename):
    _f = open(filename,'r')
    _data = _f.read()
    _f.close()

    try:
        data = json.loads(_data)

        # Summary data only has 3 entries, launch, burst and landing.
        if len(data) != 3:
            return None

        return data
    except:
        return None



def coordinates_to_kml_placemark(lat, lon, alt,
                                 name="Placemark Name",
                                 description="Placemark Description",
                                 absolute=False,
                                 icon="https://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",
                                 scale=1.0):
    """ Generate a generic placemark object """

    placemark = ET.Element("Placemark")

    pm_name = ET.SubElement(placemark, "name")
    pm_name.text = name
    pm_desc = ET.SubElement(placemark, "description")
    pm_desc.text = description

    style = ET.SubElement(placemark, "Style")
    icon_style = ET.SubElement(style, "IconStyle")
    icon_scale = ET.SubElement(icon_style, "scale")
    icon_scale.text = str(scale)
    pm_icon = ET.SubElement(icon_style, "Icon")
    href = ET.SubElement(pm_icon, "href")
    href.text = icon

    point = ET.SubElement(placemark, "Point")
    if absolute:
        altitude_mode = ET.SubElement(point, "altitudeMode")
        altitude_mode.text = "absolute"
    coordinates = ET.SubElement(point, "coordinates")
    coordinates.text = f"{lon:.6f},{lat:.6f},{alt:.6f}"

    return placemark


def path_to_kml_placemark(flight_path,
                          name="Flight Path Name",
                          track_color="ff03bafc",
                          poly_color="8003bafc",
                          track_width=2.0,
                          absolute=True,
                          extrude=True):
    ''' Produce a placemark object from a flight path array '''

    placemark = ET.Element("Placemark")

    pm_name = ET.SubElement(placemark, "name")
    pm_name.text = name

    style = ET.SubElement(placemark, "Style")
    line_style = ET.SubElement(style, "LineStyle")
    color = ET.SubElement(line_style, "color")
    color.text = track_color
    width = ET.SubElement(line_style, "width")
    width.text = str(track_width)
    if extrude:
        poly_style = ET.SubElement(style, "PolyStyle")
        color = ET.SubElement(poly_style, "color")
        color.text = poly_color
        fill = ET.SubElement(poly_style, "fill")
        fill.text = "1"
        outline = ET.SubElement(poly_style, "outline")
        outline.text = "1"

    line_string = ET.SubElement(placemark, "LineString")
    if absolute:
        if extrude:
            ls_extrude = ET.SubElement(line_string, "extrude")
            ls_extrude.text = "1"
        altitude_mode = ET.SubElement(line_string, "altitudeMode")
        altitude_mode.text = "absolute"
    else:
        ls_tessellate = ET.SubElement(line_string, "tessellate")
        ls_tessellate.text = "1"
    coordinates = ET.SubElement(line_string, "coordinates")
    coordinates.text = " ".join(f"{lon:.6f},{lat:.6f},{alt:.6f}" for lat, lon, alt in flight_path)

    return placemark


def read_json_file(filename):
    """
    Read in a SondeHub Exported JSON file and convert into data that can be used for KML Generation
    """

    output = {}

    _f = open(filename,'r')
    data = json.loads(_f.read())
    _f.close()

    # Read in everything into a dictionary, which de-dupes.
    _telem = {}
    for _entry in data:
        _telem[_entry['datetime']] = _entry
    
    # Get keys and sort, now we can pull out data in time order.
    _telem_dates = list(_telem.keys())
    _telem_dates.sort()

    _first = _telem[_telem_dates[0]]
    _last = _telem[_telem_dates[-1]]

    output['serial'] = _first['serial']
    output['last_time'] = _last['datetime']

    _path = []
    
    for _entry in _telem_dates:
        _a = _telem[_entry]

        _path.append([_a['lat'], _a['lon'], _a['alt']])

    output['path'] = _path

    return output


def _log_file_to_kml_folder(filename, absolute=True, extrude=True, last_only=False):
    ''' Convert a single sonde log file to a KML Folder object '''

    # Read file.
    _flight_data = read_json_file(filename)

    _flight_serial = _flight_data["serial"]
    _landing_time = _flight_data["last_time"]
    _landing_pos = _flight_data["path"][-1]

    _folder = ET.Element("Folder")
    _name = ET.SubElement(_folder, "name")
    _name.text = _flight_serial

    # Generate the placemark & flight track.
    _folder.append(coordinates_to_kml_placemark(_landing_pos[0], _landing_pos[1], _landing_pos[2],
                                                name=_flight_serial, description=_landing_time, absolute=absolute))
    if not last_only:
        _folder.append(path_to_kml_placemark(_flight_data["path"], name="Track",
                                             absolute=absolute, extrude=extrude))

    return _folder


def log_files_to_kml(file_list, kml_file, absolute=True, extrude=True, last_only=False):
    """ Convert a collection of log files to a KML file """

    kml_root = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    kml_doc = ET.SubElement(kml_root, "Document")

    for file in file_list:
        logging.debug(f"Converting {file} to KML")
        try:
            kml_doc.append(_log_file_to_kml_folder(file, absolute=absolute,
                                                   extrude=extrude, last_only=last_only))
        except Exception:
            logging.exception(f"Failed to convert {file} to KML")

    tree = ET.ElementTree(kml_root)
    tree.write(kml_file, encoding="UTF-8", xml_declaration=True)
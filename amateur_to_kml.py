#!/usr/bin/env python
import argparse
import json
import glob
import os
import sys
import logging
import pprint
import numpy as np
import time

from utils import *
from dateutil.parser import parse
import xml.etree.ElementTree as ET


def reformat_sondehub_data(telem):

    output = {}

    # Get keys and sort, now we can pull out data in time order.
    _telem_dates = list(telem.keys())
    _telem_dates.sort()

    _first = telem[_telem_dates[0]]
    _last = telem[_telem_dates[-1]]

    output['serial'] = _first['payload_callsign']
    output['last_time'] = _last['datetime']

    _path = []
    
    for _entry in _telem_dates:
        _a = telem[_entry]

        _path.append([_a['lat'], _a['lon'], _a['alt']])

    output['path'] = _path

    return output


def _telem_to_kml_folder(telem_data, absolute=True, extrude=True, last_only=False):
    ''' Convert a single sonde log file to a KML Folder object '''

    # Read file.
    _flight_data = reformat_sondehub_data(telem_data)

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

INFILE = 'amateur.json'
OUTFILE = 'amateur.kml'


_f = open(INFILE, 'r')
data = json.loads(_f.read())
_f.close()


_callsigns = list(data.keys())

kml_root = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
kml_doc = ET.SubElement(kml_root, "Document")


for call in _callsigns:
    logging.debug(f"Converting {call} to KML")
    try:
        kml_doc.append(_telem_to_kml_folder(data[call], absolute=True,
                                                extrude=True, last_only=False))
    except Exception:
        logging.exception(f"Failed to convert {call} to KML")

tree = ET.ElementTree(kml_root)
tree.write(OUTFILE, encoding="UTF-8", xml_declaration=True)
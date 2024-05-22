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


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description="SondeHub Utils", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--folder", default="summary_data/", help="Folder to read sonde summary data from")
    parser.add_argument("--output", default="serial_matches.txt", help="Write out matching serial numbers to this file.")
    parser.add_argument("--lat", type=float, default=37.4300, help="Latitude of observation site, in decmial degrees.")
    parser.add_argument("--lon", type=float, default=-89.6436, help="Longitude of observation site, in decmial degrees.")
    parser.add_argument("--alt", type=float, default=161, help="Altitude AMSL of the observing site, in metres.")
    parser.add_argument("--min_el", type=float, default=-5.0, help="Elevation threshold to filter sondes.")
    parser.add_argument("--datetime", type=str, default="2024-04-08T19:00:15Z", help="Time to search from")
    parser.add_argument("--window", type=float, default=3600*4, help="Time window (seconds)")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Verbose output (set logging level to DEBUG)")
    args = parser.parse_args()

    if args.verbose:
        _log_level = logging.DEBUG
    else:
        _log_level = logging.INFO

    # Setup Logging
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s", level=_log_level
    )

    observer = (args.lat, args.lon, args.alt)
    observer_time = parse(args.datetime)
    logging.info(f"Observer position: {observer}, time: {observer_time.isoformat()}")

    # Get list of sonde summary files.
    _file_list = glob.glob(f"{args.folder}/*.json")

    logging.info(f"Working on {len(_file_list)} files.")

    serials = {}

    for _file in _file_list:
        logging.debug(f"Testing file {_file}.")

        _data = load_summary_file(_file)
        if _data:
            for _entry in _data:
                _sonde_pos = (_entry['lat'], _entry['lon'], _entry['alt'])

                _pos_info = position_info(observer, _sonde_pos)

                if _pos_info['elevation'] > args.min_el:
                    _pos_time = parse(_entry['datetime'])
                    _time_diff = abs((observer_time-_pos_time).total_seconds())
                    if _time_diff < args.window:
                        logging.info(f"Match! - {_entry['datetime']}: {_entry['serial']} at {_pos_info['elevation']} degrees elevation, {_pos_info['bearing']} degrees azimuth.")
                        serials[_entry['serial']] = _entry
                    
    
    logging.info(f"Found {len(list(serials.keys()))} matching flights.")


    logging.info(f"Writing serial list to {args.output}")
    _out = open(args.output, 'w')
    for _serial in list(serials.keys()):
        _out.write(f"{_serial}\n")
    _out.close()

                


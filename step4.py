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
    parser = argparse.ArgumentParser(description="SondeHub Utils - Bin Summary Data", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--folder", default="telemetry/", help="Folder to read sonde summary data from")
    parser.add_argument("--output", default="outputs.kml", help="Write out telemetry to this file.")
    parser.add_argument("--lat", type=float, default=37.4300, help="Latitude of observation site, in decmial degrees.")
    parser.add_argument("--lon", type=float, default=-89.6436, help="Longitude of observation site, in decmial degrees.")
    parser.add_argument("--alt", type=float, default=161, help="Altitude AMSL of the observing site, in metres.")
    parser.add_argument("--min_el", type=float, default=1.0, help="Elevation threshold to filter sondes.")
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

    # Get list of sonde summary files.
    _file_list = glob.glob(f"{args.folder}/*.json")

    logging.info(f"Working on {len(_file_list)} files.")

    log_files_to_kml(_file_list, args.output, absolute=True, extrude=True, last_only=False)



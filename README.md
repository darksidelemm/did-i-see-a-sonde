# Did I see a Radiosonde?
Some scripts to extract data from SondeHub's S3 archive, and filter it to just data within a user-defined position and time range, to assist with determining if a 'Unidentified Flying Object' was a radiosonde.

This was written to figure out if the object that Destin (Smarter Every Day) saw during the April 2024 total solar eclipse was a radiosonde or not.

Some data on Destin's observation:
- Observation location: 37.43N, 89.6436W, ~161m AMSL
- Maximum eclipse time: 19:00:15Z, sun at 57.2 degrees elevation, 208 degrees azimuth.
- From eclipse start to eclipse end, the sun's elevation moved from 59.5 through 47 degrees, and azimuth from 171 to 235 degrees.

We approach the problem in the following way:
* Download all sonde summary files for the day we are interested in (in this case, April 8th 2024)
* Use the sonde summary data to determine which radiosonde serial numbers were within above the horizon at a user-specified location. From this we end up with a list of radiosonde serial numbers.
* Download the full JSON dataset for each of the identified sondes.
* For each sonde, perform further filtering, and extract just the portion of the flight which matches our time of interest.
* Plot the data on a sky-map, showing the position of the identified sondes relative to the sun.

### Authors
* Mark Jessop <vk5qi(at)rfhead.net>

## Dependencies
You will need the awscli python lib for this:
```
$ python -m venv venv
$ . venv/bin/activate
$ pip install awscli numpy matplotlib python-dateutil
```

### Optional AWS Configurations
In `~/.aws/config`:
```
[default]
s3 =
  max_concurrent_requests = 100
  max_queue_size = 10000
  multipart_threshold = 64MB
  multipart_chunksize = 16MB
  max_bandwidth = 50MB/s
  use_accelerate_endpoint = false
  addressing_style = path
```

## Step 1 - Downloading Sonde Summary Data

The sonde 'summary' datasets provide first/highest/last telemetry snapshots for every sonde serial number observed by the SondeHub network. This information is enough to perform quite a lot of analysis, such as assigning sondes to launch sites, and determining mean flight profile parameters.

These datasets can be browsed by date at: https://sondehub-history.s3.amazonaws.com/index.html#date/

To grab the data for the day we are interested in (the US 2024 total solar eclipse):

```
aws s3 cp --recursive --no-sign-request s3://sondehub-history/date/2024/04/08 summary_data/
```

We now have a large set of JSON files (1123 of them...) in summary_data.

## Step 2 - Filtering to just the area we are interested in
In this case step2.py's argument defaults are set up for Destin's eclipse viewing location.

```
$ python step2.py
2024-05-22 13:26:38,306 INFO: Observer position: (37.43, -89.6436, 161), time: 2024-04-08T19:00:15+00:00
2024-05-22 13:26:38,309 INFO: Working on 1122 files.
2024-05-22 13:26:38,320 INFO: Match! - 2024-04-08T18:12:24.000000Z: 22059930 at 6.859831971224835 degrees elevation, 219.06348469373216 degrees azimuth.
2024-05-22 13:26:38,320 INFO: Match! - 2024-04-08T18:39:41.000000Z: 22059930 at 2.1065424492403158 degrees elevation, 213.6806894049244 degrees azimuth.
2024-05-22 13:26:38,325 INFO: Match! - 2024-04-08T19:28:48.000000Z: 22059825 at 2.022511790319252 degrees elevation, 227.71658231389003 degrees azimuth.
2024-05-22 13:26:38,336 INFO: Match! - 2024-04-08T19:41:20.000000Z: 23066769 at 1.391398017624286 degrees elevation, 211.88810309752498 degrees azimuth.
2024-05-22 13:26:38,337 INFO: Match! - 2024-04-08T20:38:32.000000Z: 23066769 at 6.199018562311508 degrees elevation, 207.24176420958923 degrees azimuth.
2024-05-22 13:26:38,346 INFO: Match! - 2024-04-08T18:55:51.000000Z: 38E9E3A8 at 2.9485688476320564 degrees elevation, 198.95686185556602 degrees azimuth.
2024-05-22 13:26:38,346 INFO: Match! - 2024-04-08T19:11:12.000000Z: 38E9E3A8 at 4.0064192546585256 degrees elevation, 195.51534497459363 degrees azimuth.
2024-05-22 13:26:38,346 INFO: Match! - 2024-04-08T19:37:38.000000Z: 38E9E3A8 at 1.6654019279417733 degrees elevation, 180.24261814934113 degrees azimuth.
2024-05-22 13:26:38,347 INFO: Match! - 2024-04-08T20:28:45.000000Z: 22059040 at 2.114012634577715 degrees elevation, 56.731382852657674 degrees azimuth.
...
2024-05-22 13:26:38,417 INFO: Found 25 matching flights.
```

## Step 3 - Download full sonde telemetry data
Now we download all the raw telemetry data.

```
$ mkdir telemetry
$ ./step3.sh
```

We should now have a bunch of .json files in `./telemetry/`.

## Step 4 - Convert to KML
Next we can convert all the sonde flight paths in the telemetry directory to a kml file (output.kml)

```
$ python step4.py
```
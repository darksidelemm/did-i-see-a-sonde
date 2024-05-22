#!/bin/bash
while IFS= read -r line
do
   curl -L --compressed "https://api.v2.sondehub.org/sonde/$line" > telemetry/$line.json
done < serial_matches.txt
# garmin_gpx_fix
Small python script that fixes gpx file imported from garmin connect.

There are 2 possible operations to perform on the gpx file:
1) remove the gaps greater than a given threshold (in seconds) from the file
2) add the timestamps for the gpx file that is missing them 

Usage:

$ python gpx_fix.py -h
usage: gpx_fix.py [-h] [-o {remove-gaps,add-timestamps}] [-g GAP] input_file

positional arguments:
  input_file            Name of the gpx file to process

optional arguments:
  -h, --help            show this help message and exit
  -o {remove-gaps,add-timestamps}, --operation {remove-gaps,add-timestamps}
                        Operation to perform (default: remove-gaps)
  -g GAP, --gap GAP     Gap duration (in seconds) to use for the operation
                        (default: 15)

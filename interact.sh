#! /bin/bash
# Start the 'python' app, then run the command below for a python interpreter

if [ -f /dev/ttyACM0 ]
then
  screen /dev/ttyACM0 115200
else
  screen /dev/ttyUSB0 115200
fi
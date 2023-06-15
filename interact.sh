#! /bin/bash

# Start this script and start the 'python' app from the command line
# Start a web server (!) in your target directory
# then run the command 'deploy' on your computer and paste that in the python interpreter
# (Hint: press 'Ctrl+E' to activate paste mode, then paste, then press Ctr+D to execute. This sometimes fails though)
# The deploy script will download the necessary files via the local network and start them

if [[ -f /dev/ttyACM0 ]]
then
  screen /dev/ttyACM0 115200
else
  screen /dev/ttyUSB0 115200
fi
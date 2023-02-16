#! /bin/bash

echo "Deploying Hackerhotel package"

# python3 webusb_fat_mkdir.py /apps/
# python3 webusb_fat_mkdir.py /apps/python/
# python3 webusb_fat_mkdir.py /apps/python/hackerhotel

my_ip=$(ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}')

echo "import wifi"

echo "wifi.connect()"
echo "wifi.wait()"

echo "import os"
echo "import urequests as requests"

echo ""
echo "host = \"http://$my_ip:8081/\""
echo "targetdir = \"/lib/hackerhotel\""
# echo "targetdir = \"/sd/apps/python/hackerhotel\""

echo "os.chdir(targetdir)"

echo "def update():"
for F in ./hackerhotel/*
do
  
  FF=`echo $F | sed 's/^\\.\\/hackerhotel\\///'`
  if [[ $FF = "display.py" || $FF = "buttons.py" || $FF = "__pycache__" || $FF = "mch22.py" || $FF = "wifi.py" || $FF = "mapdata" || $FF = "utime.py" || $FF = "urequests.py" ]]
  then
    echo "Skipping $FF" > /dev/null
  elif [[ -d "$FF" ]]
  then
    # This is a directory
    echo "    # Skipping directory '$FF'"
  else  
    echo "    downloadToFile(host + \"$FF\", \"$FF\")"
  fi
done

cat deploy.py
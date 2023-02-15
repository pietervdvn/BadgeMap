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
cat hackerhotel/utils.py

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
  else
    
    # echo "$F --> /sdcard/apps/python/$FF"
    # cp $F /media/pietervdvn/3938-3063/apps/python/$FF
    # python3 ./mch2022-tools-master/webusb_push.py $F  /sdcard/apps/python/$FF
    echo "    downloadToFile(host + \"$FF\", \"$FF\")"
  fi
done

echo "def run():"
echo "    os.chdir(targetdir)"
echo "    f = open(\"main_entry.py\")"
echo "    script = f.read()"
echo "    f.close()"
echo "    exec(script)"
echo "def l():"
echo "    downloadToFile(host + \"DeskClock.py\", \"main_entry.py\")"
echo "    gc.collect()"
echo "    run()"
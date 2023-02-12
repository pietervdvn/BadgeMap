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
echo "host = \"http://$my_ip:8080/\""

echo "os.chdir(\"sd/apps/python/hackerhotel\")"

echo "def update():"
for F in ./hackerhotel/*
do
  
  FF=`echo $F | sed 's/^\\.\\/hackerhotel\\///'`
  if [[ $FF = "display.py" || $FF = "buttons.py" || $FF = "__pycache__" || $FF = "mch22.py" || $FF = "wifi.py" ]]
  then
    echo "Skipping $FF" > /dev/null
  else
    
    # echo "$F --> /sdcard/apps/python/$FF"
    # cp $F /media/pietervdvn/3938-3063/apps/python/$FF
    # python3 ./mch2022-tools-master/webusb_push.py $F  /sdcard/apps/python/$FF
    echo "    downloadToFile(host + \"$FF\", \"$FF\")"
  fi
done

echo "def l():"
echo "    downloadToFile(host + \"Main.py\", \"Main.py\")"
echo "    run()"

echo "def run():"
echo "    os.chdir(\"/sd/apps/python/hackerhotel\")"
echo "    f = open(\"Main.py\")"
echo "    script = f.read()"
echo "    f.close()"
echo "    exec(script)"
echo "l()"
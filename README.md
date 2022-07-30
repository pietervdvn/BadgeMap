# BadgeMap

This application loads and renders a geojson with micropython.

It can be used on event badges such as the MCH22 badge

To push to your badge:

```
cd mch_2022-tools-master
nix-shell
python3 webusb_fat_push.py ../__init__.py /sdcard/apps/python/badgemap/__init__.py
```
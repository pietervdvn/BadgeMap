# Some useful things to know when developing micropython

Use `python3 webusb_fat_push.py sourcefile /sdcard/apps/python/<appname>/filename.py`

- Include the filename
- Webusb expects `sdcard`, whereas the sdcard is internally visible as `sd`. Yes, this is confusing!
- Importing a file can be done via the shell with `import path.to.file` and it'll execute it

In a screen session, typing `CTRL+E` will enter paste mode which disables this annoying automatic indentation. However, for me it is somewhat unstable. 

# "Cloud"-development

Setup a host of the target directory (e.g. with webfsd) on port 8080
Run 'deploy.sh', paste it into an interactive console (CTRL+E)
Paste it into the console
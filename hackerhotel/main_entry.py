import os
targetdir = "/lib/deskcalendar"
print("Starting application "+targetdir+"/main_entry.py via loader ...")
os.chdir(targetdir)
f = open("DeskClock.py")
script = f.read()
f.close()
exec(script)
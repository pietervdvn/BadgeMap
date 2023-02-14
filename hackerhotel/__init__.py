import os
print(os.getcwd())
if not os.getcwd().endswith("hackerhotel"):
    os.chdir("/sd/apps/python/hackerhotel")
      
from .main_entry import Main
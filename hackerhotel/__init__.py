import os
print(os.getcwd())
if not os.getcwd().endswith("hackerhotel"):
    os.chdir("/lib/hackerhotel")
      
from .main_entry import Main
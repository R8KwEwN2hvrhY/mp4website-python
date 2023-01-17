import sys
import os

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, curr_dir)
#os.environ['PYTHONHOME']=‘C:\Users\frien\AppData\Local\Programs\Python\Python39\Scripts\’
#os.environ['  PYTHONPATH']=‘C:\Users\frien\AppData\Local\Programs\Python\Python39\Scripts\’
from fileserver import app
application = app

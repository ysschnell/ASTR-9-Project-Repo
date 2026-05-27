import pandas as pd

x = 56960 #idenifier goes here

HIPc = pd.read_csv('C:/Users/b17de/Downloads/asu.tsv', sep=';', comment='#') #swap this to your directory

bmv = HIPc.at[x,"B-V"]
HIPi = HIPc.at[x, "HIP"]

print(bmv, HIPi)

import sys
from pathlib import Path
baffles_dir = Path("C:/Users/b17de/BAFFLES") #swap this to your directory
sys.path.insert(0, str(baffles_dir))
import baffles

import os
currentdir=os.getcwd()
os.chdir(str(baffles_dir))
posterior = baffles.baffles_age(bv=float(bmv),li=229.3, #change as needed 
                                li_err=2, fileName=star_name+"Age_Posterior", savePlots=False)
os.chdir(currentdir)
import pandas as pd

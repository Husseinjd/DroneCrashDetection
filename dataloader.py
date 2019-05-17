'''
This class loads data from log files
into data dictionaries that can be queried
'''
import pandas as pd
import csv
import time
import numpy as np
import os
import json
import pickle


class DataLoader():

    def __init__(self,filepath):
        '''
        init a dataloader instance
        '''
        self.filepath = filepath
        self.dict = {}

    def load(self):
        """load file into a pandas data frame and queries the log
           into required form to add it to a dict for exporting as a pickle files

        Returns
        -------
        int
            returns -1 if loading of the file was not successfull

        """
        try: # parse error handling for log files
            df = pd.read_csv(filepath,names=range(30),low_memory=False)
        except:
            return -1 #broken file

         if len(df) == 1: # empty df
             return -1 # broken file

        #use components as index and drop fully empty columns
        df = df.set_index(0).dropna(axis=1, how='all')

         try:
             components  = df.loc['FMT'][3].str.strip() #not unique
         except:
             return -1 #data not complete




    def export(self,dict_export,ex_filename):
        """Export dict to pickle file
        Parameters
        ----------
        ex_filename : string
            export file name in the form of 'variablename_filename.pickle'

        """

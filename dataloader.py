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

    def __init__(self):
        '''
        init a dataloader instance
        '''
        self.errors_list = []
        # list with all variable detected (can contain duplicates)
        self.var_list = []

    def load(self,filepath):
        """load file into a pandas data frame and queries the log
           into required form to add it to a dict for exporting as a pickle files
        Returns
        -------
        int
            returns -1 if loading of the file was not successfull

        """
        self.filepath = filepath
        try:  # parse error handling for log files
            df = pd.read_csv(self.filepath, names=range(30), low_memory=False)
        except:
            print('Broken log file')
            self.errors_list.append(-1)
            return -1  # broken file

        if len(df) == 1:  # empty df
            print('Empty Dataframe')
            self.errors_list.append(-2)
            return -2  # broken file

        # use components as index and drop fully empty columns
        self.df = df.set_index(0).dropna(axis=1, how='all')

        try:
            self.components = self.df.loc['FMT'][3].str.strip()  # not unique
        except:
            print('Error in extracting components')
            self.errors_list.append(-3)
            return -3  # data not complete
        return 1  # read successfully

    def extractinfo(self,export=False):
        """Extract variable information from dataframe for each component
        Returns
        -------
        list of dataframes for each component
        """
        comp_list = []
        already_visited_list = []
        for j, c in enumerate(self.components):
            if c in already_visited_list:
                continue
            else:
                already_visited_list.append(c)
            variable_name_list = []
            if 'FMT' in self.df.index:
                # getting all the values
                c_labels = self.df.loc['FMT'][self.components == c].values[0][4:18]
                # removing nan values
                c_labels = [ob for ob in c_labels if not ob is np.nan]
                c_labels = np.array([str(c).strip() for c in c_labels])  # cleaning the spaces
                var_recor = [c+'_'+sub for sub in c_labels]
                variable_name_list = [sub for sub in c_labels]
                self.var_list += var_recor
                df_comp = self._non_equalcolumns(c, variable_name_list)
                if isinstance(df_comp,int): #component has inconsistent columns
                    continue
            # more goes on here to extract to pickle files
            #here we can add failure detection on the df comp per column

            #clean up the columsn that contain spaces
            try:
                df_comp = df_comp.apply(pd.to_numeric)
            except:
                print('No numeric conversion in component ', c)
            if export:
                    self.export(df_comp,c)

    def getcount(self):
        """returns a dataframe with the number of occurences for each variable found in the log files
        Returns
        -------
        dataframe ['variable','count']
        """
        if len(self.var_list) > 1:
            dt = {}
            uniq_var = set(self.var_list)
            for el in uniq_var:
                self.var_list.count(el)
                dt[el] = self.var_list.count(el)
        # dataframe
            return pd.DataFrame(dt, index=['count']).transpose()
        else:
            print('Please run load before trying to get count')
            return -1

    def _non_equalcolumns(self, comp, var_list):
        """Checks the var list vs the dataframe column list and
        creates a dataframe with the corrected column names for a specified component

        Parameters
        ----------
        comp: string
            component name
        var_list : string
            var list extracted from FMT

        Returns
        -------
        dataframe
            dataframe of the component with corrected columns names and th
            their corresponding values

        """
        # dataframe with only the variable added
        try:
            df_comp = self.df.loc[comp].dropna(axis=1, how='all')
                # drop any columns which has more than 70% of nan values
                # df_comp.drop(df_comp.loc[:,(df_comp.isnull().sum()  / len(df_comp) > 0.70)], axis=1 ,inplace=True)
        except:
                # component not in the dataframe
                return -1
            # variables are always less than columns in the log files
        cnter=0
        if len(var_list) < len(df_comp.columns):
                # calculate the difference and add dummy columns
                 for i in range(len(df_comp.columns) -  len(var_list)):
                            var_list.append(comp+'_'+str(cnter))
                            cnter+=1
        if len(var_list) > len(df_comp.columns):
                    return -1
        #check if it's RollIn instead of DesRoll
        if comp == 'ATT':
            self._fix_varlist(var_list)
        #----------------------------------------
        df_comp.columns = var_list.copy()
        return df_comp

    def _fix_varlist(self,varlist):
        for i,c in enumerate(varlist):
            if c == 'RollIn':
                varlist[i] = 'DesRoll'
            elif c == 'YawIn':
                varlist[i] = 'DesYaw'
            elif c == 'PitchIn':
                varlist[i] = 'DesPitch'

    def export(self,df_comp,comp_name):
        """export dataframe to pickle file per component
        """
        file_name = self.filepath[self.filepath.index('/') + 1:-4]
        df_comp.to_pickle('variables_info/'+comp_name +'_'+file_name+'.pickle')
        del df_comp

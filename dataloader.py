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
        #list of errors recorded while loading the data
        self.errors_list = []
        # list with all variable detected (can contain duplicates)
        self.var_list = []

    def load(self,filepath):
        """load file into a pandas data frame and extract log information into required
        format type

        Returns
        -------
        int
            returns -1 if loading of the file was not successfull
            returns 1 if loading was successfull

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
            self.df[3] = self.df[3].str.strip() # cleaning third column
        except:
            print('Dataframe with weird column datatypes and structure')
            self.errors_list.append(-4)
            return -4
        try:
            self.components = self.df.index.unique() # not unique
            #filter components to ones with spaces
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
        for j, c in enumerate(self.components):
            variable_name_list = []
            if 'FMT' in self.df.index:
                # getting all the values
                c_labels = self.df.loc['FMT'][self.df.loc['FMT'][3] == c]
                if len(c_labels) > 0: #if that component was not found in the logs
                    c_labels =  c_labels.values[0][4:18]
                else:
                    continue
                # removing nan values
                c_labels = [ob for ob in c_labels if not ob is np.nan]
                c_labels = np.array([str(c).strip() for c in c_labels])  # cleaning the spaces
                var_recor = [c+'_'+sub for sub in c_labels]
                variable_name_list = [sub for sub in c_labels] #this is used for the exported dataframe
                self.var_list += var_recor #this is used for variable counting
                df_comp = self._non_equalcolumns(c, variable_name_list)
                if isinstance(df_comp,int): #component has inconsistent columns
                    continue
            else:
                continue
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

        #some can contain more columns that are not all Nan making the parsing to numeric return an error
        if comp == 'ATT':
            try:
                df_comp = df_comp[['DesRoll','Roll','DesPitch','Pitch','DesYaw','Yaw']]
            except:
                return -1

        return df_comp

    def _fix_varlist(self,varlist):
        """Fixing the naming schema for roll,pitch and yaw before exporting

        Parameters
        ----------
        varlist : list
            list of names extracted
        """
        for i,c in enumerate(varlist):
            if c == 'RollIn':
                varlist[i] = 'DesRoll'
            elif c == 'YawIn':
                varlist[i] = 'DesYaw'
            elif c == 'PitchIn':
                varlist[i] = 'DesPitch'


    def export(self,df_comp,comp_name):
        """export dataframe to csv file per component

        -- this might be changed later to export into a database
        """
        file_name = self.filepath[self.filepath.index('/') + 1:-4]
        df_comp.to_csv('variables_info/'+comp_name +'_'+file_name+'.csv')
        del df_comp


    def read_file(self,component,logfile_name,variable_needed):
        """a method for querying extracted
        dataframes

        Parameters
        ----------
        component_df_name : str
        logfile_name : str
        variable_needed : str

        Returns
        -------
        series
            columns required from dataframe if found
        int
            return -1 if column was not found

        """
        path = 'variables_info/'+component+'_/'+logfile_name+'.csv'
        try:
            temp = pd.read_csv(path)
        except:
            print('File not found error')
            return -1
        try:
            return temp[variable_needed]
        except:
            print('Variable not found in dataframe --KeyError')
            return -1

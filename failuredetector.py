'''
This file includes a FailureDetector Class,
containing conditions to label the failure occurred
'''
import pandas as pd
import numpy as np
import glob


class FailureDetector():
    '''
            The class contains different methods to detect the failure
            in the components and report back the reason for that failure based
            on rule based conditions.
    '''
    def __init__(self):
        """init the failureDetector instance
        """
        # failures to add to the table
        self.full_failure_table = pd.DataFrame() #rows to this table are appended using failures dict

        self._reset_failures()

        self.parameters = {'ATT': ['DesRoll','Roll','DesPitch','Pitch','DesYaw','Yaw','ErrRP','ErrYaw'] ,
                           'ATUN': ['TuneStep','RateMax','RPGain','RDGain','SPGain'],
                           'GPS': ['Time','NSats','HDop','Lng','RelAlt','Alt','SPD','GCrs']
                           }


    def _reset_failures(self):
        self.failures = {'File Name': np.nan,
                             'GPS Failure': np.nan ,
                             'Mechanical Failure': np.nan,
                              'Compass Failure': np.nan,
                              'Power Failure': np.nan,
                              'Gyroscope Failure': np.nan,
                              'Radio Failure': np.nan,
                              'ERR': np.nan,
                              'Uncontrolled yaw': np.nan,
                              'Uncontrolled altitude':np.nan,
                              'Uncontrolled pitch':np.nan,
                              'Uncontrolled roll':np.nan}

    def check_file_exist(self,component,filelist):
        """checks for the exists of a dataframe pickle file and returns the name
            of the file

        Parameters
        ----------
        component : string

        filelist : list
            list of pickle files

        Returns
        -------
        string
            filepath
        """
        for f in filelist:
            if component in f:
                return f
        return -1

    def detectFailures(self,filelist):
        """Loops through each file's variables and checks if a failure is detected
            using predefined rules
        """
        self.fileslist = filelist
        self.log_name = filelist[0][filelist[0].index('_')+1:-7]

        #check if component exists in the files
        #loop throught the components present in the parameters dictionary
        if self.check_file_exist('ATT',self.filelist) != -1: #if component file was found
                df_comp = pd.read_pickle(f)
                self.checkATT(df_comp)

        if self.check_file_exist('GPS',self.filelist) != -1: #if component file was found
                df_comp = pd.read_pickle(f)
                self.checkGPS(df_comp)

        # update failure dataframe
        self.failures['File Name'] = self.log_name
        self.full_failure_table = self.full_failure_table.append(self.failures,ignore_index=True)
        self._reset_failures()

        return self.full_failure_table


    def checkGPS(self,df_comp):
        #not implemented yet..
        #should follow the same rules
        pass


#-------------------------------------------------------------------------------------------------------------
    def checkATT(self,df_comp):
        """Checks for ATT failures and updates failure dict to True failures or False otherwise

        """
        cls = df_comp.columns
        if 'DesRoll'  in cls and 'Roll'  in cls :
            if self._checkroll(df_comp['DesRoll'],df_comp['Roll']):
                self.failures['Uncontrolled roll'] = True
            else:
                self.failures['Uncontrolled roll'] = False

        if 'DesPitch'  in cls and 'Pitch'  in cls:
            if self._checkpitch(df_comp['DesPitch'],df_comp['Pitch']):
                self.failures['Uncontrolled pitch'] = True
            else:
                self.failures['Uncontrolled pitch'] = False

        if 'DesYaw'  in cls and 'Yaw'  in cls:
            if self._checkyaw(df_comp['DesYaw'],df_comp['Yaw']):
                self.failures['Uncontrolled yaw'] = True
            else:
                self.failures['Uncontrolled yaw'] = False


    def _checkyaw(self,desraw,raw):
        if len(abs(desraw - raw) > 40) >= 0 :
            return True
        return False

    def _checkpitch(self,despitch,pitch):
        if len(abs(despitch - pitch) > 40) >= 0 :
            return True
        return False

    def _checkroll(self,desroll,roll):
        if len(abs(desroll - roll) > 40) >= 0 :
            return True
        return False

 # more methods here for different failures that can occur

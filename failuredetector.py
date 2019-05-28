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
                              'Acceleromer  Failure': np.nan,
                              'Radio Failure': np.nan,
                              'Uncontrolled latitude':np.nan,
                              'Uncontrolled longitude':np.nan,
                              'Uncontrolled altitude':np.nan,
                              'Uncontrolled yaw': np.nan,
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


    def _dropnacol(self,df_comp):
        '''
        some dataframes still contain fully Nan columns
        '''
        #drop columns if nan reach more than 95% percent of the number of rows
        df_comp =df_comp.dropna(axis=1,thresh=int(0.95* len(df_comp)),how='all',)
        try:
            df_comp = df_comp.apply(pd.to_numeric)
        except:
            print('No numeric conversion in component') #can be due to many errors
            return -1
        return 1

    def detectFailures(self,filelist,filename):
        """Loops through each file's variables and checks if a failure is detected
            using predefined rules
        """
        self.filelist = filelist
        self.log_name = filename

        #check if component exists in the files
        #loop throught the components present in the parameters dictionary
        f_err = self.check_file_exist('ERR',self.filelist)
        if  f != -1:
            df_err = pd.read_csv(f)
        else:
            df_err = None


        f_att = self.check_file_exist('ATT',self.filelist)
        if f != -1: #if component file was found
                df_comp = pd.read_csv(f)
                res = self._dropnacol(df_comp)
                if res == 1:
                    self.checkATT(df_comp)


        f_gps = self.check_file_exist('GPS',self.filelist)
        if f != -1: #if component file was found
                df_comp = pd.read_csv(f)
                res = self._dropnacol(df_comp)
                if res == 1:
                    self.checkGPS(df_comp,df_err)



        # update failure dataframe
        self.failures['File Name'] = self.log_name



        #append to the full table of log files
        self.full_failure_table = self.full_failure_table.append(self.failures,ignore_index=True)
        self._reset_failures()
        return self.full_failure_table




    def uc_altitude(self,gps_ralt,baro_alt,ctun_alt):
        pass

    def uc_latitude(self,gps_lat,cmd_lat):
        pass

    def uc_longitude(self,cmd_lng,gps_lng):
        pass
#----------------------------------------------------------------------------------------------
    def checkGPS(self,df_comp,df_err=None):
        cls = df_comp.columns
        self.failures['GPS Failure'] = False

        if 'NSats' in cls:
            if sum(df_comp['NSats'][df_comp['NSats'] < 10 ]) > 0:
                self.failures['GPS Failure'] = True

        if 'HDop' in cls:
            if sum(df_comp['HDop'][df_comp['HDop'] < 10 ]) > 0:
                self.failures['GPS Failure'] = True

        #check error dataframe
        if df_err is not None:
                cls_err = df_err.columns
                if 'Subsys' in cls_err and 'ECode' in cls_err:
                    for index, row in df_err.iterrows():
                        if (row['Subsys'] == 11 ) and (row['ECode'] == 2):
                            self.failures['GPS Failure'] = True
       #check error codes from df_err ['Subsys','ECode']


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
        try:
            if len(abs(desraw - raw) > 40) > 0 :
                return True
        except:
            print('Error occured in subtracting raw in file :', self.log_name)
            return False
        return False

    def _checkpitch(self,despitch,pitch):
        try:
            if len(abs(despitch - pitch) > 40) > 0 :
                return True
        except:
            print('Error occured in subtracting pitch in file :', self.log_name)
            return False
        return False

    def _checkroll(self,desroll,roll):
        try:
            if len(abs(desroll - roll) > 40) > 0 :
                return True
        except:
            print('Error occured in subtracting roll in file :', self.log_name)
            return False
        return False
 # more methods here for different failures that can occur

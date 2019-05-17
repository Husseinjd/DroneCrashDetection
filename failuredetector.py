'''
This file includes a FailureDetector Class,
containing conditions to label the failure occurred
'''
import pandas as pd
import numpy as np

class FailureDetector():
            '''
            The class contains different methods to detect the failure
            in the components and report back the reason for that failure based
            on rule based conditions.
            '''
    def __init__(self,vardata):
        """init the failureDetector instance

        Parameters
        ----------
        vardata : 'numpyarray/dataframe'
            data containing variables information,
            for e.g GPS_RAlt, GPS_Lat ...
        """
        self.df = vardata.copy()

    def gps_fail(self):
        """Checks for GPS failures and returns the
        failure reason as 1 else 0

        Returns
        -------
        int
            failure result is 1
        """
        pass

    def gyro_fail(self):
        """Check for gyroscope failures

        Returns
        -------
        int
            failure result is 1 else 0
        """
        pass

 #more methods here for different failures that can occur

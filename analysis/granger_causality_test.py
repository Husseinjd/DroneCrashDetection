from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import sys
import pickle

class GrangerCausalityTest():
    def __init__(self, root_directory, cleaned_logs_folder):
        """

        :param root_directory: Root project directory
        :param raw_ardu_logs_folder: The folder containing raw ardupilot logs (ardu_data)
        :param cleaned_logs_folder: The folder containing cleaned logs and stored as pickles. (variables_info)
        """

        self.root_directory = root_directory
        self.cleaned_logs = self.root_directory + "\\" + cleaned_logs_folder

    def stationary_test(self, timeseries, plot = False, print_stats = False):
        """

        :param timeseries: The timeseries to be tested
        :param plot: Flag variable to plot
        :return: A dataframe with the results and a flag which is True if the signal is stationary and False if not.
        """
        dftest = adfuller(timeseries, autolag='AIC')
        dfoutput = pd.Series(dftest[0:4],
                             index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
        is_stationary = False
        for key, value in dftest[4].items():
            dfoutput['Critical Value (%s)' % key] = value
        if print_stats:
            print ('Results of Dickey-Fuller Test:')
            print (dfoutput)
        if dfoutput['Test Statistic'] <= dfoutput['Critical Value (1%)']:
            is_stationary = True
        if plot:
            plt.clf()
            plt.xlabel("Time")
            plt.ylabel("Signal")
            plt.plot(timeseries.values)
            plt.show()
        return dfoutput, is_stationary

    def save_as_pickle(self,object, path, filename):
        """
        Save an object as a pickle file
        :param object: The python object. Can be list, dict etc.
        :param path: The path where to save.
        :param filename: The filename
        """
        with open(path + "\\" + filename, 'wb') as handle:
            pickle.dumps(object, handle)
        print("Save "+ name +" successfully.")

    def load_pickle(self,path, name):
        """
        Load a python object from a pickle file
        :param path: Path where the object is stored
        :param name: File name
        :return: The python object
        """
        with open(path + "\\" + name, 'rb') as handle:
            return_obj = pickle.load(handle)
        return return_obj

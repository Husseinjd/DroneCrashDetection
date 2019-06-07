from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.tsatools import lagmat2ds
import statsmodels.api as sm
from statsmodels.tools.tools import add_constant
from statsmodels.tsa.vector_ar.var_model import VAR
from scipy import stats
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import sys
import pickle

class GrangerCausalityTest():
    def __init__(self,x=None,y=None,pd_frame=None,maxlag=None,alpha=0.05,names=['x','y']):
        """
            Init
        """
        self.alpha = alpha
        self.names = names
        self.x = x
        self.y = y
        self.maxlag = maxlag
        self.df = pd_frame
        self.dict_res = {}


    def var_grangertest(self,check_stationary=True,verbose=True,use_simpleols = False):
        if self.df is None:
            print('Empty Dataframe')
            return -1
        
        if len(self.df.columns) > 2:
            print('Df has more than 2 columns')
            return -1
        
        #check that both variables are stationary
        if check_stationary:
            _,is_stationary_x = self.stationary_test(self.df.iloc[:,0])
            _,is_stationary_y = self.stationary_test(self.df.iloc[:,1])
            if not (is_stationary_x and is_stationary_y):
                    if verbose:
                        print('Series not stationary')
                    self.dict_res['err'] = True
                    return np.nan
            else:
                self.dict_res['err'] = False



        xcy = self.df.columns[0]+ ' causes ' + self.df.columns[1]
        ycx = self.df.columns[1]+ ' causes ' + self.df.columns[0]
        nc = 'no-causal'
        self.dict_res = {xcy : np.nan , ycx : np.nan , nc : np.nan,'bc' : np.nan ,'err': np.nan}

        
        model = VAR(self.df)
        try:
            if use_simpleols:
                raise Exception('Except')
            mf = model.fit(maxlags=self.maxlag,ic='aic',verbose=False)
        except: #Error when using aic  'x already contains a constant' use full model
            #mf = model.fit(maxlags=self.maxlag,ic=None,verbose=False)
            self.x = self.df.iloc[:,0]
            self.y = self.df.iloc[:,1]
            self.names = self.df.columns
            self.simple_grangertest()
            return 0
        #first column caused
        #second column causing

        #xcy
        res_xyc = mf.test_causality(self.df.columns[1],self.df.columns[0])
        if res_xyc.conclusion == 'reject':
            self.dict_res[xcy] =True
        else:
            self.dict_res[xcy] = False


        #ycx
        res_ycx = mf.test_causality(self.df.columns[0],self.df.columns[1])
        if res_ycx.conclusion == 'reject':
            self.dict_res[ycx] =True
        else:
            self.dict_res[ycx] = False



        #both causes each other
        if self.dict_res[ycx] and  self.dict_res[xcy]:
            self.dict_res['bc'] = True
        
        #no causal
        if self.dict_res[xcy] == False and self.dict_res[ycx] == False:
            self.dict_res[nc] = True
        else:
            self.dict_res[nc] = False

        return 0 #success


    def stationary_test(self,timeseries, plot = False, print_stats = False):
        try:
            dftest = adfuller(timeseries,maxlag=5, autolag='t-stat') #this was changed to the time it takes
        except:
            return None,False
        dfoutput = pd.Series(dftest[0:4],index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
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
        self.output = dfoutput
        return dfoutput, is_stationary

    def simple_grangertest(self):
        """checks if the 

                -  x causes y
                -  y causes x
                - both cause each other
                - no causes        
        
        Arguments:
            x {numpyarray/series} -- series
            y {[numpyarray/series]} -- series
            maxlag {[int]} -- max number of lag
        """


        xcy = self.names[0]+ ' causes ' + self.names[1]
        ycx = self.names[1]+ ' causes ' + self.names[0]
        nc = 'no-causal'
        self.dict_res = {xcy : np.nan , ycx : np.nan , nc : np.nan,'bc' : np.nan ,'err': np.nan}

        #check if x causes y 
        res_xcy = self.granger_test()
        #loop through and check if pvalue < self.alpha
        if not isinstance(res_xcy,dict) or res_xcy == -1:
            self.dict_res['err'] = True
            return np.nan
        else:
            self.dict_res['err'] = False
            self.dict_res[xcy] = False
            #print(res_xcy)
            for _,value in res_xcy.items():
                if value['pvalue'] < self.alpha:
                    self.dict_res[xcy] = True
        
        #switch variables
        temp = self.x
        self.x = self.y
        self.y = temp

        res_ycx = self.granger_test()
        if not isinstance(res_ycx,dict) or res_ycx == -1:
            #self.dict_res['err'] = True
            return np.nan
        else:
            self.dict_res[ycx] = False
            #print(res_ycx)
            for _,value in res_ycx.items():
                if value['pvalue'] < self.alpha:
                    self.dict_res[ycx] = True


        if res_xcy == False and res_ycx == False:
            self.dict_res[nc] = True
        else:
            self.dict_res[nc] = False

        if  self.dict_res[ycx] and self.dict_res[xcy]:
            self.dict_res['bc']  = True
        else:
            self.dict_res['bc']  = True

           
        

    def granger_test(self,bias=False,check_stationary=True):
        """apply granger causality test to test of x causes y
        
        Arguments:
            x {numpy array} -- list of numeric values
            y {numpy array} -- list of numeric values
            alpha {float} -- alpha for p-value comparison
            lag {int} -- the number of lags to consider
            bias {bool} -- including bias in the ols model
        """
        # we want to check if x causes y
        #check if lag 
        if len(self.x) != len(self.y):
            print('Incompatible length between x and y')    
            return -1
        #check if x and y are of the same length
        if self.maxlag > len(self.x):
            print('incompatible observations count and Lag value')
            return -1
        #data preparation 
        self.res = {}
        #test for different lags if maxlog not equal to None
        for lg in range(1,self.maxlag+1): #here we can use ar models with aic or bic to choose the best fit model
            x_prev = lagmat2ds(self.x,lg)[:,1:] #xt-1 , #xt-2 ... 
            y_prev = lagmat2ds(self.y,lg)[:,1:] # yt-1 , yt-2  ..
            if bias:
                x_prev = add_constant(x_prev,prepend=False)
                y_prev = add_constant(y_prev,prepend=False)
            #full model
            x_y_prev = np.concatenate((x_prev,y_prev),axis=1) 
            full_model =  sm.OLS(self.y,x_y_prev).fit() 
            #reduced model
            red_model = sm.OLS(self.y,y_prev).fit()
            #F-test 
            df1 = lg
            df2 = len(self.y) - 2*lg - 1
            fstat,p_value = self.f_test (red_model,full_model,df1,df2)
            self.res[lg] = {'pvalue':p_value,'F-Stat':fstat}
            #def granger_test(x,y,lag):
        #return false is no detection happened for all lags
        
        return  self.res 

    def f_test(self,r_model,f_model,df1,df2):
        """perform an F test on the two models and returns the p value 
            H0 : reduced model
            H1: full model
        
        Arguments:
            r_model {ols model} -- reduced model
            f_model {ols model} -- full Model
            df1 : degrees of freedom numerator
            df2 : degrees of freedom denominator
        """
        fstat = ((r_model.ssr - f_model.ssr)/ df1) / (f_model.ssr / df2)
        p_value = 1- stats.f.cdf(fstat, df1, df2)
        return fstat,p_value

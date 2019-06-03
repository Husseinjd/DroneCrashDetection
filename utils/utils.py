"""
This module contains helper functions that are used
in the analysis
"""
import numpy as np
import pandas as pd
import pickle
import seaborn as sns

def time_df(time_list,plot=False,save_path=None):
    dtime = pd.DataFrame(time_list,columns=['logname','size MB','duration s'])
    if plot:
        sns.lineplot(y='duration s',x='size MB',data=tm)
        plt.ylabel('Seconds')
        plt.xlabel('MB')
        plt.title('Top 100 Causality Time Statistic')
        plt.show()
    if save is not None:
        dtime.to_csv(save_path)
    return dtime

def encode_cause(df_dict1,sig,dict_var,empty_dict):
    """
    Parses dict with comp -> [caused1,caused2, caused3 ...] 
    and adds it to the dataframe of the component
    """
    #dict_var : GPS causes : [ 1 ,2 ,3 nc]
    d = empty_dict.copy()
    for v in dict_var[sig]:
            if 'nc' in v:
                d[v[:-2]] = 0 #no cause 
            elif 'bc' in v:
                 d[v[:-2]] = 2 #both causes each other
            else:
                d[v] = 1 #the component is the causes and the columns are the ones affected
    #concat to the df 
    df_dict1[sig] = pd.concat([df_dict1[sig],pd.DataFrame(d,index=[len(df_dict1[sig])])])#the df to concat the value to


def check_state(gc_t,sr):
    try:
        _,is_stat = gc_t.stationary_test(sr)
        return is_stat
    except:
        return -1



def save_as_pickle(a, path, filename):
        """
        Save an object as a pickle file
        :param object: The python object. Can be list, dict etc.
        :param path: The path where to save.
        :param filename: The filename
        """
        with open(path+'\\'+ filename, 'wb') as handle:
                pickle.dump(a, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print("Save "+ filename +" successfully.")

def load_pickle(path, name):
        """
        Load a python object from a pickle file
        :param path: Path where the object is stored
        :param name: File name
        :return: The python object
        """
        with open(path + "\\" + name, 'rb') as handle:
            return_obj = pickle.load(handle)
        return return_obj


def yawfix(series):
    """fixes yaw reset

    Parameters
    ----------
    series : pandas series

    Returns
    -------
    series
        fixed series values
    """
    diff = series - series.shift(-1)
    pos_add = np.where(diff > 300, 1, 0)
    neg_add = np.where(diff < -300, -1, 0)
    sum = pos_add + neg_add
    sum = sum.cumsum()
    sum = sum * 360
    sum = pd.Series(sum, index = series.index)
    series = series + sum.shift(1)
    return series

def load_top100_dict(sample=None):
    df = load_top100()
    vardict = {}
    for var in df['name'][:sample]:
        key_comp = var[:var.index('_')]
        var_sub = var[var.index('_')+1:]
        if key_comp in vardict.keys():
            vardict[key_comp].append(var_sub)
        else:
            vardict[key_comp] = [var_sub]
    return vardict


def load_top100():
    df = pd.read_csv('../stats_files/top_100_variables.csv')
    try:
        df.columns  =['name','count']
    except:
        df.drop('Unnamed: 0',axis=1,inplace=True)
        df.columns  =['name','count']
    df = df[~df.name.str.contains("FMT")]
    return df

def cat_to_int(df,col):
    """cat categories to integer values

    Parameters
    ----------
    df : dataframe
        Description of parameter `df`.
    col : str
        column in the dataframe to be casted

    Returns
    -------
    int
        returns -1 if error occured

    """
    try:
        df[col]  = pd.factorize(df[col])[0]
    except:
        print('Error Occured while casting')
        return -1

def corr_var(filename,loader,dictlist,find_corr=True):
    """
    :param dictlist  : dict with components needed as key and variable list as values
    e.g. { RCIN : [C1,C2 ..]}
    """
    full_df = pd.DataFrame({'tempcol':[0]}) #temp dataframe
    novaluescounter=0 #count the number of columns not found per log file
    for key,values in dictlist.items():
        resp = loader.dbconnector.query(key+'_'+filename)
        if resp != -1: #component found in the database
            df = pd.DataFrame(resp)
        else:
            print('Component not found: ',key)
            return -1
        try:
            #choose only the columns that exists in dataframe
            values = list(set(df.columns) & set(values))
            df = df[values+['lineIndex']].set_index('lineIndex')
            df.columns = [key+'_'+col for col in df.columns]
        except:
            novaluescounter+=1
            continue
        full_df = pd.concat([full_df,df],axis =1).fillna(method = 'ffill')
    
    #clean up the init column
    full_df = full_df.drop([0],axis=0)
    full_df = full_df.drop('tempcol',axis=1)

    if len(full_df) > 1 :
        #check for categorica  l columns and set them for numeric
        for col in full_df.columns:
            if not full_df[col].dtype.kind in 'bifc':
                cat_to_int(full_df,col)
        if find_corr:
            return novaluescounter,full_df.corr()
        else:
            return full_df
    else:
        print('No values in the component were found')
        return -1

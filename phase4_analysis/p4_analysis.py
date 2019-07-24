""" 
Methods used in analysis of phase 4 
-> Jupyter notebook in the file used to run the methods and script
"""
import pandas as pd
import numpy as np
import os
import sys
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import warnings
import seaborn as sns
warnings.filterwarnings('ignore')
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from db.database import DatabaseConnector
from dtloader.dataloader import DataLoader
from utils.utils import *
from utils.features_eng import *
from segmentation.segmentation import Segmentation
from scipy.stats import ttest_ind
from statsmodels.tsa.stattools import grangercausalitytests

def segment_signal(sr,max_err = None,err_growth=0,num_dessegs=np.inf):
    """
    return a segment list of the signal
    """
    if max_err is None:
        max_err = np.mean(sr)
    sg = Segmentation(max_err)
    fitmethod= 'inter'
    sgmethod = 'td'
    segments = sg.segment(sr,seg_method=sgmethod,fit_method=fitmethod,err_growth=err_growth,batch=False,batch_size=50,num_dessegs=num_dessegs)
    return segments

def idx_segments_threshold(df_sg,sgmts,percen=92):
    """Return target list of segments were ration greater than the 92 percentile by default
    
    Arguments:
        df_sg {[dataframe]} -- [description]
        sgmts {[list of tuples]} -- [description]
    
    Keyword Arguments:
        percen {int} -- [description] (default: {92})
    
    Returns:
        [list] -- [description]
    """
    ratios = []
    if sgmts == -1:
        print('Segmentation Failed')
        return -1
    for segment in sgmts:
        x1,y1,x2,y2 = segment
        ratios.append((y2-y1)/(x2-x1))    
    assert len(ratios) == len(sgmts),"Length does not match"
    target = np.zeros_like(ratios)
    if percen > 0: 
        target[np.array(ratios) > np.percentile(ratios,percen) ] =  1
    else: #take any increase or decrease (mainly used for mode to record the increase and decrease)
         target[np.array(ratios) != 0] =  1
    
    return ratios,target

def plot_segments_signal(sr,sgmts,target = None,title='',marker='r*-'):
    for i,sgmt in enumerate(sgmts):
        if target[i] == 1:
            x_points = [sgmt[0],sgmt[2]]
            y_points = [sgmt[1],sgmt[3]]
            plt.plot(x_points,y_points,marker)
    plt.title(title)

def high_mgfield_detect(list_prev_seg,list_post_seg):
    """detect high fluctuation in magnetic field according to a threshold,
       by checking the absolute difference between the slopes of the segments before and after
    
    Arguments:
        list_prev_seg {[list]} -- [list of segments before the event]
        list_post_seg {[list]} -- [list of segments after the event]
    """
    slope_prev_sg = []
    slope_post_sg = []
    for prev_sg in list_prev_seg:
        x1,y1,x2,y2 = prev_sg
        slope_prev_sg.append((y2+y1/2))
    
    for post_sg in list_post_seg:
        x1,y1,x2,y2 = post_sg
        slope_post_sg.append((y2+y1)/2)

    return ttest_ind(slope_prev_sg,slope_post_sg)


def signals_stat(d,files_list,dt):
    """statisitcs about the existance of the signals in the datalogs
    
    Arguments:
        d {[type]} -- [dictionary with comp as keys and comp columns as values in a list]
        e.g.
        d = {'RCOU':['Ch1','Ch2','Ch3','Ch4'],
        'RCIN':['C3','C4'],
        'MAG':['MagX','MagY','MagZ'],
        'CTUN':['ThrOut'],
        'GPS':['Alt'],
        'ATT':['Yaw','DesYaw'],
        'MODE':['ModeNum']
            }
        files_list {[type]} -- [description]
        dt {[Dataloader instalce]} -- [description]
    
    Returns:
        [dataframe] -- 
    """
    res_dt  = {}
    num_sig = len(d.keys())
    for i,filename in enumerate(files_list):
        l_res = [1]*num_sig
        if i % 100  == 0:
              print(i)
        for idx,(comp,sig) in enumerate(d.items()):
                df = pd.DataFrame(dt.dbconnector.query(comp+'_'+filename))
                if len(df) <= 0 : #comp does not exist
                    l_res[idx] = np.nan
                    break
                else: 
                    for signal_col in sig: #check if all signals exist in the dataframe
                        if not signal_col in df.columns:
                            l_res[idx] = np.nan
                            
        res_dt [filename] = l_res
    resdf = pd.DataFrame(res_dt).T
    resdf.columns = list(d.keys())
    return resdf


def get_yaw_event(file_detect,dt,unwrap_thresh=280,undes_thresh=70):
    """get the first segment where we detect an uncontrolled yaw value
    
    Arguments:
        file_detect {[string]} -- [description]
    
    Keyword Arguments:
        unwrap_thresh {int} -- [description] (default: {280})
        undes_thresh {int} -- [description] (default: {70})
    Return:
        dataframe -- yaw dataframe 
        int -- lineindex value where the event occured
    """

    df = pd.DataFrame(dt.dbconnector.query('ATT'+'_'+ file_detect))
    df['Yaw'] = np.unwrap(df['Yaw'],280)
    df['DesYaw'] = np.unwrap(df['DesYaw'],280)
    bool_res = abs(df['Yaw'] - df['DesYaw']) > undes_thresh #Detection RULE
    for i,b in enumerate(bool_res):
        if b == True:
            line_idx_pos = df.iloc[i,-1] #line index number of when the event started
            return df,line_idx_pos
    return -1 #no event occured 

def get_targets(sgmts,line_idx_pos,lower_window=20,upper_window=20):


    """find the segment where the value line_idx_pos is contained in.

    Arguments:
        line_idx_pos {int} -- position where an event had occured and we wish to find on the signal
    
    Returns:
        [list of integers] -- [list of 0's and 1's]
    """
    #ratios ,_  = idx_segments_threshold(sig,sgmts) #might be used with something else
    target = np.zeros(len(sgmts))
    for sg_idx , sg in enumerate(sgmts):
            if (line_idx_pos >= sg[0] - lower_window ) and ( line_idx_pos  <= sg[2] + upper_window):
                target[sg_idx] = 1 
                #break #look at more than one segment
    return target

#plotting the signals and segmenting
def plot_sig_lineidx(comp,sig,dt,line_idx_pos,file,err=2,lower_window=100):
    plt.figure(figsize=(10,8))
    if comp =='MODE':
        d = corr_var(file,dt,{'MODE':['ModeNum'],'ATT':['DesYaw']},find_corr=False)[['MODE_ModeNum']]
        d.columns = [sig]
        d = d.reset_index()
    else:
        d = pd.DataFrame(dt.dbconnector.query(comp+'_'+file))
        if len(d) <= 0 :
            print(f'{comp}_{sig} do not exist.')
            return -1
    sig_val  = d[sig]
    sgm = map_axis(d,segment_signal(sig_val,err))
    target = get_targets(sgm,line_idx_pos)
    d = d.set_index('lineIndex')
    d[sig].plot()
    plot_segments_signal(sig_val,sgm,target = target,title=sig)
    plt.show()
    return sgm,d

def get_window_values(sig_df,line_idx,win=600):
    """
    filter the signal dataframe by the idx in the lineidex 
    and return a filtered dataframe
    """
    lower_win = max(0,line_idx - win)
    upper_win = min(np.max(sig_df['lineIndex']),line_idx + win)
    bool_idx = (sig_df['lineIndex'] >= lower_win) & (sig_df['lineIndex'] <= upper_win)
    return sig_df[bool_idx]

def test_signal(yawdf,causedf):
    aldf = align_index(yawdf, causedf)
    mxlag = 20
    while(True):
        try:
            pvalue = grangercausalitytests(np.array(aldf.dropna(
            )), maxlag=mxlag, addconst=True, verbose=False)[mxlag-1][0]['ssr_ftest'][1]
            print(f'Maxlag = {mxlag} ; pvalue = {pvalue}')
            return mxlag,pvalue
        except:
            print(f'Error in maxlag = {mxlag}')
            mxlag-=2
            if mxlag <= 0:
                break
    return -1,-1
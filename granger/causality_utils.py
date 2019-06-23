"""
This module contains utility methods used for segmentations and causality
"""
import pandas as pd
import numpy as np
import glob
import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from dtloader.dataloader import DataLoader
from segmentation.segmentation import *
from utils.utils import *
from utils.features_eng import *
from granger.grangercausality_cl import GrangerCausalityDiscrete

def signal_comp_va(signal_name):
    return  signal_name[:signal_name.index('_')],signal_name[signal_name.index('_')+1:]

def ft_eg(signal_name,sr,segmts,lag=5):
    """
    given a continuous series return a dataframe with added features
    methods are implemented in the file feature_eng.py in the utils directory
    """
    seg_ratio = segment_ratio(sr, segmts)
    seg_means = segment_mean(sr,segmts)
    seg_median = segment_median(sr,segmts)
    seg_ratio_perc = segment_ratio_outlier(seg_ratio)
    moving_avg_data = moving_average_window(sr, 10)
    lagged_segments = lagged_segment(sr, segmts) #lagged segment ratios
    lagged_percentile = seg_ratio_perc.shift(lag).fillna(method='bfill')
    
    lagged_seg_means = seg_means.shift(lag).fillna(method='bfill')
    lagged_seg_median = seg_median.shift(lag).fillna(method='bfill')
    lagged_mov_avg = moving_avg_data.shift(lag).fillna(method='bfill')
    
    dataset = pd.DataFrame()
    #dataset['seg_ratio'] = seg_ratio
    #dataset['seg_ratio_percentile'] = seg_ratio_perc
    dataset[signal_name+'_lagged_moving_avg'] = lagged_mov_avg
    #dataset[signal_name+'_lagged_segments'] = lagged_segments
    dataset[signal_name+'_lagged_perc'] = lagged_percentile
    dataset[signal_name+'_lagged_means'] = lagged_seg_means
    dataset[signal_name+'_lagged_medians'] = lagged_seg_median
    return dataset

def segment_signal(sr):
    """
    return a segment list of the signal
    """
    m = np.mean(sr)
    sg = Segmentation(1)
    fitmethod= 'inter'
    sgmethod = 'td'
    try:
        #preprocessing.scale(sr)
        segments = sg.segment(sr,seg_method=sgmethod,fit_method=fitmethod,err_growth=0,batch=True,batch_size=50)
    except:
        return -1
    
    return segments


def align_index(filename,comp_x,va_x,comp_z,va_z,dl):
    #aligning the time index of the two signals
    #---------------------------------------------------------------------------
    ts = {comp_x:[va_x],comp_z:[va_z]}
    dft = corr_var(filename,dl,ts,find_corr=False)
    dft.reset_index(inplace=True)
    dft.drop('lineIndex',axis=1,inplace=True)
    dft.dropna(axis=0,how='any',inplace=True) #remove nans
    dft.index = range(len(dft))
    #for variables with the same keys we add the other manaully    
    #to be fixed later
    if len(dft.columns) == 1:
        #same key case - add the other to the dataframe
        dft[comp_x+'_'+va_x] = dl.dbconnector.query(comp_x+'_'+filename,va_x)
    if va_z in 'DesYaw':
        dft[comp_z+'_'+va_z] = yawfix(dft[comp_z+'_'+va_z])
    if va_x in 'DesYaw':
        dft[comp_x+'_'+va_x] = yawfix(dft[comp_x+'_'+va_x])
    return dft

def causality_cls_preprocess(x,y,z,filename,lag,dl):
    """
    preprocess data to put it in the write form for granger test using classification

    :param filename : log file to process
    :param lag: lag value for features 

    """
    # segmenting signals
    # not loading from database to test different segments with max error and batch sizes
    # ------------------------------------------------------------------------------------
    
    comp_x, va_x = signal_comp_va(x)
    comp_y, va_y = signal_comp_va(y)
    comp_z, va_z = signal_comp_va(z)
    
    # align time index between two files
    dft = align_index(filename, comp_x, va_x, comp_z, va_z,dl)
    dft_y = align_index(filename, comp_y, va_y, comp_z, va_z,dl)

    
    # segment x
   
    seg_x = segment_signal(dft[comp_x+'_'+va_x])
    # segment y
    
    seg_y = segment_signal(dft_y[comp_y+'_'+va_y])

    # segment z
    
    seg_z  = segment_signal(dft[comp_z+'_'+va_z])
    if seg_x == -1 or seg_y == -1 or seg_z == -1:
        return -1,-1,-1,-1,-1,-1,-1,-1,-1
    

    # datasets containing the features for predictions
    # Adding features
    # ---------------------------------------------------------------------------
    dataset_x = ft_eg(comp_x+'_'+va_x, dft[comp_x+'_'+va_x], seg_x, lag=lag)
    dataset_y = ft_eg(comp_y+'_'+va_y, dft_y[comp_y+'_'+va_y], seg_y, lag=lag)
    dataset_z = ft_eg(comp_z+'_'+va_z, dft[comp_z+'_'+va_z], seg_z, lag=lag)

    # Building the target variable for z
    # ---------------------------------------------------------------------------
    seg_ratio_z = segment_ratio(dft[comp_z+'_'+va_z], seg_z)
    target = np.zeros_like(seg_ratio_z)
    target[seg_ratio_z > np.percentile(seg_ratio_z,91)] =  1
    
    #if another variable was used the segments will not be equal to the lineindex concat so another must be constructed
    seg_ratio_z = segment_ratio(dft_y[comp_z+'_'+va_z], seg_z)
    target_y = np.zeros_like(seg_ratio_z)
    target_y[seg_ratio_z > np.percentile(seg_ratio_z,91)] =  1

    # combining features for full model
    # ---------------------------------------------------------------------------
    dataset_combined_xz = pd.concat([dataset_x, dataset_z], axis=1).dropna()
    dataset_combined_yz = pd.concat([dataset_y, dataset_z], axis=1).dropna()
    return dft, dft_y, dataset_x, dataset_y, dataset_z, dataset_combined_xz, dataset_combined_yz, target,target_y


def test_causality(df, comp_x, va_x, dataset_red, dataset_combined, comp_z, va_z, target,cv):
    l = ['nb', 'dt', 'knn', 'lr']
    gcl = GrangerCausalityDiscrete(
        names=[comp_x+'_'+va_x, comp_x+' +' + comp_z])
    dict_cls = {}
    for cls in l:
        res = gcl.test(df[comp_x+'_'+va_x], df[comp_z+'_'+va_z], dataset_red, dataset_combined, target, check_stationary=False,
                       classifier=cls, verbose=False, cv=cv)
        dict_cls[cls] = {'Mean-Acc-Full': gcl.mean_full,
                         'Mean-Acc-Reduced': gcl.mean_reduced, 'P-Value': gcl.pvalue}
    return dict_cls
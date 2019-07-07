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

def segment_signal(sr):
    """
    return a segment list of the signal
    """
    sg = Segmentation(np.mean(sr))
    fitmethod= 'inter'
    sgmethod = 'td'
    try:
        segments = sg.segment(sr,seg_method=sgmethod,fit_method=fitmethod,err_growth=0.02,batch=False,batch_size=50)
    except:
        print('Error')
        return -1
    return segments

def idx_segments_threshold(df_sg,sgmts,percen=92):
    ratios = []
    for segment in sgmts:
        x1,y1,x2,y2 = segment
        ratios.append((y2-y1))    
    assert len(ratios) == len(sgmts),"Length does not match"
    target = np.zeros_like(ratios)
    if percen > 0: 
        target[np.array(ratios) > np.percentile(ratios,percen) ] =  1
    else: #take any increase or decrease (mainly used for mode to record the increase and decrease)
         target[np.array(ratios) != 0] =  1
    
    return ratios,target

def plot_segments_signal(sr,sgmts,target = None,title=''):
    plt.figure()
    plt.plot(sr)
    sg = Segmentation(1)
    sg.draw_segments_modified(highlight_idx=target,segments=sgmts)
    plt.title(title)
    plt.show()

#Method used to run the code through the entire dataset and store the information in a dict which
#later analyzed to get the statistics
#plots and results are in the jupyter notebook in this file
def p4_analyze():
    """The method extract , segments , filter by threshold and returns the potentioanl causes for DesYaw signal ,
    by checking user input and rcout

    
    Returns:
        [dict] -- [dict containing the information on the causes]
    """
    dt = DataLoader()
    datalist =os.listdir('../data')
    comp = 'ATT'
    bicausal_dt = {}
    counter_events = 0
    #np.array(datalist)[np.random.choice(len(datalist), 100)]
    for i,log in enumerate(['577668e2d959285826b1e718.log']):
        print('File:{} --  {} / {}'.format(log,i,len(datalist)-1))
        filename = log[:-4]

        #DESYAW
        df = pd.DataFrame(dt.dbconnector.query(comp+'_'+filename))

        #RCOUT
        df_rcout = pd.DataFrame(dt.dbconnector.query('RCOU'+'_'+filename))
        if len(df_rcout) < 10 :
            continue
        #RCIN    
        df_rcin = pd.DataFrame(dt.dbconnector.query('RCIN'+'_'+filename))
        if len(df_rcin) < 10 :
            continue

        try:            
            sr_mode = corr_var(filename,dt,{'MODE':['ModeNum'],'ATT':['DesYaw']},find_corr=False).reset_index()['MODE_ModeNum']
        except:
            continue
        if isinstance(sr_mode,int):
            continue
    
        try:
            df_rcout['total_out'] = df_rcout['Ch1'] +  df_rcout['Ch2'] - (df_rcout['Ch4'] +  df_rcout['Ch3'])
        except: #Required channels not found
            continue

        #fixing the yaw
        df['Yaw'] = yawfix(df['Yaw'])
        df['DesYaw'] = yawfix(df['DesYaw'])
        #segment all three signals
        print('Segmenting...')
        sgmts_desyaw = segment_signal(df['DesYaw'])
        sgmts_totalout = segment_signal(df_rcout['total_out'])
        sgmts_rcin = segment_signal(df_rcin['C4'])
        sgmts_mode = segment_signal(sr_mode)
        
        if isinstance(sgmts_desyaw,int) or isinstance(sgmts_totalout,int) or isinstance(sgmts_rcin,int) or  isinstance(sgmts_mode,int):
            continue

        ratios_desyaw ,target_desyaw  = idx_segments_threshold(df['DesYaw'],sgmts_desyaw)
        ratios_totalout,target_totalout  = idx_segments_threshold( df_rcout['total_out'] ,sgmts_totalout)
        ratios_rcin,target_rcin  = idx_segments_threshold(df_rcin['C4'],sgmts_rcin)
        ratios_mode,target_mode  = idx_segments_threshold(sr_mode,sgmts_mode,0)

        #Extracting segments were ratio threshold match
        seg_inc_totalout = np.array(sgmts_totalout)[target_totalout == 1]
        seg_inc_rcin = np.array(sgmts_rcin)[target_rcin == 1]
        seg_inc_desyaw = np.array(sgmts_desyaw)[target_desyaw == 1]
        seg_inc_mode = np.array(sgmts_mode)[target_mode == 1]

        print('Checking Events...')
        #Looping through the events (DesYaw Segments)
        bicausal_dt[filename] = {}
        if  i  < 30:
            plot_segments_signal(df['DesYaw'],sgmts_desyaw,target = target_desyaw,title='DesYaw')
            plot_segments_signal(df_rcout['total_out'],sgmts_totalout,target = target_totalout,title='RCOU')
            plot_segments_signal(df_rcin['C4'],sgmts_rcin,target = target_rcin,title='RCIN_C4')
            plot_segments_signal(sr_mode,sgmts_mode,target = target_mode,title='MODE')
        for seg_desyaw in seg_inc_desyaw:
            counter_events+=1
            event_num = 'event' + str(counter_events)
        
            #[0,0,0,x1,x2] first zero for user, second for controller, mode , event_start,event_end
            init_res_list = [0,0,0,seg_desyaw[0],seg_desyaw[2]]  
            #creating a window for the interval (sometimes it takes some x's for the result to show)
            lower_window = seg_desyaw[0]
            if seg_desyaw[0] >= 50:
                lower_window = seg_desyaw[0] - 50 
            upper_window = seg_desyaw[2] + 50
        
            #check if rcin and total_out segments are in the interval of the event
            #for each segment in rcin
            for seg_rcin in seg_inc_rcin:
                if (seg_rcin[0] >= lower_window) and (seg_rcin[2] <= upper_window):
                    init_res_list[0] = 1
                    break #dont check more segments (performance)
            
            #for each segment in totalout
            for seg_totout in seg_inc_totalout:
                if (seg_totout[0] >= lower_window) and (seg_totout[2] <= upper_window):
                    init_res_list[1] = 1
                    break #dont check more segments (performance)
            
            for seg_mode in seg_inc_mode:
                if (seg_mode[0] >= lower_window) and (seg_mode[2] <= upper_window):
                    init_res_list[2] = 1
                    break #dont check more segments (performance)
            
            #add the event with the results
            bicausal_dt[filename][event_num] = init_res_list
            print('Dictionary Updated.')

    # plot_segments_signal(df['DesYaw'],sgmts_desyaw,target = target_desyaw,title='DesYaw')
    # plot_segments_signal(df_rcout['total_out'],sgmts_totalout,target = target_totalout,title='RCOU')
    # plot_segments_signal(df_rcin['C4'],sgmts_rcin,target = target_rcin,title='RCIN_C4')
    return bicausal_dt    
import numpy as np
from numpy.linalg import lstsq
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from .segment import *
import pandas as pd
import os
import sys
from scipy.stats import linregress

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from utils.utils import *

class Segmentation():
    """Segmentation module providing methods to segment a time series sequence based 
        of different algorithms 
    """

    def __init__(self,max_error):
        """Segmentation init
        
        Arguments:
            max_error {numeric} -- max error threshold for a segment creation
        
        Keyword Arguments:
            seq_list {list} -- list of values (default: {None})
        """
        self.max_error = max_error
        self.segment_list = []  #a list of segment instances


    def segment(self,sequence,seg_method ='sw' ,fit_method='ls',err_method='ssr',seq_range=None,save_seginstance=False,err_growth=0,batch=True,batch_size=None):
        """Return a list of line segments that approximate the sequence.
        
        Arguments:
            sequence {[list]} -- numeric least of numeric values that represent a time series 
        
        Keyword Arguments:
            method {str} -- [fitting method] (default: {'ls'})
            err_method {str} -- [error computation method] (default: {'ssr'})
            seq_range {[list]} -- [index list for the given time series list] (default: {None})
        """
        self.sequence = sequence
        
        if  not seq_range :
            self.seq_range = (0, len(self.sequence) - 1)
        else:
            self.seq_range = seq_range
        
        #line fit method
        if fit_method == 'ls':
            self.fit_sequence = self.regression
        
        elif fit_method == 'inter':
            self.fit_sequence = self.interpolate
        else:
            print('Fittin Method not available')
            return -1

        #error computation method
        if err_method == 'ssr':
            self.compute_error = self.sumsquared_error
        elif err_method == 'rsq':
            if self.max_error > 1:
                print('Please use a max error between 0 and 1')
            self.compute_error = self.rsquared_comp
        else:
            print('Compute Error Method not available')
            return -1

        #segmentation method
        if seg_method == 'sw':
            self.segments = self.slidingwindowsegment(self.fit_sequence,self.compute_error,seq_range=self.seq_range)
        elif seg_method == 'td':
            self.segments = self.topdownsegment(self.fit_sequence, self.compute_error,self.seq_range,self.max_error,err_growth,batch=batch,batch_size=batch_size)
        elif seg_method == 'bu':
            self.segments = self.bottomupsegment(self.fit_sequence, self.compute_error,seq_range=self.seq_range)
        else:
            print('Segmentation method not available')
            return -1
        
        #populate segments list
        if isinstance(self.segments,int):
            return -1
        if save_seginstance:
            for segment in self.segments:
                self.segment_list.append(Segment(segment[0],segment[1],segment[2],segment[3]))
        else:  #save as a list of tuples (x0,y0,x1,y1)
            for segment in self.segments:
                self.segment_list.append((segment[0],segment[1],segment[2],segment[3]))
        return self.segment_list

    def slidingwindowsegment(self,fit_sequence, compute_error,seq_range):
        """
        Return a list of line segments that approximate the sequence.
        The list is computed using the sliding window technique.
        Parameters
        ----------
        sequence : sequence to segment
        fit_sequence : a function of two arguments (sequence, sequence range) that returns a line segment that approximates the sequence data in the specified range
        compute_error: a function of two argments (sequence, segment) that returns the error from fitting the specified line segment to the sequence data
        max_error: the maximum allowable line segment fitting error
        """
        start = seq_range[0]
        end = start
        result_segment = fit_sequence((seq_range[0], seq_range[1]))
        while end < seq_range[1]:
            end += 1
            test_segment = fit_sequence( (start, end)) #(x0,y0,x1,y1)
            error = compute_error(test_segment)
            if error <= self.max_error:
                result_segment = test_segment
            else:
                break
        if end == seq_range[1]:
            return [result_segment]
        else:
             return [result_segment] + self.slidingwindowsegment(fit_sequence, compute_error,
                                                       (end - 1, seq_range[1]))


    def bottomupsegment(self,fit_sequence, compute_error,seq_range):
        """
        Return a list of line segments that approximate the sequence.

        The list is computed using the bottom-up technique.

        Parameters
        ----------
        self.sequence : self.sequence to segment
        fit_sequence : a function of two arguments (self.sequence, self.sequence range) that returns a line segment that approximates the self.sequence data in the specified range
        compute_error: a function of two argments (self.sequence, segment) that returns the error from fitting the specified line segment to the self.sequence data
        max_error: the maximum allowable line segment fitting error

        """
        segments = [fit_sequence(seq_range) for seq_range in zip(range(len(self.sequence))[:-1], range(len(self.sequence))[1:])]
        mergesegments = [fit_sequence( (seg1[0], seg2[2])) for seg1, seg2 in zip(segments[:-1], segments[1:])]
        mergecosts = [compute_error( segment) for segment in mergesegments]
        try:
            while min(mergecosts) < self.max_error:
                idx = mergecosts.index(min(mergecosts))
                segments[idx] = mergesegments[idx]
                del segments[idx + 1]

                if idx > 0:
                    mergesegments[idx - 1] = fit_sequence((segments[idx - 1][0], segments[idx][2]))
                    mergecosts[idx - 1] = compute_error(mergesegments[idx - 1])

                if idx + 1 < len(mergecosts):
                    mergesegments[idx + 1] = fit_sequence((segments[idx][0], segments[idx + 1][2]))
                    mergecosts[idx + 1] = compute_error(mergesegments[idx])

                del mergesegments[idx]
                del mergecosts[idx]
                self.segments = segments
            return segments
        except:
            return -1


    def topdownsegment(self,fit_sequence, compute_error,seq_range,max_err,err_growth,batch,batch_size):
        """
        Return a list of line segments that approximate the sequence.

        The list is computed using the bottom-up technique.

        Parameters
        ----------
        sequence : sequence to segment
        create_segment : a function of two arguments (sequence, sequence range) that returns a line segment that approximates the sequence data in the specified range
        compute_error: a function of two argments (sequence, segment) that returns the error from fitting the specified line segment to the sequence data
        max_error: the maximum allowable line segment fitting error

        """
        if not seq_range:
            seq_range = (0, len(self.sequence) - 1)

        bestlefterror, bestleftsegment = float('inf'), None
        bestrighterror, bestrightsegment = float('inf'), None
        bestidx = None
        step = 1
        if batch:
            step = batch_size
        for idx in np.arange(seq_range[0] + 1, seq_range[1],step):
            segment_left = fit_sequence( (seq_range[0], idx))
            error_left = compute_error(segment_left)
            segment_right = fit_sequence((idx, seq_range[1]))
            error_right = compute_error(segment_right)
            if error_left + error_right < bestlefterror + bestrighterror:
                bestlefterror, bestrighterror = error_left, error_right
                bestleftsegment, bestrightsegment = segment_left, segment_right
                bestidx = idx
        if bestlefterror <= max_err:
            leftsegs = [bestleftsegment]
        else:
            leftsegs = self.topdownsegment(fit_sequence,compute_error, (seq_range[0], bestidx),err_growth = err_growth,
                                         max_err = err_growth*max_err + max_err,batch=batch,batch_size=batch_size)                                    
        if bestrighterror <= max_err:
            rightsegs = [bestrightsegment]
        else:
             rightsegs = self.topdownsegment(fit_sequence,compute_error,(bestidx, seq_range[1]),err_growth=err_growth,
                                        max_err = err_growth*max_err + max_err,batch=batch,batch_size=batch_size)
        
        self.segments = leftsegs + rightsegs
        return self.segments

    def interpolate(self,seq_range):
        """Return (x0,y0,x1,y1) of a line fit to a segment using a simple interpolation"""
        #not implemented
        return (seq_range[0], self.sequence[seq_range[0]], seq_range[1], self.sequence[seq_range[1]])


    def regression(self,seq_range):
        """Return (x0,y0,x1,y1) of a line fit to a segment of a sequence using linear regression"""
        p, _ = self.leastsquareslinefit(seq_range)
        fit_y = p[0] * np.array(seq_range) + p[1]
        #(x0,y0,x1,y1)
        return (seq_range[0], fit_y[0], seq_range[1], fit_y[1])


    def sumsquared_error(self,fit_segment):
        """Return the sum of squared errors for a least squares line fit of one segment of a sequence"""
        x0,y0,x1,y1= fit_segment #result of regression
        _, error = self.leastsquareslinefit((x0, x1))
        return error

    
    def rsquared_comp(self,fit_segment):
        x0,y0,x1,y1= fit_segment #result of regression
        slope, intercept, r_value, p_value, std_err  = self.lrg((x0, x1))
        val = r_value**2
        return val
    
    def lrg(self,seq_range):
        start = seq_range[0]
        end = seq_range[1]+1
        x = np.arange(start,end)
        y = np.array(self.sequence[start:end])
        return linregress(x,y)


    def leastsquareslinefit(self,seq_range):
        """Return the parameters and error for a least squares line fit of one segment of a sequence"""
        start = seq_range[0]
        end = seq_range[1]+1
        x = np.arange(start,end)
        y = np.array(self.sequence[start:end])
        A = np.vstack([x, np.ones(len(x))]).T
        (p,residuals,_,_) = lstsq(A,y)
        try:
            error = residuals[0]
        except IndexError:
            error = 0.0
        return (p,error)

    def draw_plot(self,plot_title,label=None,xrange=None):
        """plots the current sequence of data
        
        Arguments:
            plot_title {[str]} -- plot title
        """
        if xrange is None:
            xrange = range(len(self.sequence))
        plt.plot(xrange,self.sequence,alpha=0.8,color='black',label=plot_title+' real')
        plt.title(plot_title)
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.xlim((0,len(self.sequence)-1))
        plt.legend()

    def find_maxratio(self):
        ratio_list = []
        for segment in self.segments:
            clc_val = calc_segmentsRation(segment[0],segment[1],segment[2],segment[3])
            ratio_list.append(clc_val)
        return ratio_list,np.argmax(np.array(ratio_list))
        
    def draw_segments(self,highlight_idx = None,segments=None):
        """plot fitted segments
        
        Arguments:
            segments {[list]} -- tuples representing the line coordinates 
        """
        ax = plt.gca()
        if segments is None:
            segments = self.segments
        for i,segment in enumerate(segments):
            clr = 'blue'
            x1,y1,x2,y2 = segment
            if 1 in  highlight_idx[x1:x2]:
                clr = 'red'
            line = Line2D((segment[0],segment[2]),(segment[1],segment[3]),color=clr)
            ax.add_line(line)
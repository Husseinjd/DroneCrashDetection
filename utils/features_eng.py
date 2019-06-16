"""This module contains methods used for Feature engineering
"""
import os
import numpy as np
import pandas as pd


def segment_ratio(series, segments):
    """
    :param series: raw data series
    :param segments: segments list
    :return: a series of the length of raw series with ratio values of the respective segment
    """
    ratio_series = series.copy(deep = True)
    for segment in segments:
        x1,y1,x2,y2 = segment
        ratio = (y2-y1)/(x2-x1)
        ratio_series[x1:x2] = ratio
    return ratio_series


def segment_mean(series,segments):
    mean_series = series.copy(deep = True)
    for segment in segments:
        x1,_,x2,_ = segment
        mean = np.mean(series[x1:x2])
        mean_series[x1:x2] = mean
    return mean_series

def segment_median(series,segments):
    median_series = series.copy(deep = True)
    for segment in segments:
        x1,_,x2,_ = segment
        median = np.median(series[x1:x2])
        median_series[x1:x2] = median
    return median_series

def segment_ratio_outlier(ratio_series):
    """

    :param ratio_series: the ratio series (from segment_ratio function)
    :return: the percentile value of each ratio. The high and low values will be useful in detecting specific events
    """
    return ratio_series.rank(pct = True)

def moving_average_window(series, window_size):
    """

    :param series: The series whos moving window average needs to be calculated
    :param window_size: sinze of window
    :return: average as per the moving window for each value
    """
    return series.rolling(window_size, min_periods=1).mean()

def event_finder(seg_ratio, threshold, greater_or_lesser = "greater"):
    """

    :param seg_ratio: series containing segmentation ratio
    :param threshold: threshold value above or below which we classify an event
    :param greater_or_lesser: check of greater than or less than the threshold
    :return: series of True or False based on where event occurred
    """
    if greater_or_lesser == "greater":
        event_occurred = np.where(seg_ratio > threshold, True, False)
    elif greater_or_lesser == "lesser":
        event_occurred = np.where(seg_ratio < threshold, True, False)
    else:
        raise ValueError('Invalid value supplied to greater_or_lesser parameter')

    return event_occurred

def lagged_segment(series, segments):
    """
    :param series: the raw data series
    :param segments: segments list
    :return: a series where previous segmentation ratio is associated with current value
    """
    lagged_series = series.copy(deep=True)
    prev_x1 , prev_y1 , prev_x2, prev_y2 = segments[0]
    lagged_series[prev_x1:prev_x2] = 0
    for segment in segments[1:]:
        x1, y1, x2, y2 = segment
        lagged_series[x1:x2] = (prev_y2 - prev_y1) / (prev_x2 - prev_x1)
        prev_y1 = y1
        prev_y2 = y2
        prev_x1 = x1
        prev_x2 = x2
    return lagged_series

"""
This module contains helper functions that are used
in the analysis
"""
import numpy as np
import pandas as pd

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

import os
import sys
import time
import datetime
import argparse
import re
from pathlib import Path
from tqdm import tqdm
from copy import deepcopy, copy
import traceback
import json

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib_venn import venn2
try:
    import japanize_matplotlib
except:
    print('japanize_matplotlib not found.')
import seaborn as sns
from scipy.stats import ks_2samp

import warnings

from .preprocessing import CatEncoder


def KS_test(train, test, plot_rejected=False, plot_accepted=False, thres=0.05):
    '''
    Kolmogorov-Smirnov test
    '''
    assert isinstance(train, pd.DataFrame)
    assert type(train) == type(test)

    h0_accepted = []
    h0_rejected = []

    for col in test.columns:
        d, p = ks_2samp(train[col], test[col])

        if p >= thres:
            h0_accepted.append(col)
            if plot_accepted:
                plt.figure(figsize=(6, 3))
                plt.title("Kolmogorov-Smirnov test\n"
                          "feature: {}, statistics: {:.5f}, pvalue: {:5f}".format(col, d, p))
                sns.kdeplot(train[col], color='blue',
                            shade=True, label='Train')
                sns.kdeplot(test[col], color='green', shade=True, label='Test')
                plt.show()
        else:  # pvalue < thres
            h0_rejected.append(col)
            if plot_rejected:
                plt.figure(figsize=(6, 3))
                plt.title("Kolmogorov-Smirnov test\n"
                          "feature: {}, statistics: {:.5f}, pvalue: {:5f}".format(col, d, p))
                sns.kdeplot(train[col], color='blue',
                            shade=True, label='Train')
                sns.kdeplot(test[col], color='green', shade=True, label='Test')
                plt.show()

    return h0_accepted, h0_rejected


def train_test_venn(train, test):
    if not isinstance(train, set):
        train = set(train)
    if not isinstance(test, set):
        test = set(test)
    common_val = train & test
    train_val = train - common_val
    test_val = test - common_val
    return venn2(subsets=(
        len(train_val), 
        len(test_val),
        len(common_val),
        ),
        set_labels=('train', 'test')
    )


def is_categorical(x, count=10):
    if len(np.unique(x)) <= count:
        return True
    else:
        return False


def not_null(x):
    return x[x==x]
    

def explore_dataframe(train, test=None, categorical_threshold=10):
    assert isinstance(train, pd.DataFrame)
    if test is not None:
        assert isinstance(test, pd.DataFrame)
    catenc = CatEncoder('label', handle_missing='return_nan', handle_unknown='value')

    train_columns = set(train.columns)
    print(f'train shape:\t{train.shape}')
    print(f'train columns:\n{sorted(train_columns)}({len(train_columns)})')
    target_columns = train_columns
    if test is not None:
        test_columns = set(test.columns)
        print(f'test shape:\t{test.shape}')
        print(f'test columns:\n{sorted(test_columns)}({len(test_columns)})')
        common_columns = train_columns & test_columns
        print(f'common columns:\n{sorted(common_columns)}({len(common_columns)})')
        target_columns = common_columns

    for icol, col in enumerate(target_columns):
        res_str = f'\n[{icol}/{col}]: {train[col].dtype}\n'
        
        train_vals = train[col].values.copy()
        train_null = train_vals != train_vals
        res_str += f'train_null: {np.sum(train_null)}({np.mean(train_null)*100:.2f}%)\n'
        if test is not None:
            test_vals = test[col].values.copy()
            test_null = test_vals != test_vals
            res_str += f'test_null: {np.sum(test_null)}({np.mean(test_null)*100:.2f}%)\n'
        
        try:
            if is_categorical(train_vals, categorical_threshold):
                train_vals = catenc.fit_transform(train_vals)
                res_str += 'is categorical'
                if test is not None:
                    fig_len = 2
                    plt.figure(figsize=(6, fig_len*3))
                    test_vals = catenc.transform(test_vals)
                    plt.subplot(fig_len, 1, 1)
                    plt.title(res_str)
                    train_test_venn(np.unique(train_vals), np.unique(test_vals))
                else:
                    fig_len = 1
                    plt.figure(figsize=(6, fig_len*3))
                    plt.subplot(fig_len, 1, 1)
                    plt.title(res_str)
            else:
                fig_len = 1
                plt.subplot(fig_len, 1, 1)
                plt.title(res_str)

            plt.subplot(fig_len, 1, fig_len)
            sns.distplot(train_vals[~train_null], kde=False, norm_hist=True, label='train')
            if test is not None:
                sns.distplot(test_vals[~test_null], kde=False, norm_hist=True, label='test')
            plt.legend()
            plt.show()
        except:
            res_str += 'Error Occured'
            print(res_str)
        
        
        


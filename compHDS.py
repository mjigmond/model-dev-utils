# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 19:07:32 2017

Comparison of model simulated heads across two models

@author: mjigmond
"""

import numpy as np
import os
import arcpy as arc
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle

mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['font.size'] = 10

def func(x, pos):
    return '{:,d}'.format(int(x))

def plotDiff(hList=None, kper=None, qlrc=None):
    '''Plot the full extent of the xsect'''
    hds = np.zeros((len(hList), nnod))
    fSize = os.path.getsize(hList[0])
    ofst = 0
    while ofst < fSize:
        h = np.empty(0)
        for i, n in enumerate(nodes):
            dt = np.dtype([
                ('kstp', 'i4'),
                ('kper', 'i4'),
                ('pertim', 'f4'),
                ('totim', 'f4'),
                ('text', 'S16'),
                ('nstrt', 'i4'),
                ('nndlay', 'i4'),
                ('ilay', 'i4'),
                ('data', 'f4', n)
            ])
            hdsarr = np.memmap(hList[0],
                                dtype=dt,
                                mode='r',
                                offset=ofst,
                                shape=1)[0]
            ofst += dt.itemsize
            h = np.concatenate((h, hdsarr['data']))
        if hdsarr['kper'] == kper:
            hds[0,:] = h[:]
        elif hdsarr['kper'] > kper:
            break
    fSize = os.path.getsize(hList[1])
    ofst = 0
    nn, ll, rr, cc = zip(*qlrc)
    while ofst < fSize:
        dt = np.dtype([
            ('kstp', 'i4'),
            ('kper', 'i4'),
            ('pertim', 'f4'),
            ('totim', 'f4'),
            ('desc', 'S16'),
            ('ncol', 'i4'),
            ('nrow', 'i4'),
            ('ilay', 'i4'),
            ('rec', 'f4', (nrow, ncol))
        ])
        hdsarr = np.memmap(hList[1],
                            dtype=dt,
                            mode='r',
                            offset=ofst,
                            shape=nlay)
        ofst += dt.itemsize*nlay
        if hdsarr['kper'][0] == kper:
            hds[1,:] = hdsarr['rec'][list(ll),list(rr),list(cc)]
        elif hdsarr['kper'][0] > kper:
            break
    if kper == 1:
        flds = ['node','MF96_1975','USG_1975','DIFF_1975']
    elif kper == 26:
        flds = ['node','MF96_2000','USG_2000','DIFF_2000']
    with arc.da.UpdateCursor('gis/shp/qcspc_usg_hds_comp.shp', flds) as uc:
        for r in uc:
            r[1]  = hds[1,r[0]-1]
            r[2]  = hds[0,r[0]-1]
            if hds[1,r[0]-1] < 99999:
                r[3] = hds[1,r[0]-1]-hds[0,r[0]-1]
            else:
                r[3] = 99999
            uc.updateRow(r)

    for i, n in enumerate(cs):
        fig, ax = plt.subplots(figsize = (4, 4))
        fig.subplots_adjust(left=.19, right=.95, bottom=.12, top=.92)
        ax.grid()
        nstrt, nend = 0, n
        if i > 0:
            nstrt, nend = cs[i-1], n
        ax.plot(
            np.ma.masked_values(hds[1],99999)[nstrt:nend],
            hds[0][nstrt:nend],
            ls='None', marker='o', ms=2, mfc='b', mec='b'
        )
        ax.plot([-300, 700], [-300, 700], c='r', ls='--')
        ax.set_xlabel('Hydraulic head simulated by MODFLOW 96 [feet msl]', fontsize=8)
        ax.set_ylabel('Hydraulic head simulated by MODFLOW-USG [feet msl]', fontsize=8)
        ax.set_title('{} (Layer {}) - {}'.format(aq[i], i+1, kper+1974))
        plt.savefig('{}/scatter_lay{}_{}.png'.format(figDir, i+1, kper+1974), dpi=300)
        plt.close()

arc.env.overwriteOutput = 1

figDir = 'figures'
if not os.path.exists(figDir):
    os.mkdir(figDir)

nrow, ncol = 177, 273
aq = ['Sparta', 'Weches', 'Queen City', 'Reklaw', 'Carrizo', 'Calvert Bluff', 'Simsboro', 'Hooper']

with open('thirdParty/model.v2/v2.dis', 'r') as f:
    lines = f.readlines()
    ls = [int(x) for x in lines[0].split()]
    nnod, nlay, nja = ls[:3]
    nsp = ls[4]
    nodes = [int(x) for x in lines[3].split()]

cs = np.cumsum(nodes)

grid = 'gis/shp/qcspc_usg.shp'
arc.management.CopyFeatures(grid, 'gis/shp/qcspc_usg_hds_comp.shp')
arc.management.AddField('gis/shp/qcspc_usg_hds_comp.shp', 'MF96_1975', 'FLOAT')
arc.management.AddField('gis/shp/qcspc_usg_hds_comp.shp', 'USG_1975', 'FLOAT')
arc.management.AddField('gis/shp/qcspc_usg_hds_comp.shp', 'DIFF_1975', 'FLOAT')
arc.management.AddField('gis/shp/qcspc_usg_hds_comp.shp', 'MF96_2000', 'FLOAT')
arc.management.AddField('gis/shp/qcspc_usg_hds_comp.shp', 'USG_2000', 'FLOAT')
arc.management.AddField('gis/shp/qcspc_usg_hds_comp.shp', 'DIFF_2000', 'FLOAT')

grd = arc.da.FeatureClassToNumPyArray(grid, ['node','nlay','nrow','ncol'])
grd = np.sort(grd, order='node')
nlrc = zip(grd['node']-1,grd['nlay']-1, grd['nrow']-1,grd['ncol']-1)

hdsFiles = ['thirdParty/model.v2/v2.hds', 'gam/PS4run/qcsp_c_update.hds']
plotDiff(hdsFiles, 1, nlrc)

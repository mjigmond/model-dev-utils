# -*- coding: utf-8 -*-
"""
Created on Thu May 26 15:38:29 2016

Generate cross-sectional profiles (strike and dip) of aquifer properties

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
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm, LogNorm

mpl.rcParams['legend.fontsize'] = 8
mpl.rcParams['font.size'] = 8
mpl.rcParams['font.family'] = 'Trebuchet MS'

def func(x, pos):
    return '{:,d}'.format(int(x))

def plotPropFE(pDict=None, arr=None, lims=None, xmax=None, axt=None, direction=None, label=None, units=None, f=None):
    '''Plot the full extent of the xsect'''
    norm = LogNorm()
    fig, ax = plt.subplots(2, 3, figsize = (12, 6), squeeze=True)
    fig.suptitle('{} for {} Cross-sections'.format(label, direction), fontsize=10)
    for i, (k, v) in enumerate(sorted(pDict.items())):
        r, c = i//3, i%3
        ax[r,c].grid()
        pCol = PatchCollection(v[0])
        pCol.set_linewidth(.08)
        pCol.set_array(v[arr+1])
        pCol.set_clim(*lims)
        if label.lower() != 'sy':
            pCol.set_norm(norm)
        ax[r,c].set_title('{} {:3d}'.format(axt, k))
        ax[r,c].add_collection(pCol)
        ax[r,c].set_ylim(-12000, 1000)
        ax[r,c].yaxis.set_major_formatter(y_format)
        ax[r,c].set_xlim(0, xmax*5280)
        ax[r,c].set_xticks(np.linspace(0, xmax*5280, 5))
        if r == 1:
            ax[r,c].set_xticklabels(['{:.1f}'.format(x) for x in np.linspace(0, xmax, 5)])
            ax[r,c].set_xlabel('Distance (miles)')
        else:
            ax[r,c].set_xticklabels([])
        if c == 0:
            ax[r,c].set_ylabel('Elevation (feet)')
        else:
            ax[r,c].set_yticklabels([])
    fig.subplots_adjust(left=.08, right=.9, bottom=.08, top=.9, wspace=.1, hspace=.2)
    cbaxes = fig.add_axes([.91, 0.25, 0.03, 0.5])
    plt.colorbar(pCol, cax=cbaxes, orientation='vertical', label='{} [{}]'.format(label, units))
    plt.savefig(f, dpi=300)
    plt.close()

y_format = FuncFormatter(func)

figDir = 'figures'
if not os.path.exists(figDir): os.mkdir(figDir)
grid = 'gis/shp/qcspc_usg.shp'

nrow, ncol = 177, 273
rownum = 28
colnum = 40
lList = ['Kx', 'Vcont', 'S', 'Ss', 'Sy']
props = [x.lower() for x in lList]
uList = ['feet/day', r'day$^{-1}$', '', r'feet$^{-1}$', '']

patchDict = {}
llim, ulim = {x: 1e6 for x in props}, {x: 0 for x in props}
for col in range(colnum, colnum*6+1, colnum):
    patches = []
    sql = '''"ncol"={}'''.format(col)
    grd = arc.da.FeatureClassToNumPyArray(grid, ['node','nrow','top','bottom'] + props, sql)
    grd = np.sort(grd, order='node')
    for p in props:
        llim[p] = min(llim[p], grd[p].min())
        ulim[p] = max(ulim[p], grd[p].max())
    for g in grd:
        patches.append(Rectangle(((g[1]-1)*5280.,g[3]),5280.,g[2]-g[3]))
    patchDict[col] = (patches,) + tuple((grd[p] for p in props))

for i, (l, u) in enumerate(zip(lList, uList)):
    fn = '{}/dip_{}_gam'.format(figDir, props[i])
    plotPropFE(patchDict, i, (llim[props[i]], ulim[props[i]]), nrow, 'column', 'Dip', l, u, fn)

patchDict = {}
llim, ulim = {x: 1e6 for x in props}, {x: 0 for x in props}
for row in range(rownum, rownum*6+1, rownum):
    patches = []
    sql = '''"nrow"={}'''.format(row)
    grd = arc.da.FeatureClassToNumPyArray(grid, ['node','ncol','top','bottom'] + props, sql)
    grd = np.sort(grd, order='node')
    for p in props:
        llim[p] = min(llim[p], grd[p].min())
        ulim[p] = max(ulim[p], grd[p].max())
    for g in grd:
        patches.append(Rectangle(((g[1]-1)*5280.,g[3]),5280.,g[2]-g[3]))
    patchDict[row] = (patches,) + tuple((grd[p] for p in props))

for i, (l, u) in enumerate(zip(lList, uList)):
    fn = '{}/strike_{}_gam'.format(figDir, props[i])
    plotPropFE(patchDict, i, (llim[props[i]], ulim[props[i]]), ncol, 'row', 'Strike', l, u, fn)

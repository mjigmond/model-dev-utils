# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 11:08:14 2016

Plots of pumping tests under different simulation conditions

@author: mjigmond
"""

import numpy as np
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from dateutil.parser import parse as dp
from datetime import timedelta

font = {'family': 'Consolas'}
mpl.rc('font', **font)

cell = True

hdsFiles = [
    'thirdParty/pump.test.riv/v2.well049.cln.hds'
    ,'thirdParty/pump.test.riv/v2.well106.cln.hds'
    ,'thirdParty/pump.test.riv/v2.well049.cln.nohfb.hds'
    ,'thirdParty/pump.test.riv/v2.well106.cln.nohfb.hds'
    ,'thirdParty/pump.test.riv/v2.well049.cln.clh'
    ,'thirdParty/pump.test.riv/v2.well106.cln.clh'
    ,'thirdParty/pump.test.riv/v2.well049.cln.nohfb.clh'
    ,'thirdParty/pump.test.riv/v2.well106.cln.nohfb.clh'
]

with open('thirdParty/pump.test.riv/v2.dis', 'r') as f:
    lines = f.readlines()
    ls = [int(x) for x in lines[0].split()]
    nnod, nlay, nja = ls[:3]
    nsp = ls[4]
    nodes = [int(x) for x in lines[3].split()]

hds = {49: np.zeros((len(hdsFiles)/2, 37)), 106: np.zeros((len(hdsFiles)/2, 97))}
wnode = {49: 140861, 106: 142744}

fSize = os.path.getsize(hdsFiles[0])
ofst = 0
while ofst < fSize:
    h = np.zeros((len(hdsFiles)/4, nnod))
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
        for j in range(0, len(hdsFiles)/2, 2):
            hdsarr = np.memmap(hdsFiles[j],
                               dtype=dt,
                               mode='r',
                               offset=ofst,
                               shape=1)[0]
            ns, ne = hdsarr['nstrt'], hdsarr['nndlay']
            h[j//2, ns-1:ne] = hdsarr['data'].copy()
        ofst += dt.itemsize
    sp = hdsarr['kper']
    hds[49][:2, sp-1] = h[:, wnode[49]-1]

fSize = os.path.getsize(hdsFiles[4])
ofst = 0
while ofst < fSize:
    dt = np.dtype([
        ('kstp', 'i4'),
        ('kper', 'i4'),
        ('pertim', 'f4'),
        ('totim', 'f4'),
        ('text', 'S16'),
        ('nstrt', 'i4'),
        ('nndlay', 'i4'),
        ('ilay', 'i4'),
        ('data', 'f4', 1)
    ])
    for j in range(4, len(hdsFiles), 2):
        hdsarr = np.memmap(hdsFiles[j],
                           dtype=dt,
                           mode='r',
                           offset=ofst,
                           shape=1)[0]
        sp = hdsarr['kper']
        hds[49][j//2:, sp-1] = hdsarr['data'].copy()
    ofst += dt.itemsize

fSize = os.path.getsize(hdsFiles[1])
ofst = 0
while ofst < fSize:
    h = np.zeros((len(hdsFiles)/4, nnod))
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
        for j in range(1, len(hdsFiles)/2, 2):
            hdsarr = np.memmap(hdsFiles[j],
                               dtype=dt,
                               mode='r',
                               offset=ofst,
                               shape=1)[0]
            ns, ne = hdsarr['nstrt'], hdsarr['nndlay']
            h[(j-1)//2, ns-1:ne] = hdsarr['data'].copy()
        ofst += dt.itemsize
    sp = hdsarr['kper']
    hds[106][:2, sp-1] = h[:, wnode[106]-1]

fSize = os.path.getsize(hdsFiles[5])
ofst = 0
while ofst < fSize:
    dt = np.dtype([
        ('kstp', 'i4'),
        ('kper', 'i4'),
        ('pertim', 'f4'),
        ('totim', 'f4'),
        ('text', 'S16'),
        ('nstrt', 'i4'),
        ('nndlay', 'i4'),
        ('ilay', 'i4'),
        ('data', 'f4', 1)
    ])
    for j in range(5, len(hdsFiles), 2):
        hdsarr = np.memmap(hdsFiles[j],
                           dtype=dt,
                           mode='r',
                           offset=ofst,
                           shape=1)[0]
        sp = hdsarr['kper']
        hds[106][(j-1)//2:, sp-1] = hdsarr['data'].copy()
    ofst += dt.itemsize

fig, ax = plt.subplots(figsize=(10,7))
ax.grid()
if cell:
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 6*36+1, 6)],
        hds[49][0],
        label='#49  h in cell    (HFB)', ls=':', c='g', mec='g', ms=3.5
    )
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 12*96+1, 12)],
        hds[106][0],
        label='#106 h in cell    (HFB)', ls=':', c='r', mec='r', ms=3.5
    )
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 6*36+1, 6)],
        hds[49][1], label='#49  h in cell (no HFB)', c='k', mec='k', ms=2.
    )
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 12*96+1, 12)],
        hds[106][1],
        label='#106 h in cell (no HFB)', c='b', mec='b', ms=2.
    )
else:
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 6*36+1, 6)],
        hds[49][2],
        label='#49  h in CLN    (HFB)', ls=':', c='g', mec='g', ms=3.5
    )
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 12*96+1, 12)],
        hds[106][2],
        label='#106 h in CLN    (HFB)', ls=':', c='r', mec='r', ms=3.5
    )
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 6*36+1, 6)],
        hds[49][3],
        label='#49  h in CLN (no HFB)', c='k', mec='k', ms=2.
    )
    ax.plot_date(
        [dp('1/1/1976 00:00:00') + timedelta(hours=hrs) for hrs in range(0, 12*96+1, 12)],
        hds[106][3],
        label='#106 h in CLN (no HFB)', c='b', mec='b', ms=2.
    )
ax.set_xlim(dp('12/31/1975 12:00:00'), dp('1/1/1976 00:00:00') + timedelta(days=49))
for l in ax.get_xticklabels():
    l.set_rotation(5)
ax.set_xlabel('Time [days]')
ax.set_ylabel('Head [feet]')
ax.legend(loc='lower right', numpoints=1)
fig.suptitle('Pumping Tests w/ CLN (1/16 mile)')
plt.savefig('figures/pump_test_ref_049_106.png', dpi=300)

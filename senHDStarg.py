# -*- coding: utf-8 -*-
"""
Created on Mon Sep 22 11:34:49 2014

Generate MOD2OBS inputs, generate simulated heads at targets, generate sensitivity plots and statistics

@author: mjigmond
"""

import numpy as np
import os
import subprocess as subp
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt


# script assumes all HDS files are in current directory
# SS plots based on SP1
# TR plots based on SP2-84
# all aquifer active cells included based on BAS

def plotSen(series, figTitle, ylabel, outFN):
    fig = plt.figure(figsize = (6, 4))
    fig.suptitle(figTitle, fontsize=8)
    ax = fig.add_subplot(111)
    ax.grid(color='#888888')
    ax.set_xticks(EQ1)
    for s in series:
        ax.plot(EQ1, s[2], label=s[0], c=colors[s[1]])
    ax.set_xlim([.45, 1.55])
    ax.set_ylabel(ylabel, fontsize=7)
    ax.set_xlabel('Base factor', fontsize=7)
    xl = ax.get_xticklabels()
    for label in xl:
        label.set_rotation(35)
        label.set_fontsize(6)
    yl = ax.get_yticklabels()
    for label in yl:
        label.set_fontsize(6)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(loc='upper left', bbox_to_anchor=(1., 1.015), fancybox=True, prop={'size':6})
    plt.savefig(outFN, bbox_inches='tight', dpi=300)
    plt.close()

def readBAS(bas):
    with open(bas, 'r') as f:
        ilbls = []
        f.readline()
        f.readline()
        while True:
            line = f.readline()
            if 'INTERNAL' not in line:
                ilbls.extend([x for x in line.split()])
                if len(ilbls) == lays * rows * cols:
                    break
    return np.array(ilbls, dtype='i4').reshape(lays, rows * cols)

sps, lays, rows, cols = 84, 4, 932, 580
calFile = 'hpas.hds'
senFiles = [f for f in sorted(os.listdir('.')) if f.endswith('.hds') and 'fact' in f]
basFile = 'hpas.bas'
aqLZ = [('og', 1, 10), ('rb', 2, 30), ('et', 2, 40), ('ud', 3, 60), ('ld', 4, 70)]

colors = ['#DD3DE3', '#0d233a', '#8bbc21', '#910000', '#1aadce', '#ff0000', '#f28f43', '#0716EB']
aqs = {
    'og': 'Ogallala'
    ,'rb': 'Rita Blanca'
    ,'et': 'Edwards-Trinity (High Plains)'
    ,'ud': 'Upper Dockum'
    ,'ld': 'Lower Dockum'
}
EQ1 = np.array([.5, .9, 1., 1.1, 1.5])

labels = {
    'kh': 'Kh of '
    ,'kv': 'Kv of '
    ,'ss': 'Ss of '
    ,'sy': 'Sy of '
    ,'riv': 'River conductance'
    ,'ghb': 'GHB conductance'
    ,'res': 'Reservoir conductance'
    ,'evt': 'EVT conductance'
    ,'drw': 'Ephemeral stream conductance'
    ,'spr': 'Spring conductance'
    ,'rch': 'Recharge of '
    ,'evtr': 'Evapotranspiration rate'
    ,'exdp': 'Extinction depth'
    ,'wel': 'Pumping'
}

upwdir = './upwsen'
condir = './consen'
if not os.path.exists(upwdir): os.mkdir(upwdir)
if not os.path.exists(condir): os.mkdir(condir)

with open('./mod2obs.in', 'r') as f:
    m2oInput = f.readlines()

ibounds = readBAS(basFile)

IDX = {}
for aq in aqLZ:
    a, l, z = aq[0], int(aq[1]), int(aq[2])
    IDX[a] = np.where((ibounds[l-1]>z) & (ibounds[l-1]<(z+3)))

with open(r'S:\Projects\TWB-HPAS_GAM\modeling\mjWorkspace\targets\bore_coords.dat', 'r') as f:
    AQ = {}
    for line in f:
        ls = line.split()
        AQ[ls[0]] = ls[6]

with open('./mod2obs.in', 'r') as f:
    p = subp.Popen(['mod2obs'], stdin=f, stdout=subp.PIPE).communicate()

SAMPTR = {
    'og': ([], [], []),
    'rb': ([], [], []),
    'et': ([], [], []),
    'ud': ([], [], []),
    'ld': ([], [], [])
}
with open('output.dat', 'r') as f:
    i = 0
    for line in f:
        ls = line.split()
        SAMPTR[AQ[ls[0]]][0].append(float(ls[3]))
        SAMPTR[AQ[ls[0]]][1].append(i)
        i += 1

with open(r'S:\Projects\TWB-HPAS_GAM\modeling\mjWorkspace\targets\bore_samples.dat', 'r') as f:
    for line in f:
        ls = line.split()
        SAMPTR[AQ[ls[0]]][2].append(float(ls[3]))

for k, v in SAMPTR.items():
    SAMPTR[k] = (np.array(v[0]), v[1], np.array(v[2]))

SAMPSS = {
    'og': ([], [], []),
    'rb': ([], [], []),
    'et': ([], [], []),
    'ud': ([], [], []),
    'ld': ([], [], [])
}

ibounds = ibounds.reshape(lays, rows, cols)
with open('preDwells.csv', 'r') as f:
    for line in f:
        ls = line.split(',')
        r, c, a, h = int(ls[1])-1, int(ls[2])-1, ls[4], float(ls[6])
        SAMPSS[a][0].append(h)
        SAMPSS[a][1].append(r)
        SAMPSS[a][2].append(c)

for k, v in SAMPSS.items():
    SAMPSS[k] = (np.array(v[0]), v[1], v[2])

sf = open('senStats.csv', 'w')
sf.write('aquifer,ss/tr,run,factor,me,mae,rng,mae/rng,count\n')

MHDSS, MHDTR = {}, {}
for f in senFiles:
    fs = f.split('_')
    if len(fs) == 3:
        t = fs[1]
        fact = int(fs[2][4])
    else:
        t = '_'.join(fs[1:3])
        fact = int(fs[3][4])
    m2oName = 'mod2obs_' + f[5:-4] + '.in'
    m2oOut = 'bore_' + f[5:-4] + '.dat'
    with open(m2oName, 'w') as mf:
        lines = m2oInput[:]
        lines[4] = f + '\n'
        lines[12] = m2oOut + '\n'
        mf.writelines(lines)
    with open(m2oName, 'r') as mf:
        p = subp.Popen(['mod2obs'], stdin=mf, stdout=subp.PIPE).communicate()
    arr = np.loadtxt(m2oOut, dtype='f4', usecols=(3,))
    MHDSS.setdefault(t, np.zeros((len(aqLZ), 4)))
    MHDTR.setdefault(t, np.zeros((len(aqLZ), 4)))
    arrcal = np.memmap(
        calFile, dtype='f4', mode='r', offset=0, shape=(lays, rows * cols + 11)
    )[:,11:].reshape(lays, rows, cols)
    arrsen = np.memmap(
        f, dtype='f4', mode='r', offset=0, shape=(lays, rows * cols + 11)
    )[:,11:].reshape(lays, rows, cols)
    for i, aq in enumerate(aqLZ):
        a, l, z = aq[0], int(aq[1]), int(aq[2])
        rs, cs = SAMPSS[a][1:]
        MHDSS[t][i, fact-1] = (arrsen[l-1] - arrcal[l-1])[rs, cs].mean()
        o, s = SAMPSS[a][0], arrsen[l-1][rs, cs]
        me = (o - s).mean()
        mae = (np.abs(o - s)).mean()
        rng = o.max() - o.min()
        sf.write('{},ss,{},{},{},{},{},{},{}\n'.format(a, t, fact, me, mae, rng, mae/rng, o.size))
    for i, aq in enumerate(aqLZ):
        a, l, z = aq[0], int(aq[1]), int(aq[2])
        arrsen = arr[SAMPTR[a][1]]
        arrcal = SAMPTR[a][0]
        MHDTR[t][i, fact-1] = (arrsen - arrcal).mean()
        o, s = SAMPTR[a][2], arrsen
        me = (o - s).mean()
        mae = (np.abs(o - s)).mean()
        rng = o.max() - o.min()
        sf.write('{},tr,{},{},{},{},{},{},{}\n'.format(a, t, fact, me, mae, rng, mae/rng, o.size))

for k in MHDTR.keys():
    ks = k.split('_')
    if len(ks) == 1:
        fTitle = labels[k]
        ylabel = 'Mean head difference (feet)'
        plotSeries = []
        for i, aq in enumerate(aqLZ):
            if MHDSS[k][i,-1] == 0:
                MHDSS[k][i,-1] = np.nan
            arr = list(MHDSS[k][i])
            arr.insert(2, 0)
            plotSeries.append((aqs[aq[0]], i, arr))
        fname = '{}/{}_SS_targ'.format(condir, k)
        plotSen(plotSeries, fTitle, ylabel, fname)
        plotSeries = []
        for i, aq in enumerate(aqLZ):
            if MHDTR[k][i,-1] == 0:
                MHDTR[k][i,-1] = np.nan
            arr = list(MHDTR[k][i])
            arr.insert(2, 0)
            plotSeries.append((aqs[aq[0]], i, arr))
        fname = '{}/{}_TR_targ'.format(condir, k)
        plotSen(plotSeries, fTitle, ylabel, fname)
    else:
        fTitle = labels[ks[0]] + aqs[ks[1]]
        ylabel = 'Mean head difference (feet)'
        plotSeries = []
        for i, aq in enumerate(aqLZ):
            if MHDSS[k][i,-1] == 0:
                MHDSS[k][i,-1] = np.nan
            arr = list(MHDSS[k][i])
            arr.insert(2, 0)
            plotSeries.append((aqs[aq[0]], i, arr))
        fname = '{}/{}_SS_targ'.format(upwdir, k)
        plotSen(plotSeries, fTitle, ylabel, fname)
        plotSeries = []
        for i, aq in enumerate(aqLZ):
            if MHDTR[k][i,-1] == 0:
                MHDTR[k][i,-1] = np.nan
            arr = list(MHDTR[k][i])
            arr.insert(2, 0)
            plotSeries.append((aqs[aq[0]], i, arr))
        fname = '{}/{}_TR_targ'.format(upwdir, k)
        plotSen(plotSeries, fTitle, ylabel, fname)

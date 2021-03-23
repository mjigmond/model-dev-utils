# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 11:39:35 2016

Calculate and plot residuals and statistics

@author: mjigmond
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from dateutil.parser import parse

font = {'family': 'Consolas'}
mpl.rc('font', **font)

p = 3 # 1=primary layer assignment, 0=lowest layer assignment, 2=td only wells, 3=screen+td
db = {0: [parse('10/31/1989'), parse('3/1/1990')], 1: [parse('10/31/1999'), parse('3/1/2000')]}

if p == 1:
    bFile = 'tr_bore.primary.dat'
    oFile = 'tr_bore_output.primary.dat'
    sFile = 'tr_bore_samples.dat'
elif p == 0:
    bFile = 'tr_bore.lowest.dat'
    oFile = 'tr_bore_output.lowest.dat'
    sFile = 'tr_bore_samples.dat'
elif p == 2:
    bFile = 'tr_bore.tdonly.dat'
    oFile = 'tr_bore_output.tdonly.dat'
    sFile = 'tr_bore_samples_tdonly.dat'
elif p == 3:
    bFile = 'tr_bore.all.dat'
    oFile = 'tr_bore_output.all.dat'
    sFile = 'tr_bore_samples_all.dat'

L = {}
with open(bFile, 'r') as f:
    for line in f:
        ls = line.split()
        try: int(ls[0])
        except: continue
        L[int(ls[0])] = int(ls[3])

# parse all calibration period
WL = {}
with open(sFile, 'r') as f:
    for line in f:
        ls = line.split()
        d = parse(ls[1])
        if parse('10/31/1975') < d < parse('3/1/2000'):
            WL[int(ls[0]), d] = [float(ls[3])]

with open(oFile, 'r') as f:
    for line in f:
        ls = line.split()
        w = int(ls[0])
        d = parse(ls[1])
        if ls[3].startswith('dry') or 'E' in ls[3] and (w, d) in WL.keys():
            del WL[w, d]
        elif (w, d) in WL:
            WL[w, d].append(float(ls[3]))

LS = {}
for (w, d), v in WL.items():
    l = L[w]
    LS.setdefault(l, [])
    LS[l].append(v)

for l, v in sorted(LS.items()):
    fig, ax = plt.subplots(figsize=(6,6))
    obs, sim = zip(*v)
    obs, sim = np.array(obs), np.array(sim)
    r = obs - sim
    me = np.mean(r)
    mae = np.mean(np.abs(r))
    rng = np.max(r) - np.min(r)
    std = np.std(r)
    stats = 'ME: {:>15.2f}\nMAE: {:>14.2f}\nSTD: {:>14.2f}\nMAE/RANGE: {:8.4f}\nCOUNT: {:12d}'\
        .format(me, mae, std, mae/rng, r.size)
    ax.grid()
    ax.plot(obs, sim, ls='None', marker='o', ms=2., c='k', mec='k')
    ax.plot(
        [min(obs.min(), sim.min())-30, max(obs.max(), sim.max())+30],
        [min(obs.min(), sim.min())-30, max(obs.max(), sim.max())+30],
        c='r'
    )
    ax.set_xlabel('observed')
    ax.set_ylabel('simulated')
    ax.text(
        0.02, 0.98, stats.strip(), transform=ax.transAxes,fontsize=8,
        verticalalignment='top', horizontalalignment='left', bbox={'facecolor':'white', 'alpha':0.5}
    )
    if p == 1:
        fig.suptitle('Layer {}\n(primary layer assignment)'.format(l))
        plt.savefig('figures/L{}_oto.primary.png'.format(l), dpi=300)
    elif p == 0:
        fig.suptitle('Layer {}\n(lowest layer assignment)'.format(l))
        plt.savefig('figures/L{}_oto.lowest.png'.format(l), dpi=300)
    elif p == 2:
        fig.suptitle('Layer {}\n(TD only assignment)'.format(l))
        plt.savefig('figures/L{}_oto.tdonly.png'.format(l), dpi=300)
    elif p == 3:
        fig.suptitle('Layer {}\n(Screen+TD assignment)'.format(l))
        plt.savefig('figures/L{}_oto.screentd.png'.format(l), dpi=300)
    plt.close()

# parse 1990 and 2000
WL = {1990: {}, 2000: {}}
with open(sFile, 'r') as f:
    for line in f:
        ls = line.split()
        d = parse(ls[1])
        if (db[0][0] < d < db[0][1]) or (parse('10/31/1990') < d < parse('3/1/1991')):
            WL[1990][int(ls[0]), d] = [float(ls[3])]
        elif (db[1][0] < d < db[1][1]) or (parse('10/31/1998') < d < parse('3/1/1999')):
            WL[2000][int(ls[0]), d] = [float(ls[3])]

with open(oFile, 'r') as f:
    for line in f:
        ls = line.split()
        w = int(ls[0])
        d = parse(ls[1])
        for y in [1990, 2000]:
            if (w, d) in WL[y]:
                WL[y][w, d].append(float(ls[3]))

LS = {1990: {}, 2000: {}}
for y in [1990, 2000]:
    for (w, d), v in WL[y].items():
        l = L[w]
        LS[y].setdefault(l, [])
        LS[y][l].append(v)

lines = ''
for y in [1990, 2000]:
    for l, v in sorted(LS[y].items()):
        fig, ax = plt.subplots(figsize=(6,6))
        obs, sim = zip(*v)
        obs, sim = np.array(obs), np.array(sim)
        r = obs - sim
        me = np.mean(r)
        mae = np.mean(np.abs(r))
        rng = np.max(r) - np.min(r)
        std = np.std(r)
        rmse = np.sqrt(np.mean(r**2))
        stats = 'ME: {:>15.2f}\nMAE: {:>14.2f}\nSTD: {:>14.2f}\nMAE/RANGE: {:8.4f}\nCOUNT: {:12d}\nRMSE: {:13.2f}\nRMSE/RANGE: {:7.4f}'\
            .format(me, mae, std, mae/rng, r.size, rmse, rmse/rng)
        lines += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'\
            .format(y, l, std, mae, me, rng, r.size, std/rng, rmse, rmse/rng)
        ax.grid()
        ax.plot(obs, sim, ls='None', marker='o', ms=2., c='k', mec='k')
        ax.plot(
            [min(obs.min(), sim.min())-30, max(obs.max(), sim.max())+30],
            [min(obs.min(), sim.min())-30, max(obs.max(), sim.max())+30],
            c='r'
        )
        ax.set_xlabel('observed')
        ax.set_ylabel('simulated')
        ax.text(
            0.02, 0.98, stats.strip(), transform=ax.transAxes,fontsize=8,
            verticalalignment='top', horizontalalignment='left', bbox={'facecolor':'white', 'alpha':0.5}
        )
        if p == 1:
            fig.suptitle('{} - Layer {}\n(primary layer assignment)'.format(y, l))
            plt.savefig('figures/{}_L{}_oto.primary.png'.format(y, l), dpi=300)
        elif p == 0:
            fig.suptitle('{} - Layer {}\n(lowest layer assignment)'.format(y, l))
            plt.savefig('figures/{}_L{}_oto.lowest.png'.format(y, l), dpi=300)
        elif p == 2:
            fig.suptitle('{} - Layer {}\n(TD only assignment)'.format(y, l))
            plt.savefig('figures/{}_L{}_oto.tdonly.png'.format(y, l), dpi=300)
        elif p == 3:
            fig.suptitle('{} - Layer {}\n(Screen+TD assignment)'.format(y, l))
            plt.savefig('figures/{}_L{}_oto.screentd.png'.format(y, l), dpi=300)
        plt.close()

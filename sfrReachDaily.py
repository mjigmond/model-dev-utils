# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 08:23:13 2015

Retrieve streamflow data from the USGS and generate SFR package

@author: mjigmond
"""

import arcpy as arc
import numpy as np
import os
from dateutil.parser import parse
import json
from urllib2 import urlopen
from glob import glob


def readBASu():
    with open(basFile, 'r') as f:
        ilbls = []
        for i in range(5): f.readline()
        while 1:
            line = f.readline()
            if 'INTERNAL' not in line:
                ilbls.extend([x for x in line.split()])
                if len(ilbls) == lays * nodes: break
    return np.array(ilbls, dtype='i4').reshape(lays, nodes)

def readDISu():
    with open(disFile, 'r') as f:
        elev = []
        for i in range(3): f.readline()
        while 1:
            line = f.readline()
            if 'INTERNAL' not in line:
                elev.extend(line.split())
                if len(elev) == lays * nodes * 2: break
    return np.array(elev, dtype='f4').reshape(lays*2, nodes)

streams = 'shp/stream_grid_xsect.shp'
spFile = 'stress_periods_daily.csv'
basFile = 'braa.bas'
disFile = 'braa.dis'
rwFiles = glob(r'S:\Projects\TWB-BRAA-GAM\Model\mjigmond\sfr\RiverWare_wUSGS\*.dat')
grid = 'base_grid.shp'
xyFile = 'reaches.xy'
gagFile = 'BrazosFlowGages.txt'
rcFiles = r'S:\Projects\TWB-BRAA-GAM\Model\mjigmond\sfr\RatingCurves'

sps, lays, nodes = 365, 3, 124829
ft3d = 3600. * 24.
ft = 3.28084
fudge = 1.
stat = 0 # statistic to be used median(0)||mean(1)
strahler = 1
targyr = 2006

CONST = 1.486 * ft3d
DLEAK = 1e-4
ISFROPT = 1
IRTFLG = 1
NUMTIM = 3
WEIGHT = 7.5e-1
FLWTOL = 3e-5 * ft * ft3d

# 4a.
IUPSEG = 0

bas = readBASu()
dis = readDISu()

RC, S = {}, {} # RC=rating curve, S=segment number for each name
with open(gagFile, 'r') as f:
    lines = f.readlines()
    for line in lines[1:]:
        ls = line.split()
        g, name, s = ls
        s = int(s)
        if s != 0:
            if os.path.exists(os.path.join(rcFiles, name+'.txt')):
                with open(os.path.join(rcFiles, name+'.txt'), 'r') as f1:
                    urldata = f1.readlines()
            else:
                link = '''http://waterdata.usgs.gov/nwisweb/get_ratings?file_type=exsa&site_no={}'''.format(g)
                urldata = urlopen(link).readlines()
                data = ''.join(urldata)
                if 'QUERY = 0' in data:
                    continue
                with open(os.path.join(rcFiles, name+'.txt'), 'w') as f1:
                    f1.writelines(urldata)
            ix = [urldata.index(x) for x in urldata if x.startswith('16N')]
            if len(ix) == 0:
                print('Failed to get rating curve for', ls)
                continue
            x, y = [], []
            ps = ['', '', '']
            for dl in urldata[ix[0]+1:]:
                d = dl.split()
                if d[2] == ps[2] or d[0].startswith('-'):
                    continue
                if float(d[0]) <= 0:
                    d[0] = '.001'
                x.append(float(d[2])*ft3d)
                y.append(float(d[0]))
                ps = d[:]
            RC[s] = (x[:], y[:])
        S[name] = s

with open(os.path.join(rcFiles, 'rcGapFill.dat'), 'r') as f:
    for line in f:
        ls = line.split()
        ts, ps, lcs = [int(x) for x in ls] #ts=target seg, ps=preferred seg, lcs=last choice seg
        if ts not in RC:
            try:
                RC[ts] = RC[ps]
            except:
                RC[ts] = RC[lcs]

data = arc.da.FeatureClassToNumPyArray(
    streams,
    ['GNIS_NAME','StreamOrde','NODE','SegmOrder','Shape_Leng','RWSEG','OUTSEG','SORT_MIN','RWLABEL'],
    '''"StreamOrde">3 and "RWSEG"<73'''
)
data = np.sort(data, order=('RWSEG', 'GNIS_NAME', 'SegmOrder'))
ordnames = sorted(set(zip(data['RWSEG'], data['OUTSEG'])))

NSS = len(ordnames)

ELEV, RWFN, SO = {}, {}, {}
for d in data:
    s = d[5]
    e = d[7]
    ELEV.setdefault(s, [])
    ELEV[s].append(e)
    SO[s] = d[1]
    if d[8] not in ('', ' '): RWFN[s] = d[8]

with open(spFile, 'r') as f, open('append2dis_daily.dat', 'w') as fw:
    SP = {}
    for line in f:
        ls = line.split(',')
        mm, dd, yyyy = [int(x) for x in ls[0].split('/')]
        SP[int(ls[1])] = (yyyy, mm, dd)
        fw.write('1 1 1.2 TR\n')

RW = {}
for fn in rwFiles:
    bn = os.path.basename(fn)
    RW[bn[:-4]] = []
    with open(fn, 'r') as f:
        lines = f.readlines()
        for line in lines[5:]:
            ls = line.split()
            date = parse(ls[0])
            flw = float(ls[1]) * ft3d
            yyyy, mm, dd = date.year, date.month, date.day
            if yyyy == targyr:
                RW[bn[:-4]].append(flw)

with open('gage_flows_daily.dat', 'w') as f:
    for k, v in sorted(RW.items()):
        f.write('{} {}\n'.format(k, sps))
        for i in range(sps):
            f.write('{} {}\n'.format(i+1, v[i]))

with arc.da.SearchCursor(grid, ['NODE', 'SHAPE@XY']) as sc:
    XY = {}
    for row in sc:
        XY[row[0]] = row[1]

with open('braa.daily.sfr', 'w') as f, open(xyFile, 'w') as fxy:
    nodeLength = {}
    for i, r in enumerate(data):
        nodeLength.setdefault(r[2], [0, []])
        nodeLength[r[2]][0] += r[4] #sum lengths withing a node
        nodeLength[r[2]][1].append(r[5]) #collect segment numbers
    IREACH = 1
    assNodes = {}
    reachLines = []
    segData = {'len': {}, 'name': {}}
    for i, r in enumerate(data):
        n = r[2]
        ISEG = r[5]
        elev = r[7]
        segData['len'].setdefault(ISEG, [])
        segData['name'].setdefault(ISEG, None)
        if i > 0 and ISEG > data[i-1][5]: IREACH = 1
        s = max(nodeLength[n][1])
        RCHLEN = nodeLength[n][0]
        active = np.nonzero(bas[:,n-1])[0][0]
        NRCH = nodes * active + n
        if NRCH not in assNodes:
            reachLines.append('{} {} {} {}'.format(NRCH, ISEG, IREACH, RCHLEN))
            assNodes[NRCH] = 1
            IREACH += 1
            segData['len'][ISEG].append((RCHLEN, elev))
            segData['name'][ISEG] = r[0]
    NSTRM = len(reachLines)
    f.write('REACHINPUT\n')
    f.write('{} {} 0 0 {} {} 50 51 {} {} {} {} {}\n'.format(NSTRM, NSS, CONST, DLEAK, ISFROPT, IRTFLG, NUMTIM, WEIGHT, FLWTOL))
    corr = []
    for line in reachLines:
        ls = line.split()
        l = int(ls[0])//nodes
        n = int(ls[0])-nodes*l
        s = int(ls[1])
        ir = int(ls[2])
        if strahler:
            with open('pest/strahler{}.json'.format(SO[s]), 'r') as js:
                data = json.load(js)
                d2b = data['data.2b']
        if l == 0 and dis[4,n-1] > (segData['len'][s][ir-1][1]-21):
            corr.append((n, XY[n][0], XY[n][1], dis[0,n-1] - segData['len'][s][ir-1][1] + 21))
        start, end = segData['len'][s][0][1], segData['len'][s][-1][1]
        dist = sum(zip(*segData['len'][s])[0])
        slope = (start-end)/dist
        ls.extend([str(segData['len'][s][ir-1][1]), str(slope), '1', str(d2b['STRHC1']), segData['name'][s]])
        f.write(' '.join(ls) + '\n')
        fxy.write('{} {} {}\n'.format(int(ls[0]), *XY[n]))
    np.savetxt('braa.sfr.alterr', corr, fmt='%d %f %f %f')
    np.savetxt('botL2_corrections.csv', corr, fmt='%d,%f,%f,%f')
    ISEG = 1
    for i in range(1, sps+1):
        ITMP = NSS
        f.write('{} 1 0 SP:YYYY:MM {:03d}:{}:{:02d}:{:02d}\n'.format(ITMP, i, *SP[i]))
        for j, n in enumerate(ordnames):
            NSEG = n[0]
            OUTSEG = n[1]
            if OUTSEG in RWFN: OUTSEG = 0
            if NSEG == 8: OUTSEG = 9
            ELEVUP = ELEV[NSEG][0]
            ELEVDN = ELEV[NSEG][-1]
            ICALC = 1
            if NSEG in RC:
                ICALC = 4
                NSTRPTS = len(RC[NSEG][0])
            if NSEG in RWFN:
                fn = RWFN[NSEG]
                FLOW = RW[fn][i-1] * fudge
            else:
                FLOW = 0
            if strahler:
                with open('pest/strahler{}.json'.format(SO[NSEG]), 'r') as js:
                    data = json.load(js)
                    d6a = data['data.6a']
                    d6b = data['data.6b']
                    d6c = data['data.6c']
            else:
                with open('pest/segm{}.json'.format(NSEG), 'r') as js:
                    data = json.load(js)
                    d6a = data['data.6a']
                    d6b = data['data.6b']
                    d6c = data['data.6c']
            if ICALC == 4:
                f.write('{} {} {} {} {} {:.6e} {} {} {}\n'
                        .format(NSEG, ICALC, OUTSEG, IUPSEG, NSTRPTS, FLOW, d6a['RUNOFF'], d6a['ETSW'], d6a['PPTSW']))
                f.write('{}\n'.format(' '.join(['{:.6e}'.format(x) for x in RC[NSEG][0]])))
                f.write('{}\n'.format(' '.join([str(x) for x in RC[NSEG][1]])))
                f.write('{}\n'.format(' '.join([str(d6b['WIDTH1'])]*len(RC[NSEG][0]))))
            else:
                f.write('{} {} {} {} {:.6e} {:.3e} {} {} {}\n'
                        .format(NSEG, ICALC, OUTSEG, IUPSEG, FLOW, d6a['RUNOFF'], d6a['ETSW'], d6a['PPTSW'], d6a['ROUGHCH']))
                f.write('{}\n'.format(d6b['WIDTH1']))
                f.write('{}\n'.format(d6c['WIDTH2']))

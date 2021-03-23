# -*- coding: utf-8 -*-
"""
Created on Wed Mar 05 11:49:28 2014

Build a HFB package from a shapefile of fault lines

@author: mjigmond
"""

import arcpy as arc
import numpy as np
import os


nlay, nrow, ncol = 8, 177, 273

grid = 'qcspc.shp'
hfbcheck = 'hfbcheck_ewing_color.shp'
cfields = ['ROW', 'COL', 'CentroidX', 'CentroidY'] + ['IBND{}'.format(l+1) for l in range(nlay)]
outdir = './shp'
lines = 'polylines.shp'
outshp = os.path.join(outdir, lines)
faultshp = 'Ewing_Grid_Faults_GAM.shp'

cond = {'Red': 1e-4, 'Green': 1e-3}

arc.env.overwriteOutput = 1

arr = arc.da.FeatureClassToNumPyArray(grid, cfields)
arr = np.sort(arr, order=cfields[:2])
coords = np.vstack((arr[cfields[2]], arr[cfields[3]])).T.reshape(nrow, ncol, 2)

bas = arr[cfields[4:]].view('i4').reshape(-1, 8).T.reshape(nlay, nrow, ncol)

arc.management.CreateFeatureclass(
    outdir, lines, 'POLYLINE', '#', 'DISABLED', 'DISABLED', arc.Describe(grid).spatialReference, '#', '0', '0', '0'
)
arc.management.AddField(outshp, 'from_row', 'SHORT')
arc.management.AddField(outshp, 'from_col', 'SHORT')
arc.management.AddField(outshp, 'to_row', 'SHORT')
arc.management.AddField(outshp, 'to_col', 'SHORT')

with arc.da.InsertCursor(outshp, ['SHAPE@', 'from_row', 'from_col', 'to_row', 'to_col']) as ic:
    print('Begin drawing ...')
    for r in range(nrow):
        for c in range(ncol - 1):
            array = arc.Array()
            array.add(arc.Point(float(coords[r, c, 0]), float(coords[r, c, 1])))
            array.add(arc.Point(float(coords[r, c + 1, 0]), float(coords[r, c + 1, 1])))
            ic.insertRow([arc.Polyline(array)] + [r + 1, c + 1, r + 1, c + 2])
            array.removeAll()
    print('Finished drawing rows ...')
    for c in range(ncol):
        for r in range(nrow - 1):
            array = arc.Array()
            array.add(arc.Point(float(coords[r, c, 0]), float(coords[r, c, 1])))
            array.add(arc.Point(float(coords[r + 1, c, 0]), float(coords[r + 1, c, 1])))
            ic.insertRow([arc.Polyline(array)] + [r + 1, c + 1, r + 2, c + 1])
            array.removeAll()
    print('Finished drawing columns ...')

arc.management.MakeFeatureLayer(outshp, 'lLayer')
arc.management.MakeFeatureLayer(faultshp, 'faults')
arc.analysis.SpatialJoin(outshp, faultshp, 'in_memory/result', join_type='KEEP_COMMON')

arr = arc.da.FeatureClassToNumPyArray('in_memory/result', ['from_row', 'from_col', 'to_row', 'to_col', 'Color'])
with open('hfb/ewing.color.hfb', 'w') as f:
    lines = [[] for l in range(nlay)]
    hfbDict = {}
    for i in range(nlay):
        for rec in arr:
            fr, fc, tr, tc, clr = rec
            if bas[i,fr-1,fc-1] and bas[i,tr-1,tc-1]:
                if clr == 'Black': continue
                lines[i].append('{:>10d}{:>10d}{:>10d}{:>10d}{cond:10.2e}\n'.format(*rec, cond=cond[clr]))
                hfbDict.setdefault((fr, fc), [0]*nlay)
                hfbDict.setdefault((tr, tc), [0]*nlay)
                hfbDict[fr, fc][i] = i+1
                hfbDict[tr, tc][i] = i+1
    f.write('{:>10d} NOPRINT\n'.format(sum([len(x) for x in lines])))
    for i in range(nlay):
        f.write('{:>10d}\n'.format(len(lines[i])))
        f.writelines(lines[i])

arc.management.Copy(grid, hfbcheck)
flds = ['ROW','COL']
for l in range(nlay):
    fn = 'HFB_L{}'.format(l+1)
    arc.management.AddField(hfbcheck, fn, 'SHORT')
    flds.append(fn)

with arc.da.UpdateCursor(hfbcheck, flds) as uc:
    for r in uc:
        if (r[0], r[1]) in hfbDict:
            r[2:] = hfbDict[r[0], r[1]]
            uc.updateRow(r)

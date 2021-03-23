# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 10:46:59 2016

Generate MOD2OBS inputs

@author: mjigmond
"""

from pandas import read_excel, read_csv, isnull
from csv import reader
from dateutil.parser import parse

nlay, nrow, ncol = 8, 177, 273
X, Y, A = 5382715.077068, 18977221.41556, 58
days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

assFile = 'model_layers_assignment_GMA12_Combined_120816.xlsx'
excFile = 'GWDB.11172016/exclude_questionable.xlsx'
majFile = 'GWDB.11172016/WaterLevelsMajor.txt'
minFile = 'GWDB.11172016/WaterLevelsMinor.txt'
othFile = 'GWDB.11172016/WaterLevelsOtherUnassigned.txt'

xlsx = read_excel(assFile, sheetname='wells_with_screen_data')
WL = {}
LXY = {}
for i, r in xlsx.iterrows():
    if r.Source == 'GWDB':
        w = r.Well_ID
        fm1 = r.Main_Fm
        fm2 = r.Secondary_Fm
        fm3 = r.Tertiary_Fm
        fm4 = r.Fourth_Fm
        fm5 = r.Fifth_Fm
        x, y = r.GAM_X, r.GAM_Y
        l = [int(z.split('_')[1]) for z in [fm1,fm2,fm3,fm4,fm5] if z.startswith('layer')]
        if len(l) == 0: continue
        WL[w] = []
        LXY[w] = [l[0], max(l), x, y]

xlsx = read_excel(assFile, sheetname='wells_with_NO_screen_data')
TDWL = {}
TDLXY = {}
for i, r in xlsx.iterrows():
    w = r.ID_Num
    if w in LXY: exit(w)
    fm1 = r.Formation
    if not fm1.startswith('lyr'): continue
    l = int(fm1[3])
    x, y = r.GAM_X, r.GAM_Y
    TDWL[w] = []
    TDLXY[w] = [l, l, x, y]

with open('tr_bore.primary.dat', 'w') as f1, open('tr_bore.lowest.dat', 'w') as f2:
    for k, v in sorted(LXY.items()):
        f1.write('{:<10} {} {} {}\n'.format(k, v[2], v[3], v[0]))
        f2.write('{:<10} {} {} {}\n'.format(k, v[2], v[3], v[1]))

with open('tr_bore.tdonly.dat', 'w') as f1:
    for k, v in sorted(TDLXY.items()):
        f1.write('{:<10} {} {} {}\n'.format(k, v[2], v[3], v[0]))

with open('tr_bore.all.dat', 'w') as f1:
    for k, v in sorted(LXY.items()):
        f1.write('{:<10} {} {} {}\n'.format(k, v[2], v[3], v[0]))
    for k, v in sorted(TDLXY.items()):
        f1.write('{:<10} {} {} {}\n'.format(k, v[2], v[3], v[0]))

xlsx = read_excel(excFile, sheetname='Sheet1', header=None)
badWL = {}
for i, r, in xlsx.iterrows():
    w = r[0]
    badWL[w] = [d for d in r[1:] if not isnull(d)]

for fn in [majFile, minFile, othFile]:
    data = read_csv(fn, sep='|', low_memory=False)
    for i, r in data.iterrows():
        w = r.StateWellNumber
        if w not in WL and w not in TDWL: continue
        q = r.Status
        if q == 'No Measurement': continue
        d = r.MeasurementDate
        if isnull(d):
            mm = r.MeasurementMonth
            dd = r.MeasurementDay
            yy = r.MeasurementYear
            if mm == 0 and dd == 0:
                d = parse('{}-12-{:02d}'.format(yy, days[mm-1]))
            elif dd == 0:
                d = parse('{}-{:02d}-{:02d}'.format(yy, mm, days[mm-1]))
            else:
                pass
        else:
            d = parse(d)
        if q == 'Publishable':
            if w in WL:
                WL[w].append((d, r.WaterElevation, r.DepthFromLSD))
            elif w in TDWL:
                TDWL[w].append((d, r.WaterElevation, r.DepthFromLSD))
        elif w in badWL and q == 'Questionable' and d not in badWL[w]:
            if w in WL:
                WL[w].append((d, r.WaterElevation, r.DepthFromLSD))
            elif w in TDWL:
                TDWL[w].append((d, r.WaterElevation, r.DepthFromLSD))

with open('tr_bore_samples.dat', 'w') as f:
    for k, v in sorted(WL.items()):
#        winter = [x for x in v if x[0].month in (1, 2, 11, 12)]
        for d, wl, dth in sorted(v):
            f.write('{:10} {} 23:59:59 {}\n'.format(k, d.strftime('%m/%d/%Y'), wl))

with open('tr_bore_samples_tdonly.dat', 'w') as f:
    for k, v in sorted(TDWL.items()):
#        winter = [x for x in v if x[0].month in (1, 2, 11, 12)]
        for d, wl, dth in sorted(v):
            f.write('{:10} {} 23:59:59 {}\n'.format(k, d.strftime('%m/%d/%Y'), wl))

with open('tr_bore_samples_all.dat', 'w') as f:
    for k, v in sorted(WL.items()):
#        winter = [x for x in v if x[0].month in (1, 2, 11, 12)]
        for d, wl, dth in sorted(v):
            f.write('{:10} {} 23:59:59 {}\n'.format(k, d.strftime('%m/%d/%Y'), wl))
    for k, v in sorted(TDWL.items()):
#        winter = [x for x in v if x[0].month in (1, 2, 11, 12)]
        for d, wl, dth in sorted(v):
            f.write('{:10} {} 23:59:59 {}\n'.format(k, d.strftime('%m/%d/%Y'), wl))

with open('model.gsf', 'w') as f:
    f.write('{} {}\n'.format(nrow, ncol))
    f.write('{} {} {}\n'.format(X, Y, A))
    f.writelines('{}*5280\n{}*5280\n'.format(ncol, nrow))

with open('m2o.tr.primary.in', 'w') as f:
    f.write('model.gsf\n')
    f.write('tr_bore.primary.dat\n')
    f.write('tr_bore.primary.dat\n')
    f.write('tr_bore_samples.dat\n')
    f.write('gam/PS4run/qcsp_c_update.hds\n')
    f.write('t\n')
    f.write('9999\n')
    f.write('day\n')
    f.write('1/1/1975\n')
    f.write('00:00:00\n')
    f.write('{}\n'.format(nlay))
    f.write('500\n')
    f.write('tr_bore_output.primary.dat\n')

with open('m2o.tr.tdonly.in', 'w') as f:
    f.write('model.gsf\n')
    f.write('tr_bore.tdonly.dat\n')
    f.write('tr_bore.tdonly.dat\n')
    f.write('tr_bore_samples_tdonly.dat\n')
    f.write('gam/PS4run/qcsp_c_update.hds\n')
    f.write('t\n')
    f.write('9999\n')
    f.write('day\n')
    f.write('1/1/1975\n')
    f.write('00:00:00\n')
    f.write('{}\n'.format(nlay))
    f.write('500\n')
    f.write('tr_bore_output.tdonly.dat\n')

with open('m2o.tr.all.in', 'w') as f:
    f.write('model.gsf\n')
    f.write('tr_bore.all.dat\n')
    f.write('tr_bore.all.dat\n')
    f.write('tr_bore_samples_all.dat\n')
    f.write('gam/PS4run/qcsp_c_update.hds\n')
    f.write('t\n')
    f.write('9999\n')
    f.write('day\n')
    f.write('1/1/1975\n')
    f.write('00:00:00\n')
    f.write('{}\n'.format(nlay))
    f.write('500\n')
    f.write('tr_bore_output.all.dat\n')

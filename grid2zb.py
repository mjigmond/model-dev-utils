# -*- coding: utf-8 -*-
"""
Created on Thu Dec 08 09:42:08 2016

Generate ZoneBudget inputs given the model discretization and a model grid shapefile

@author: mjigmond
"""

import numpy as np
import arcpy as arc


grid = 'gis/shp/qcspc.shp'
cbbFile = 'calhfb.cbb'
bdgInFile = 'gam/PS10run/budInput_cty.in'
bdgOutFile = 'gam/PS10run/ctyBudget'
budFormats = ' ZBLST CSV CSV2'
nlay, nrow, ncol = 8, 177, 273

arr = arc.da.FeatureClassToNumPyArray(grid, ['ROW', 'COL', 'CountyName'])
counties = np.sort(arr, order=('ROW', 'COL'))['CountyName'].reshape(nrow, ncol)
counties[counties==' '] = '00NoCounty'

ctyList = np.unique(counties)
zones = np.zeros((nlay, nrow, ncol), dtype='int')

with open('gam/PS10run/cty_ref.dat', 'w') as f:
    for i, cty in enumerate(ctyList):
        for l in range(nlay):
            zn = (l+1) * 100 + i+1
            zones[l][counties==cty] = zn
            f.write('{},{},{}\n'.format(cty, l+1, zn))

with open('gam/PS10run/ctylay.zone', 'w') as f:
    f.write('{} {} {}\n'.format(nlay, nrow, ncol))
    for l in range(nlay):
        f.write('INTERNAL () -1\n')
        np.savetxt(f, zones[l], fmt='%d')

with open(bdgInFile, 'w') as f:
    f.write('ctyBudget' + budFormats + '\n')
    f.write(cbbFile + '\n')
    f.write('BUDGET\n')
    f.write('ctylay.zone\n')
    f.write('A\n')

with open('gam/PS10run/cty_ref_all.dat', 'w') as f:
    for i, cty in enumerate(ctyList):
        zn = 100 + i+1
        zones[0][counties==cty] = zn
        f.write('{},{},{}\n'.format(cty, 0, zn))

with open('gam/PS10run/ctylayall.zone', 'w') as f:
    f.write('{} {} {}\n'.format(nlay, nrow, ncol))
    for l in range(nlay):
        f.write('INTERNAL () -1\n')
        np.savetxt(f, zones[0], fmt='%d')

with open('gam/PS10run/budInput_cty_all.in', 'w') as f:
    f.write('ctyBudget_all' + budFormats + '\n')
    f.write(cbbFile + '\n')
    f.write('BUDGET\n')
    f.write('ctylayall.zone\n')
    f.write('A\n')

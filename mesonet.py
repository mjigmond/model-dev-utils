# -*- coding: utf-8 -*-
"""
Created on Mon Aug 28 11:27:34 2017

Generate a shapefile of Mesonet precipitation stations
@author: mjigmond
"""

import json
import arcpy as arc


arc.env.overwriteOutput = 1
wgs = arc.SpatialReference(4326)

arc.management.CreateFeatureclass('.', 'txmesonet.shp', 'POINT', spatial_reference=wgs)
flds = [('StationID', 'TEXT'), ('Lat', 'FLOAT'), ('Lon', 'FLOAT'), ('Elevation', 'FLOAT'), ('Name', 'TEXT'), ('Mesonet', 'TEXT')]
arc.management.AddFields('./txmesonet.shp', flds)

with open(r'mesonet.json') as f:
    js = json.load(f)
    
with arc.da.InsertCursor('./txmesonet.shp', ['SHAPE@XY'] + list(list(zip(*flds))[0])) as ic:
    for d in js:
        sid = d['station']
        lat = float(d['latitude'])
        lon = float(d['longitude'])
        el = float(d['elevation'])
        name = d['stationName']
        mes = d['mesonet']
        ic.insertRow([(lon,lat), sid, lat, lon, el, name, mes])

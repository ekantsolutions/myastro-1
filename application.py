#!/usr/bin/env python
__author__ = 'naren'
########################################################################################################################
################################################imports#################################################################
import numpy as np
import birthchart
import datetime
import math
import pandas as pd
import swisseph as swe
from astro import constants
import time
import re
from flask import Flask, render_template, request, jsonify, url_for
from flask_restful import Resource, Api
from sqlalchemy import create_engine, MetaData
from sqlalchemy import *
from json import dumps
import urllib2, json
import sqlite3
from flask import g
import planet_rise_times
import ip2location_lookup
import ephemeris_today
import moon_phases
import eclipse_solar

#########################################################################################################################
################################################Common###################################################################

con = sqlite3.connect('city', check_same_thread=False)
curr = con.cursor()
application = Flask(__name__, static_url_path='/astro/static')
api = Api(application)

swe.set_ephe_path('astro/data/ephemeris/')  # path to ephemeris files
f = urllib2.urlopen('http://jsonip.com/')
json_string = f.read()
f.close()
ip_add = json.loads(json_string)
ip_addrs = ip_add['ip']#'2607:f1c0:83c:7000:0:0:43:963d'
tt = ''
if (re.match('^[0-9]{0,3}.[0-9]{0,3}.[0-9]{0,3}.[0-9]{0,3}$', ip_addrs)):
    tt = 1
    location_latitude, location_longitude, TimezoneID, region  = ip2location_lookup.ipv42loc(ip_addrs)
    
else:
    tt = 0
    location_latitude, location_longitude, TimezoneID, region  = ip2location_lookup.ipv62loc(ip_addrs)
#print 'latitude is', location_latitude
#print 'Longitude is', location_longitude
#print 'region is', region
#location_longitude = 77.2167
#location_latitude = 28.6667
nows = datetime.datetime.now()
year = nows.year
month = nows.month
day = nows.day
start_time = datetime.datetime.utcnow()
time_zone = TimezoneID
#print nows

##########################################################################################################################
###############################################moon phases API############################################################
rezultsz = moon_phases.phases(year)
@application.route('/moonphases_api/', methods=['GET'])
def get_moonphasesx():
    #return jsonify({'moonphases': rezultsz})
    return jsonify({'moonphases': 'No Data Found',
                    'error': 'missing parameter'})




@application.route('/moonphases_api/<int:year>', methods=['GET'])
def moonphasessx(year):
    rezultszz = moon_phases.phases(year)
    return jsonify({'moonphases': rezultszz})


##########################################################################################################################
#################################################planet hours API#########################################################
rezults, rezultss = ephemeris_today.plan_hours(TimezoneID, location_longitude, location_latitude)
@application.route('/hours_api/')
def hoursx():
    #return jsonify({'Sunset Planetary Hours' : rezults,'Sunrise Planetary Hours' : rezultss})
    return jsonify({'Planetary Hours': 'No Data Found',
                    'error': 'missing parameters'})

@application.route('/hours_api/<Timezonez>/<lon>/<lat>', methods=['GET'])
def hoursz(Timezonez, lon, lat):
    rezults, rezultss = ephemeris_today.plan_hours(float(Timezonez), float(lon), float(lat)) 
    return jsonify({'Sunset Planetary Hours' : rezults,'Sunrise Planetary Hours' : rezultss})
    
        

@application.route('/hours_api/<Timezonez>/<lon>/')
def hourrs(Timezonez, lon):
    return jsonify({'Planetary Hours': 'No Data Found',
                'error': '1 missing parameter'})


@application.route('/hours_api/<Timezonez>/')
def housrs(Timezonez):
    return jsonify({'Planetary Hours': 'No Data Found',
                'error': '2 missing parameters'})



##########################################################################################################################
#################################################ephemeris_today API######################################################

@application.route('/home_api/')
def get_homez():
    #return jsonify({'ephemeris': rezult})
    return jsonify({'Ephemeris Today': 'No Data Found',
                    'error': 'missing parameters'})

@application.route('/home_api/<Timezonezs>/')
def get_homex(Timezonezs):
    rezult  = ephemeris_today.ephe_today(float(Timezonezs), start_time)
    return jsonify({'ephemeris': rezult})
throwaway = datetime.datetime.strptime('20110101','%Y%m%d')
@application.route('/home_api/<Timezonezs>/<time>/')
def get_homec(Timezonezs, time):
    
    try:
        datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        rezult  = ephemeris_today.ephe_today(float(Timezonezs), datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f"))
        return jsonify({'ephemeris': rezult})
    
    except ValueError:
        return jsonify({'Ephemeris Today': 'No Data Found',
                    'error': 'Parameter value doesn\'t match the prescribed format'})


##########################################################################################################################
###################################################Today's Ephemeris######################################################

@application.route('/')
def home():
    rezult  = ephemeris_today.ephe_today(TimezoneID, start_time)
#ephemeris_today
    return render_template('home.html', rez=rezult)

##########################################################################################################################
###################################################Planet Risetimes#######################################################

@application.route('/risetimes/')
def risetimes():
    x = planet_rise_times.planet_rise()
    return render_template('planet_rise_times.html', x=x)

###########################################################################################################################
###################################################Planetary Hours#########################################################

@application.route('/hours/')
def hours():
    rezults, rezultss = ephemeris_today.plan_hours(TimezoneID, location_longitude, location_latitude)
    return render_template('planetary_hours.html', res=rezults, ress=rezultss)


############################################################################################################################
###################################################Moon Phases##############################################################

@application.route('/moonphases/<int:year>')
def moonphasess(year):
    rezults = moon_phases.phases(year)
    return render_template('moon_phases.html', rez=rezults)

@application.route('/moonphases/')
def moonphases():
    rezults = moon_phases.phases(year)
    return render_template('moon_phases.html', rez=rezults)

##############################################################################################################################
####################################################Solar Eclipse##############################################################

@application.route('/eclipse/')
def eclipse():
    result = eclipse_solar.solar(year, month, day, time_zone, location_latitude, location_longitude)
    return render_template('solareclipse.html', rez=result) 
       
    

@application.route('/eclipses/')
def eclipses():
    result = eclipse_solar.solarbypos(year, month, day, time_zone, location_latitude, location_longitude)
    return render_template('solareclipsebyposition.html', rez=result) 

##############################################################################################################################
#######################################################Lunar Eclipse##############################################################

@application.route('/leclipse/')
def leclipse():
    now = swe.julday(year, month, day)
    res = swe.lun_eclipse_when(now)
    res_how = swe.lun_eclipse_how(res[1][0], 139.7, 35.68)
    #print res
    #print res_how
    eclip_time = swe.revjul(res[1][0])  # utc
    # print len(res[1]),res[0],res[1],eclip_time,bin(res[0][0])
    ecl_central_or_not = ''
    duration_penumbral = ''
    ecl_central = int('00000001', 2)
    central = res[0][0] & ecl_central
    if central == 1:
        ecl_central_or_not = 'Eclipse Central'
    ecl_noncentral = int('00000010', 2)
    central = res[0][0] & ecl_noncentral
    if central == 2:
        ecl_central_or_not = 'Eclipse Non Central'
    eclipse_total = int('00000100', 2)
    central = res[0][0] & eclipse_total
    if central == 4:
        Type = 'Eclipse Total'
        start = (date_convert(res[1][6]) + datetime.timedelta(hours=time_zone))
        #print 'Start partial', date_convert(res[1][2]) + datetime.timedelta(hours=time_zone)
        #print 'Start Total  ', date_convert(res[1][4]) + datetime.timedelta(hours=time_zone)
        maxi = (date_convert(res[1][0]) + datetime.timedelta(hours=time_zone))
        #print 'End Total    ', date_convert(res[1][5]) + datetime.timedelta(hours=time_zone)
        #print 'End partial  ', date_convert(res[1][3]) + datetime.timedelta(hours=time_zone)
        end = (date_convert(res[1][7]) + datetime.timedelta(hours=time_zone))
        duration_penumbral = (date_convert(res[1][7]) - date_convert(res[1][6]))
        duration_umbral = (date_convert(res[1][3]) - date_convert(res[1][2]))
        #print 'Total             ', date_convert(res[1][5]) - date_convert(res[1][4])

    eclipse_annualar = int('00001000', 2)
    central = res[0][0] & eclipse_annualar
    if central == 8:
        Type = 'Eclipse Annular'
    eclipse_partial = int('0010000', 2)
    central = res[0][0] & eclipse_partial
    if central == 16:
        Type = 'Eclipse Partial'
        start = (date_convert(res[1][6]) + datetime.timedelta(hours=time_zone))
        #print 'Start partial', date_convert(res[1][2]) + datetime.timedelta(hours=time_zone)
        maxi = (date_convert(res[1][0]) + datetime.timedelta(hours=time_zone))
        #print 'End partial  ', date_convert(res[1][3]) + datetime.timedelta(hours=time_zone)
        end = (date_convert(res[1][7]) + datetime.timedelta(hours=time_zone))
        duration_penumbral = (date_convert(res[1][7]) - date_convert(res[1][6]))
        duration_umbral = (date_convert(res[1][3]) - date_convert(res[1][2]))
    eclipse_ann_total = int('0100000', 2)
    central = res[0][0] & eclipse_ann_total
    if central == 32:
        Type  = 'Eclipse Penumbral'
    eclipse_ann_total = int('1000000', 2)
    central = res[0][0] & eclipse_ann_total
    if central == 64:
        Type = 'Eclipse Penumbral'
        start = (date_convert(res[1][6]) + datetime.timedelta(hours=time_zone))
        maxi = (date_convert(res[1][0]) + datetime.timedelta(hours=time_zone))
        end = (date_convert(res[1][7]) + datetime.timedelta(hours=time_zone))
        duration_umbral = (date_convert(res[1][7]) - date_convert(res[1][6]))
    soros_cycle = int(res_how[1][9])
    soros_number = int(res_how[1][10])
    magnitude_umbral = res_how[1][0]
    magnitude_penumbral = res_how[1][1]

    pos_p = swe.calc_ut(res[1][0], 0)
    signs = birthchart.natal_planet_signs(pos_p)
    sun_pos = pos_p[0]
    sun_zodiac = constants.SIGN_ZODIAC[signs[0]]
    pos_p = swe.calc_ut(res[1][0], 1)
    signs = birthchart.natal_planet_signs(pos_p)
    moon_pos = pos_p[0]
    moon_zodiac = constants.SIGN_ZODIAC[signs[0]]

    return render_template('lunareclipse.html', ecl_central_or_not = ecl_central_or_not, soros_cycle = soros_cycle,
                            sun_pos = sun_pos, sun_zodiac = sun_zodiac, moon_pos = moon_pos, moon_zodiac = moon_zodiac,
                            start = start, max = maxi, soros_number = soros_number, magnitude_umbral = magnitude_umbral,
                            end = end, Type = Type, magnitude_penumbral=magnitude_penumbral, duration_umbral = duration_umbral,
                            duration_penumbral = duration_penumbral)

@application.route('/leclipses/')
def leclipses():
    now = swe.julday(year, month, day)
    res = swe.lun_eclipse_when_loc(now, location_longitude, location_latitude)
    res_how = swe.lun_eclipse_how(res[1][0], location_longitude, location_latitude)
    duration_umbral = ''
    if res[1][8] > 0:
        moon_rise = res[1][8]
    else:
        now1 = res[1][0] - 1  # swe.julday(2016, 3, 23)
        # rsmi=1 rise,2 set
        rise = swe.rise_trans(now1, 1, location_longitude, location_latitude, rsmi=1)
        moon_rise = rise[1][0]
    if res[1][9] > 0:
        moon_set = res[1][9]
    else:
        now1 = res[1][0]  # swe.julday(2016, 3, 23)
        rise = swe.rise_trans(now1, 1, location_longitude, location_latitude, rsmi=2)
        moon_set = rise[1][0]
    #print res
    #print res_how
    eclipse_total = int('00000100', 2)
    central = res[0][0] & eclipse_total
    if central == 4:
        Type =  'Eclipse Total'
        Moon_rise = (date_convert(moon_rise) + datetime.timedelta(hours=time_zone))
        if moon_rise < res[1][6]:
            start = (date_convert(res[1][6]) + datetime.timedelta(hours=time_zone))
            duration_start = res[1][6]
        else:
            duration_start = moon_rise
        if moon_rise < res[1][2]:
            print 'Start partial', date_convert(res[1][2]) + datetime.timedelta(hours=time_zone)
            duration_start_partial = res[1][2]
        else:
            duration_start_partial = moon_rise
        if moon_rise < res[1][4]:
            print 'Start Total  ', date_convert(res[1][4]) + datetime.timedelta(hours=time_zone)
            duration_start_total = res[1][4]
        else:
            duration_start_total = moon_rise
        maxi = (date_convert(res[1][0]) + datetime.timedelta(hours=time_zone))
        if res[1][5] > 0 and moon_set > res[1][5]:
            print 'End Total    ', date_convert(res[1][5]) + datetime.timedelta(hours=time_zone)
            duration_end_total = res[1][5]
        else:
            duration_end_total = moon_set
        if res[1][3] > 0 and moon_set > res[1][3]:
            print 'End partial  ', date_convert(res[1][3]) + datetime.timedelta(hours=time_zone)
            duration_end_partial = res[1][3]
        else:
            duration_end_partial = moon_set
        if moon_set > res[1][7] and res[1][7] > 0:
            end = (date_convert(res[1][7]) + datetime.timedelta(hours=time_zone))
            duration_end = res[1][7]
        else:
            duration_end = moon_set
        Moon_set = (date_convert(moon_set) + datetime.timedelta(hours=time_zone))
        duration_penumbral = (date_convert(duration_end) - date_convert(duration_start))
        duration_umbral = (date_convert(duration_end_partial) - date_convert(duration_start_partial))
        print 'Duration Total    ', date_convert(duration_end_total) - date_convert(duration_start_total)

    eclipse_annualar = int('00001000', 2)
    central = res[0][0] & eclipse_annualar
    if central == 8:
        Type =  'Eclipse Annular'
    eclipse_partial = int('0010000', 2)
    central = res[0][0] & eclipse_partial
    if central == 16:
        Type =  'Eclipse Partial'
        Moon_rise = (date_convert(moon_rise) + datetime.timedelta(hours=time_zone))
        if moon_rise < res[1][6]:
            start = (date_convert(res[1][6]) + datetime.timedelta(hours=time_zone))
            duration_start = res[1][6]
        else:
            duration_start = moon_rise
        if moon_rise < res[1][2]:
            print 'Start partial', date_convert(res[1][2]) + datetime.timedelta(hours=time_zone)
            duration_start_partial = res[1][2]
        else:
            duration_start_partial = moon_rise
        maxi = (date_convert(res[1][0]) + datetime.timedelta(hours=time_zone))
        if res[1][3] > 0 and moon_set > res[1][3]:
            print 'End partial  ', date_convert(res[1][9]) + datetime.timedelta(hours=time_zone)
            duration_end_partial = res[1][3]
        else:
            duration_end_partial = moon_set
        if moon_set > res[1][7] and res[1][7] > 0:
            end = (date_convert(res[1][7]) + datetime.timedelta(hours=time_zone))
            duration_end = res[1][7]
        else:
            duration_end = moon_set
        Moon_set = (date_convert(moon_set) + datetime.timedelta(hours=time_zone))
        duration_penumbral = (date_convert(duration_end) - date_convert(duration_start))
        duration_umbral = (date_convert(duration_end_partial) - date_convert(duration_start_partial))
    eclipse_ann_total = int('0100000', 2)
    central = res[0][0] & eclipse_ann_total
    if central == 32:
        Type =  'Eclipse Penumbral'
    eclipse_ann_total = int('1000000', 2)
    central = res[0][0] & eclipse_ann_total
    if central == 64:
        Type = 'Eclipse Penumbral'
        Moon_rise = (date_convert(moon_rise) + datetime.timedelta(hours=time_zone))
        if moon_rise < res[1][6]:
            start = (date_convert(res[1][6]) + datetime.timedelta(hours=time_zone))
            duration_start = res[1][6]
        else:
            duration_start = moon_rise
        if moon_rise < res[1][2]:
            print 'Start partial', date_convert(res[1][2]) + datetime.timedelta(hours=time_zone)
            duration_start_partial = res[1][2]
        else:
            duration_start_partial = moon_rise
        maxi = (date_convert(res[1][0]) + datetime.timedelta(hours=time_zone))
        if res[1][3] > 0 and moon_set > res[1][3]:
            print 'End partial  ', date_convert(res[1][9]) + datetime.timedelta(hours=time_zone)
            duration_end_partial = res[1][3]
        else:
            duration_end_partial = moon_set
        if moon_set > res[1][7] and res[1][7] > 0:
            end = (date_convert(res[1][7]) + datetime.timedelta(hours=time_zone))
            duration_end = res[1][7]
        else:
            duration_end = moon_set
        Moon_set = (date_convert(moon_set) + datetime.timedelta(hours=time_zone))
        duration_penumbral = (date_convert(duration_end) - date_convert(duration_start))
        #print 'Duration Umbral   ', date_convert(duration_end_partial) - date_convert(duration_start_partial)

    moon_azm = ((res[2][4] + 180) % 360)
    moon_alt = res[2][5]
    pos_p = swe.calc_ut(res[1][0], 0)
    signs = birthchart.natal_planet_signs(pos_p)
    sun_pos = pos_p[0]
    sun_zodiac = constants.SIGN_ZODIAC[signs[0]]
    pos_p = swe.calc_ut(res[1][0], 1)
    signs = birthchart.natal_planet_signs(pos_p)
    moon_pos = pos_p[0]
    moon_zodiac = constants.SIGN_ZODIAC[signs[0]]
    soros_cycle = int(res_how[1][9])
    soros_number = int(res_how[1][10])
    magnitude_umbral = res_how[1][0]
    magnitude_penumbral = res_how[1][1]
    return render_template('lunareclipsebyposition.html', soros_cycle = soros_cycle, moon_rise = Moon_rise, moon_set = Moon_set,
                            sun_pos = sun_pos, sun_zodiac = sun_zodiac, moon_pos = moon_pos, moon_zodiac = moon_zodiac,
                            start = start, max = maxi, soros_number = soros_number, magnitude_umbral = magnitude_umbral,
                            end = end, Type = Type, magnitude_penumbral=magnitude_penumbral, duration_umbral = duration_umbral,
                            duration_penumbral = duration_penumbral, moon_alt = moon_alt, moon_azm = moon_azm)




@application.route('/content/')
def content():
    return render_template('content.html')

if __name__ == '__main__':
     application.run(debug=True)


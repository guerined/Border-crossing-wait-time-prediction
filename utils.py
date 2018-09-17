# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 21:38:42 2018

@author: Peng
"""

from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
import pandas as pd
import json

holiday_years = ['2013','2014','2015','2016','2017','2018']

def get_bc_holidays ():    
    # BC holidays
    url_base = 'https://www.officeholidays.com/countries/canada/british_columbia/'
    bc_holidays = pd.DataFrame({'Year':[],'Date':[],'Holiday':[]})
    for year in holiday_years:
        url_query = url_base + year + '.php'
        response = urllib.request.urlopen(url_query)
        soup = BeautifulSoup(response, 'lxml')
        table = soup.find('table', attrs={'class':'list-table'})
        table_body = table.find('tbody')    
        rows = table_body.find_all('tr')
        for row in rows:     
            holiday_date = row.find_next('time').text.strip()
            cols = row.find_all('td')        
            cols = [ele.text.strip() for ele in cols]
            # Third column is Date 
            holidays_name = cols[2]
            bc_holidays = bc_holidays.append(
                    pd.DataFrame([{'Year':year, "Date":holiday_date, "Holiday":holidays_name}]), 
                    ignore_index=True, sort=False)
    # Convert to Date column to proper datatype and format
    bc_holidays['Date'] = pd.to_datetime(bc_holidays['Date']).dt.date
    # Remove Mother's Day and Father's Day (not statury holidays)
    bc_holidays = bc_holidays[(bc_holidays['Holiday']!='Father\'s Day') & (bc_holidays['Holiday']!='Mother\'s Day')]
    # Remove duplicate if any
    bc_holidays.drop_duplicates(subset=['Date'], inplace=True)
    
    bc_holidays.to_csv("./data/holidays_bc.csv", index=False) 

def get_wa_holidays():
    # US holidays
    url_base = 'https://www.officeholidays.com/countries/usa/regional.php'
    region = 'Washington'
    wa_holidays = pd.DataFrame({'Year':[],'Date':[],'Holiday':[]})
    for year in holiday_years:
        url_query = url_base + '?list_year=' + year + '&list_region=' + region
        response = urllib.request.urlopen(url_query)
        soup = BeautifulSoup(response, 'lxml')
        table = soup.find('table', attrs={'class':'list-table'})
        table_body = table.find('tbody')    
        rows = table_body.find_all('tr')
        for row in rows:     
            holiday_date = row.find_next('time').text.strip()
            cols = row.find_all('td')        
            cols = [ele.text.strip() for ele in cols]
            # Third column is Date 
            holidays_name = cols[2]
            wa_holidays = wa_holidays.append(
                    pd.DataFrame([{'Year':year, "Date":holiday_date, "Holiday":holidays_name}]), 
                    ignore_index=True, sort=False)  
    # Convert to Date column to proper datatype and format
    wa_holidays['Date'] = pd.to_datetime(wa_holidays['Date']).dt.date
    # Remove Mother's Day and Father's Day (not statury holidays)
    wa_holidays = wa_holidays[(wa_holidays['Holiday']!='Father\'s Day') & (wa_holidays['Holiday']!='Mother\'s Day')]      
    # Remove duplicate if any
    wa_holidays.drop_duplicates(subset=['Date'], inplace=True)
    
    wa_holidays.to_csv("./data/holidays_wa.csv", index=False) 
               

def get_weather_forecast(api, location_id):        
    # url for Accuweather 5 Days of Daily Forecasts
    url = 'http://dataservice.accuweather.com//forecasts/v1/daily/5day/%s?apikey=%s&language=en-us&details=true&metric=true' % (location_id, api)
    try:
        with urllib.request.urlopen(url) as url:
            data = json.loads(url.read().decode())
    except IOError:
            raise  IOError("Unable to open the data url: " + url)
    
    weather_forecast = pd.DataFrame([])
    i = 0
    # 5 Days of Daily Forecasts
    while i < 5:
        weather_forecast = weather_forecast.append(pd.DataFrame({'Date':[data['DailyForecasts'][i]['Date']], 
         'Min_temp':[data['DailyForecasts'][i]['Temperature']['Minimum']['Value']], 
         'Max_temp':[data['DailyForecasts'][i]['Temperature']['Maximum']['Value']], 
         'Day_rain':[data['DailyForecasts'][i]['Day']['Rain']['Value']], 
         'Day_snow':[data['DailyForecasts'][i]['Day']['Snow']['Value']], 
         'Night_rain':[data['DailyForecasts'][i]['Night']['Rain']['Value']], 
         'Night_snow':[data['DailyForecasts'][i]['Night']['Snow']['Value']]}) ,ignore_index=True)      
        i += 1    
    
    weather_forecast.to_csv("./data/weather.csv", index=False) 

       
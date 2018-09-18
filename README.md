# Peace Arch border crossing wait time prediction

Build XGBoost model to predict border crossing wait time at Peace Arch for each hour
Collected data from:
- Border wait time: Whatcom Council of Governments (http://www.cascadegatewaydata.com/Crossing/)
- USD/CAD exchange rate: Federal Reserve Bank of St. Louis (https://fred.stlouisfed.org/series/DEXCAUS)
- Holidays: OfficeHolidays (https://www.officeholidays.com/)

## Project workflow
![image](./figures/border_wait_time_flowchart.png)

## Test result
Predictions on 08/25-08/31/2018 wait time at Peace Arch
![image](./figures/prediction.png)
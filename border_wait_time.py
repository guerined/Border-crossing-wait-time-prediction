"""
Created on Tue Sep  4 15:50:07 2018

@author: Peng Wang

Build an XGBoost model to predict border crossing wait time at Peace Arch for each hour
Collected data from:
- Border wait time:
- USD/CAD exchange rate: https://fred.stlouisfed.org/series/DEXCAUS
- Holidays: https://www.officeholidays.com/

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from datetime import date, timedelta

# Date range 1/1/2013 - 08/31/2018. Use 08/25-08/31/2018 for testing.
BEGIN_DATE = date(2013,1,1)
END_DATE = date(2018,8,31)
TEST_START_DATE = date(2018,8,25)
TEST_END_DATE = date(2018,8,31)

# ---------------------------------------------------
# ------------- Data Exploration --------------------
# ---------------------------------------------------
# Load in border crossing wait time data
data = pd.read_csv('./data/query_PeaceArch_South_cars.csv')
# Rename columns 
data.rename(columns={'Group Starts':'Date_time', 'Avg - Delay (Peace Arch South Cars)':'Delay'}, inplace=True)
# Fill missing wait time with 0
data['Delay'].fillna(0., inplace=True)
# Change date_time column type to DateTime
data['Date_time'] = pd.to_datetime(data['Date_time'])
# Extract Date
data['Date'] = data['Date_time'].dt.date
data['HourOfDay'] = data['Date_time'].dt.hour
data = data.groupby(['Date','HourOfDay'], as_index=False).agg({'Delay':'mean', 'Date_time':'first'})
# Add more features
data['Year'] = data['Date_time'].dt.year
data['Month'] = data['Date_time'].dt.month
data['DayOfMonth'] = data['Date_time'].dt.day 
data['DayOfWeek'] = data['Date_time'].dt.dayofweek 

# Load CAD/USD exchange rates
# Data from https://fred.stlouisfed.org/series/DEXCAUS
exchange_rates = pd.read_csv('./data/cad_usd_exch_rate.csv', header=0, names=['Date','ExchRate'])
exchange_rates.replace('.', np.nan, inplace=True)
exchange_rates['ExchRate'] = exchange_rates['ExchRate'].astype('float')
# Change date column type to Date
exchange_rates['Date'] = pd.to_datetime(exchange_rates['Date']).dt.date
# Merge wait time data with exchange rates
data = pd.merge(data, exchange_rates, how='left', on='Date')
# Fill nan with previous available exchange rate
data['ExchRate'].fillna(method='ffill', inplace=True)
# Exchange rate on 1/1/2013 is nan and replace it with rate from the next day
data['ExchRate'].fillna(method='bfill', inplace=True)

# Get BC and Washington holidays
# Data from https://www.officeholidays.com/
holidays_bc = pd.read_csv('./data/holidays_bc.csv')
holidays_bc.rename(columns={'Holiday':'Holiday_bc'}, inplace=True)
holidays_bc.replace(['Canada Day (observed)', 'New Year\'s Day'], ['Canada Day','New Year Day'], inplace=True)
data = pd.merge(data, holidays_bc[['Date','Holiday_bc']], how='left', on='Date')

holidays_wa = pd.read_csv('./data/holidays_wa.csv')
holidays_wa.rename(columns={'Holiday':'Holiday_wa'}, inplace=True)
holidays_wa.replace(['Christmas Day (in lieu)', 'New Year\'s Day', 'Independence Day (observed)', 
                     'New Years Day Holiday', 'Veterans Day (observed)'], 
    ['Christmas Day','New Years Day','Independence Day','New Years Day','Veterans Day'], inplace=True)
data = pd.merge(data, holidays_wa[['Date','Holiday_wa']], how='left', on='Date')

# -----------  Data visualization ----------
fig, axes = plt.subplots(2,2,figsize=(18,10))
fig.suptitle('Peace Arch border wait time {} to {}'.format(BEGIN_DATE, END_DATE))
data.groupby(['Year'])['Delay'].mean().plot.bar(ax=axes[0,0])
data.groupby(['Month'])['Delay'].mean().plot.bar(ax=axes[0,1])
data.groupby(['DayOfWeek'])['Delay'].mean().plot.bar(ax=axes[1,0])
axes[1,0].set_xticklabels(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
data.groupby(['HourOfDay'])['Delay'].mean().plot.bar(ax=axes[1,1])
for ax in fig.axes:
    ax.set_xticklabels(ax.get_xticklabels(), rotation='horizontal')
axes[0,0].figure.text(0.05,0.5, "Delay (in Minutes)", ha="center", va="center", rotation=90, fontsize='large')

fig, axes = plt.subplots(2,1,figsize=(18,10))
fig.suptitle('Peace Arch border wait time \n V.S. \n USD/CAD exchange rate')
ax = data.groupby(['Year'])['Delay'].mean().plot(ax=axes[0])
axes[0].set_title('Border wait time')
axes[0].set_ylabel('Minutes')
data.groupby(['Year'])['ExchRate'].mean().plot(ax=axes[1])
axes[1].set_title('USD/CAD exchange rate')
axes[1].set_ylabel('Exchange rate')
# Convert holiday columns
data = pd.get_dummies(data, columns=['Holiday_bc','Holiday_wa'])

# ---------------------------------------------------
# ------------- Train Model -------------------------
# ---------------------------------------------------
# Split training/test data
train_data = data[data['Date'] < TEST_START_DATE]
test_data = data[(data['Date'] >= TEST_START_DATE) & (data['Date'] <= TEST_END_DATE)]
test_data.reset_index(inplace=True, drop=True)
train_data = train_data.drop(['Date_time', 'Date'], axis=1)
test_data = test_data.drop(['Date_time', 'Date'], axis=1)
train_x = train_data.drop(['Delay'], axis=1)
train_y = train_data['Delay']
test_x = test_data.drop(['Delay'], axis=1)
test_y = test_data['Delay']
# Build XGBoost model
# model parameters
parameters = {'objective': 'reg:linear', # Linear regression
              'seed' : 0,
              'gamma': 0.2,
              'lambda': 0.2,
              'eta': 0.1, # Step size to shrink weights
              'max_depth': 10, # Max depth of tree. Deeper -> overfitting
              'subsample': 0.5, # Subsample ratio of training instances
              'colsample_bytree': 0.7, # Subsample ratio of columns of each tree
              'silent': 1, # Printing running msg
              'eval_metric': 'rmse'
              }
num_iterations = 5000
# Step training if result is not improved in # of steps
early_stopping = 10 # Number of boosting iterations
# Construct data matrix for XGBoost
dtrain = xgb.DMatrix(train_x, train_y)
deval = xgb.DMatrix(test_x, test_y)
# List of items to be evaluated during training
eval_list = [(dtrain, 'train'),(deval, 'test')] 
booster_model = xgb.train(parameters, dtrain, num_iterations, evals=eval_list, \
                early_stopping_rounds=early_stopping, 
                verbose_eval=True)

# ---------------------------------------------------
# ------------- Prediction -------------------------
# ---------------------------------------------------
test_probs = booster_model.predict(xgb.DMatrix(test_x))
pred = pd.concat([test_data, pd.DataFrame({'Prediction':test_probs})], axis=1)
NUM_SUBPLOTS = TEST_END_DATE.day - TEST_START_DATE.day + 1
fig, axes = plt.subplots(NUM_SUBPLOTS,1, figsize=(18,9),sharex=True)
fig.suptitle('Peace Arch border wait time prediction {} to {}'.format(TEST_START_DATE, TEST_END_DATE))
for i, ax in enumerate(axes):    
    curr_pred = pred.loc[pred['DayOfMonth']==TEST_START_DATE.day + i]
    ax.plot(curr_pred['HourOfDay'], curr_pred['Delay'], 'o-')
    ax.plot(curr_pred['HourOfDay'], curr_pred['Prediction'], 'o-')
    ax.set_xticks(curr_pred['HourOfDay'])
    ax.set_ylabel(TEST_START_DATE + timedelta(days=i))    
axes[int(NUM_SUBPLOTS/2)].figure.text(0.05,0.5, "Delay (in Minutes)", \
    ha="center", va="center", rotation=90, fontsize='large')
axes[0].legend(loc='upper left')
plt.xlabel('Hour of the day', fontsize='large')
# Plot important feature scores
xgb.plot_importance(booster_model)

# Save prediction and model
booster_model.save_model('./models/border_wait_time_xgb.model')
pred.to_csv("./data/predictions.csv", index=False)


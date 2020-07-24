# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import streamlit as st
import pandas as pd

#import numpy as np
import requests
#import json
#import matplotlib.pyplot as plt
#import plotly.graph_objs as go
import plotly.express as px

r = requests.get("https://api.covid19india.org/states_daily.json")
data = pd.DataFrame(r.json()["states_daily"])
data.columns = data.columns.str.upper()
## Changing data type to int for interger value columns
cols =  list(data.columns[:7]) + list(data.columns[8:32]) + list(data.columns[33:])
for i in cols:
    data[i] = data[i].astype("int64")
#data
#Data for Daman and Diu, Dadar and Nagar Haveli is merged as its being reported together going further.
data["DNDD"] = data["DD"] + data["DN"]
#data["DNDD"]
data.drop(columns = ["DN", "DD"], inplace = True )

## Creating time series data
data_ts = data.copy()
data_ts["DATE"] = data_ts["DATE"].astype("datetime64")
data_ts = data_ts.set_index(["STATUS","DATE"]).groupby(["STATUS"]).cumsum(axis = 0).unstack().T#.reset_index()#
data_ts.reset_index(inplace = True)
data_ts.rename(columns = {"level_0":"State"}, inplace = True)


#There are some cases unassigned to any state, so captured separately.
data_ts.State.fillna("UN",inplace = True)
state_names_map = {"MH":"Maharashtra","TN":"Tamil Nadu","DL":"Delhi","GJ":"Gujarat","UP":"Uttar Pradesh","RJ":"Rajasthan",
                   "WB":"West Bengal","MP":"Madhya Pradesh","HR":"Haryana","KA":"Karnataka","AP":"Andhra Pradesh","BR":"Bihar",
                   "TG":"Telangana","JK":"Jammu and Kashmir","AS":"Assam","OR":"Odisha","PB":"Punjab","KL":"Kerala",
                   "UT":"Uttarakhand","CT":"Chhattisgarh","JH":"Jharkhand","TR":"Tripura","GA":"Goa","LA":"Ladakh",
                   "MN":"Manipur","HP":"Himachal Pradesh","CH":"Chandigarh","PY":"Puducherry","NL":"Nagaland",
                   "MZ":"Mizoram","AR":"Arunachal Pradesh","SK":"Sikkim", "DNDD":"Dadra and Nagar Haveli and Daman and Diu",
                   "AN": "Andaman and Nicobar Islands","ML":"Meghalaya","LD":"Lakshadweep","UN":"Unknown","TT":"Total"}

data_ts.State = data_ts.State.map(state_names_map)
data_ts["Active"] = data_ts.Confirmed - (data_ts.Deceased + data_ts.Recovered)
#Country column added for Tableau visualization
data_ts.insert(loc = 0, column = "Country", value = "India"  )
data_ts.set_index('DATE', inplace=True)
#data_ts.drop(columns = data_ts.DATE, inplace=True)


## Aggregating data
data_agg = data.groupby("STATUS").sum()
data_agg.drop(columns = "TT", inplace = True)
data_agg = data_agg.T
data_agg.sort_values( by = "Confirmed", ascending = False, inplace = True)
data_agg = data_agg[["Confirmed", "Recovered" , "Deceased" ]]
data_agg.columns.name = data_agg.columns.name.title()
data_agg.insert(loc = 1, column = "Active", value = data_agg.Confirmed - (data_agg.Recovered + data_agg.Deceased))
## Reading testing data (statewise) from API
r = requests.get("https://api.covid19india.org/state_test_data.json")
d = pd.DataFrame(r.json()["states_tested_data"])
d = d.loc[:, ["state","totaltested"]]
min_val = d.totaltested.min()
d.loc[d.totaltested == min_val] = d.loc[d.totaltested == min_val].replace(min_val, 0)
d["totaltested"] = d["totaltested"].astype("int64")
data_test = d.groupby("state").totaltested.max().to_frame()
## Creating consolidated data (State wise)
data_agg.index = data_agg.index.map(state_names_map)
data_con = data_agg.join(data_test, how = "left").fillna(0)
data_con.totaltested = data_con.totaltested.astype("int64")
data_con.loc["TT"] = data_con.sum(axis = 0)
data_con["Infection_Rate"] = (data_con["Confirmed"].div(data_con["totaltested"])).mul(100)
data_con["Recovery_Rate"] = (data_con["Recovered"].div(data_con["Confirmed"])).mul(100)
data_con["Mortality_Rate"] = (data_con["Deceased"].div(data_con["Confirmed"])).mul(100)
data_con.index.name = "States"
data_con.rename(index = {"TT":"Total"}, inplace = True)
data_con.reset_index(inplace = True)
data_con.loc["Unknown","Infection_Rate"] = 0
data_con.fillna(0,inplace = True)
data_con.set_index('States',inplace = True)

st.sidebar.title("State Wise Data")
s_list = list(data_ts.State.unique())
s_list.remove('Unknown')
State_list = st.sidebar.selectbox(
    'Select any state',
     s_list,
     index = s_list.index('Total'))
st.title('Covid-19 India Tracker')
st.markdown("""This displays the data Total No of Confirmed, Active, Deceased,
            Recovered  cases along with other metrics for the selected state in the side bar.
	""")

df = data_ts[data_ts['State'] == State_list]

df.drop(columns = 'Country', inplace=True)

#data_con.loc[State_list,'Infection_Rate']
#st.write('Analysis for ',State_list)
st.write('**Total Tested:** ',int(data_con.loc[State_list,'totaltested']))
st.write('**Infection Rate:** ',data_con.loc[State_list,'Infection_Rate'].round(2),'%')
st.write('**Recovery Rate:** ',data_con.loc[State_list,'Recovery_Rate'].round(2),'%')
st.write('**Mortality Rate:** ',data_con.loc[State_list,'Mortality_Rate'].round(2),'%')
#data_ts
temp = 'plotly_dark'
#temp = 'plotly_white'

fig1 = px.line(df.iloc[:,1:], labels={'value':'Cases', 'DATE':'Date','STATUS':'Status of cases'},
              title ='Status of cases with time of '+State_list, template = temp)
#fig1.update_xaxes(nticks = 20,tickangle=30)
#fig1.update_layout(xaxis_tickformat = '%d %B (%a)<br>%Y')
#fig1.show()
st.plotly_chart(fig1, use_container_width=True)

#st.write('\n')

fig2 = px.bar(x=data_con.columns[:4], y = data_con.loc[State_list,data_con.columns[:4]],
              color = data_con.columns[:4] ,template = temp,
             labels = {'x':'Status of cases','y':'Total No. of cases','color':'Status of cases'},
             title = 'Total cases reported for '+State_list)
fig2.update_traces(texttemplate='%{y:}', textposition='outside')
#fig2.show()
st.plotly_chart(fig2, use_container_width=True)
st.write('**Last updated:** ',df.index.max().strftime('%d/%m/%Y'))
st.write('**Source: https://api.covid19india.org/**',)


























# =============================================================================
# selected_metrics = st.selectbox(
#     label="Choose...", options=['Total Confirmed Cases','Active Cases','Deaths','Recoveries']
# )
#
#
# trace1 = go.Scatter(x=data_total.index, y = data_total.Confirmed, name = 'Confirmed')
# trace2 = go.Scatter(x=data_total.index, y = data_total.Recovered, name = 'Recovered')
# trace3 = go.Scatter(x=data_total.index, y = data_total.Deceased, name = 'Deceased')
# trace4 = go.Scatter(x=data_total.index,
#                     y = data_total.Confirmed-(data_total.Recovered+data_total.Deceased),
#                     name = 'Active')
#
# fig = go.Figure()
# if selected_metrics == 'Total Confirmed Cases':
# 	fig.add_trace(trace1)
# if selected_metrics == 'Deaths':
# 	fig.add_trace(trace3)
# if selected_metrics == 'Recoveries':
# 	fig.add_trace(trace2)
# if selected_metrics == 'Active Cases':
# 	fig.add_trace(trace4)
# st.write('''Trend for '''+ selected_metrics)
# st.plotly_chart(fig, use_container_width=True)
# =============================================================================

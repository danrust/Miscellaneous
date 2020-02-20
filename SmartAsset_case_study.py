# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 11:57:36 2020

@author: daniel rust
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

#in this step, I'm pulling in the data
data = pd.read_excel('C:/Users/danie/Downloads/Sales Operations Analyst Case study 12.16.19 (1).xlsx')

#cleaning data, fixing all the strings so I can tie them to their FIPS code later on
data['County'] = data['County'].apply(lambda x:x.replace('Saint','St.').replace("La Salle","Lasalle"))
data['County'] = data['County'].apply(lambda x:x.capitalize().title())

#function to define value 
def value(x):
    if x == 'Product 1':
        return 50
    elif x == 'Product 2':
        return 100
    else:
        return 200

#add value column in the dataframe
data['value'] = data['Product Interest'].apply(lambda x:value(x))
data['Product Interest'].value_counts()

#pull in FIPS codes (Federal Information Processing System -- unique for each county)
fips_codes = pd.read_excel('C:/Users/danie/Documents/fips_codes.xlsx')

#clean the data, similar to above, to make a standard case format of cities/counties
fips_codes['county_name'] = fips_codes['county_name'].apply(lambda x:x.title().replace(' County','').replace(' Parish','').replace("'S",'s').replace("St ","St. "))
fips_codes.rename(columns={'county_name':'County','state_name':'State'},inplace=True)
fips_codes['fips'] = fips_codes['fips'].astype(str)

#some of the codes are missing the leading zero, this corrects that
def fips_len(x):
    if len(x) == 4:
        return '0' + x
    else:
        return x

#apply the missing leading zero fix
fips_codes['fips'] = fips_codes['fips'].apply(lambda x:fips_len(x))

#tie the FIPS codes to the data
data = pd.merge(data,fips_codes[['fips','County','State']],how='left',on=['County','State'])

#create a dataframe of expected revenue by location
ex_rev = pd.DataFrame(data.groupby(['fips','County','State'],as_index=False)['value'].sum())
ex_rev['pct_of_total'] = ex_rev['value'] / ex_rev['value'].sum()
ex_rev.sort_values(by='pct_of_total',ascending=False,inplace=True)
ex_rev['cum_pct'] = ex_rev['pct_of_total'].cumsum()
ex_rev.reset_index(drop=True, inplace=True)

#filter the largest markets that cumulatively comprise 50% of total revenue
top_markets = pd.DataFrame(ex_rev.loc[ex_rev['cum_pct'] < .501])
top10_markets = pd.DataFrame(top_markets.head(10))

#market by product type (1, 2, or 3).
#Note that this "by_type" dataframe is the "by product and location" sheet in the excel file 
by_type = data.groupby(['fips','County','State','Product Interest','value'],as_index=False)['User Number'].count()
by_type['value'] = by_type['value'] * by_type['User Number']
by_type['pct_of_total_rev'] = by_type['value'] / by_type['value'].sum()
by_type.sort_values(by='pct_of_total_rev',ascending=False,inplace=True)
by_type['cum_rev_pct'] = by_type['pct_of_total_rev'].cumsum()
by_type.reset_index(drop=True, inplace=True)
by_type.rename(columns={'User Number':'raw_demand'},inplace=True)
filtered_by_type = pd.DataFrame(by_type.loc[by_type['value'] >= 1000])


top10_markets = pd.merge(top10_markets[['fips','County','State']],by_type[['fips','Product Interest','value']],
                         how = 'left',on='fips')

def quick_state_abbr(x):
    if x == 'New York':
        return 'NY'
    elif x == 'Arizona':
        return 'AZ'
    elif x == 'Texas':
        return 'TX'
    elif x == 'Illinois':
        return 'IL'
    elif x == 'Washington':
        return 'WA'
    else:
        return 'CA'
    
    
top10_markets['state_abbr'] = top10_markets['State'].apply(lambda x:quick_state_abbr(x))
top10_markets['county_state'] = top10_markets['County'] + ', ' + top10_markets['state_abbr']
top10_markets.drop('state_abbr',axis=1,inplace=True)


#chopping it up by product
product1 = pd.DataFrame(filtered_by_type.loc[filtered_by_type['Product Interest'] == 'Product 1'])
product1['pct_of_total'] = product1['value'] / product1['value'].sum()
product1.sort_values(by='pct_of_total',ascending=False,inplace=True)
product1['cum_pct'] = product1['pct_of_total'].cumsum()
product1.reset_index(drop=True, inplace=True)

product2 = pd.DataFrame(filtered_by_type.loc[filtered_by_type['Product Interest'] == 'Product 2'])
product2['pct_of_total'] = product2['value'] / product2['value'].sum()
product2.sort_values(by='pct_of_total',ascending=False,inplace=True)
product2['cum_pct'] = product2['pct_of_total'].cumsum()
product2.reset_index(drop=True, inplace=True)

product3 = pd.DataFrame(filtered_by_type.loc[filtered_by_type['Product Interest'] == 'Product 3'])
product3['pct_of_total'] = product3['value'] / product3['value'].sum()
product3.sort_values(by='pct_of_total',ascending=False,inplace=True)
product3['cum_pct'] = product3['pct_of_total'].cumsum()
product3.reset_index(drop=True, inplace=True)



from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)


import plotly.express as px
from plotly.offline import plot


"""plot total potential revenue"""
fig = px.choropleth_mapbox(ex_rev, geojson=counties, locations='fips', color='value',
                           color_continuous_scale="Viridis",
                           range_color=(0, round(ex_rev['value'].std() * 2)),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           labels={'value':'Potential Revenue'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
plot(fig)


"""plot largest markets"""
fig = px.choropleth_mapbox(top_markets, geojson=counties, locations='fips', color='value',
                           color_continuous_scale="Viridis",
                           range_color=(0, round(ex_rev['value'].std() * 2)),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           labels={'value':'Potential Revenue'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
plot(fig)



"""plot product 1"""
fig = px.choropleth_mapbox(product1, geojson=counties, locations='fips', color='value',
                           color_continuous_scale="Viridis",
                           range_color=(0, round(product1['value'].std() * 2)),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           labels={'value':'Potential Revenue'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
plot(fig)

"""plot product 2"""
fig = px.choropleth_mapbox(product2, geojson=counties, locations='fips', color='value',
                           color_continuous_scale="Viridis",
                           range_color=(0, round(product2['value'].std() * 2)),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           labels={'value':'Potential Revenue'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
plot(fig)

"""plot product 3"""
fig = px.choropleth_mapbox(product3, geojson=counties, locations='fips', color='value',
                           color_continuous_scale="Viridis",
                           range_color=(0, round(product3['value'].std() * 2)),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           labels={'value':'Potential Revenue'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
plot(fig)


"""Stacked Bar Chart"""
fig = plt.subplots(figsize = (12, 8))
plt.rc('font', weight='normal')
plt.style.use('fivethirtyeight')
import pandas as pd
 
# Values of each group
product3_graph = list(top10_markets.loc[top10_markets['Product Interest'] == 'Product 3', 'value'])
product2_graph = list(top10_markets.loc[top10_markets['Product Interest'] == 'Product 2', 'value'])
product1_graph = list(top10_markets.loc[top10_markets['Product Interest'] == 'Product 1', 'value'])
 
# Heights of bars1 + bars2
bars = np.add(product3_graph, product2_graph).tolist()
 
# The position of the bars on the x-axis
r = np.arange(10)
 
# Names of group and bar width
names = list(top10_markets['county_state'].unique())
barWidth = 0.35
 
# Create brown bars
plt.bar(r, product3_graph, edgecolor='white', width=barWidth, label = 'Product 3')
# Create green bars (middle), on top of the firs ones
plt.bar(r, product2_graph, bottom=product3_graph, edgecolor='white', width=barWidth, label = 'Product 2')
# Create green bars (top)
plt.bar(r, product1_graph, bottom=bars, edgecolor='white', width=barWidth, label = 'Product 1')
 
# Custom X axis
plt.xticks(r, names,rotation=90)
#plt.xlabel("Location")
plt.ylabel("Revenue")

plt.legend(loc='upper right')
plt.text(x = -1.5, y = plt.ylim()[1] * 1.1,
         s = "In large markets, Product 1 is typically low revenue",
         fontsize = 26,
         weight = "bold",
         alpha = 0.75)
plt.text(x = -1.5, y = plt.ylim()[1] * 1.05,
         s = "Total revenue by market, segmented by product type",
         fontsize = 20,
         alpha = 0.85)
# Show graphic
plt.show()

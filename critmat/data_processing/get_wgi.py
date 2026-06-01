'''
Conversion script for WGI pre 2025 (wgidataset.xlsx)
'''

import pandas as pd
import numpy as np
from critmat.data_processing.translation import *

##READ WGI
def get_wgi(file, source, publish_year):
    data = pd.read_excel(file, sheet_name=None)
    outdf = pd.DataFrame()

    for sheet in data:
        # outdf[['country_code','date_year','type','value']] = data[sheet][['Economy (code)','Year','Governance dimension','Governance estimate (approx. -2.5 to +2.5)']]
        outdf = pd.concat([outdf,data[sheet][['Economy (code)','Year','Governance dimension','Governance estimate (approx. -2.5 to +2.5)']]])

    outdf= outdf.pivot(index=['Economy (code)','Year'],columns='Governance dimension',values='Governance estimate (approx. -2.5 to +2.5)').reset_index()

    outdf['mean'] = outdf[['cc','ge','pv','rl','rq','va']].mean(axis=1)
    outdf.columns = ['country_name','date_year','controlofcorruption','governmenteffectiveness','politicalstabilitynoviolence','ruleoflaw','regulatoryquality','voiceandaccountability','mean']

    outdf['source_name'] = source
    outdf['publish_year'] = publish_year
    outdf = standardize(outdf,ccodes=True) 

    return outdf

# del data['Introduction']
# sheets = list(data.keys())
# countrydata = data[sheets[1]][data[sheets[1]].columns[0:1]].copy()
# countrydata[countrydata.columns[0]] = (countrydata[countrydata.columns[0]].str.replace("'"," ")) #Cote d'Ivorie Fix
# countrydata.columns = ['country_name']

# #Following code adds year as a column, this will enable easy merge
# years = (([1996,1998,2000,2002]) + ([2002+y for y in range(1,21)])) #Range Ende modifizieren für Zukunft
# workdf = pd.DataFrame()
# for year in years:
#     countrydata['date_year'] = (np.ones(len(countrydata))*year).astype(int)
#     workdf = pd.concat([countrydata, workdf])

# #loop over values in sheets stack them and add to work dataframe
# for currentsheet in sheets:
#     currentdata = data[currentsheet].copy()    #copy only colums with values to workable dataframe
#     currentdata = currentdata[[col for col in currentdata.columns if 'Estimate' in col]]    #Cut work dataframe down to important values (Estimate = WGI)
#     currentsheet = currentsheet.replace(' ', '').lower()  #Fix fuer Sheet namen
#     currentdata.index = [country for country in countrydata[countrydata.columns[0]]]
#     currentdata.columns = years #change column names to years
#     currentdata = (currentdata.stack(future_stack=True)).reset_index()
#     currentdata.columns = ['country_name', 'date_year',currentsheet]
#     #workdf[currentsheet] = currentdata[currentdata.columns[2]]
#     workdf = pd.merge(workdf, currentdata, on=['country_name','date_year'])

# #include mean for easyier access in database
# workdf['mean'] = workdf.iloc[:,2:].mean(axis=1)

# #set source
# workdf['source_name'] = source
# workdf['publish_year'] = publish_year
# workdf = standardize(workdf,cnames=True,ccodes=True) 
# return workdf

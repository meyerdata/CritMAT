import pandas as pd
import numpy as np
from critmat.data_processing.translation import *
'''
Conversion script for WGI data publicly available from the World Bank.
For more information on the data itself see WGI_Readme.md in the input_data directory.
'''

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

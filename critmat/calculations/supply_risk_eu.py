import pandas as pd
from sqlalchemy import create_engine
import os
from critmat.calculations import get_data
from critmat.calculations import hhi_wgi_tp

def supply_risk_eu(prod_data,supply_data,wgi_data,eureport_data,tradeparameters_data,timeframe=[2016,2017,2018,2019,2020]):
    #Refactor the report data as it is not normalized for the categories
    primary_df = eureport_data[['material_name','si_sr','end_of_life','import_reliance_primary']].copy()
    primary_df['category'] = 'primary'
    primary_df = primary_df.rename(columns={'import_reliance_primary':'import_reliance'})
    refined_df = eureport_data[['material_name','si_sr','end_of_life','import_reliance_refined']].copy()
    refined_df['category'] = 'refined'
    refined_df = refined_df.rename(columns={'import_reliance_refined':'import_reliance'})
    eureport_data = pd.concat([primary_df,refined_df])

    # Calculate HHI, WGI, and Trade Parameters
    hhi_prod = hhi_wgi_tp(prod_data, wgi_data, tradeparameters_data, timeframe=timeframe)
    hhi_supply = hhi_wgi_tp(supply_data, wgi_data, tradeparameters_data, timeframe=timeframe)

    if hhi_prod.empty:
        print('Error: Check if production data is available in the database')
        return None
    if hhi_supply.empty:
        print('Error: Check if trade data is available in the database')
        return None
    
    supply_risk_data = hhi_prod.merge(hhi_supply, on=['material_name', 'category'], how='outer', suffixes=('_world', '_eu'))
    supply_risk_data = supply_risk_data.merge(eureport_data, on=['material_name', 'category'], how='outer')
 
    supply_risk = supply_risk_data[['material_name','category','source_name_world','date_year_world','source_name_eu','date_year_eu']]
    supply_risk = supply_risk.rename(columns={'source_name_world': 'used_sources_world','date_year_world':'timeframe_world','source_name_eu': 'used_sources_eu','date_year_eu':'timeframe_eu'})

    #The supply risk is calculated three times, once only using the production data, once only using the EU supply, and once using both with the import reliance
    supply_risk['result_only_world'] = (supply_risk_data['hhi_world']/10000)*(1-supply_risk_data['end_of_life']/100)*supply_risk_data['si_sr']
    supply_risk['result_only_eu'] = (supply_risk_data['hhi_eu']/10000)*(1-supply_risk_data['end_of_life']/100)*supply_risk_data['si_sr']
    supply_risk['result'] = (supply_risk_data['hhi_world']/10000*(supply_risk_data['import_reliance']/100/2)+supply_risk_data['hhi_eu']/10000*(1-supply_risk_data['import_reliance']/100/2))*(1-supply_risk_data['end_of_life']/100)*supply_risk_data['si_sr']
    
    supply_risk['result_only_world'] = supply_risk['result_only_world'].round(3)
    supply_risk['result_only_eu'] = supply_risk['result_only_eu'].round(3)
    supply_risk['result'] = supply_risk['result'].round(3)

    supply_risk = supply_risk.dropna(subset=['result_only_world','result_only_eu','result'],how='all')

    return supply_risk
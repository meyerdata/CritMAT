import pandas as pd

'''
Function to calculate the Herfindahl-Hirschman Index (HHI) with World Governance Index (WGI) weighting.
For advanced implementations using World Governance Index (WGI) AND EU trade parameters, refer to the hhi_wgi_tp function.
If a timeframe is provided, the resulting HHI will be aggregated over the specified years. If no timeframe is provided, the HHI will be calculated for each year separately.
'''
def hhi_wgi(prod_data,wgi_data,timeframe=None):
    hhi = pd.DataFrame(columns=['material_name','source_name','hhi'])

    #Filter the data if timeframe is provided, otherwise use the entire dataset
    if timeframe is not None:
        try:
            prod_data = prod_data[prod_data['date_year'].isin(timeframe)]    
            wgi_data = wgi_data[wgi_data['date_year'].isin(timeframe)]
        except KeyError:
            print("Error: timeframe not valid. Please ensure that the the timeframe is a list of valid years.")
    
    #'supply' is used for trade data, while 'quantity' is used for production data
    data_column = 'quantity' if 'quantity' in prod_data.columns else 'supply'

    #We need to keep track of the trade data source, so that combinations of trade data and production data can be calculated.
    trade_sources = ['EUST']
    
    #We loop over the unique sources, categories, and materials to calculate the HHI for each combination
    for source in prod_data['source_name'].unique():
        source_data = prod_data[prod_data['source_name'].isin([source] + trade_sources)]
        for category in source_data['category'].unique():
            category_data = source_data[source_data['category'] == category]       
            for material in category_data['material_name'].unique():
                material_data = category_data[(category_data['material_name'] == material)]
                if material_data.empty:
                    continue

                #skip the material if the only source is not the current source, this is to avoid double counting of trade data
                if material_data['source_name'].nunique() == 1:
                    if material_data['source_name'].iloc[0] != source:
                        continue

                material_data = material_data.merge(wgi_data, on=['country_name'], how='left', suffixes=('', '_wgi'))
                material_data['mean'] = (material_data['mean']-2.5)*-2 

                #If a timeframe is provided, we aggregate the data over the specified years. If no timeframe is provided, we calculate the HHI for each year separately.
                if timeframe:
                    #The folowing groupby is used for trade data, where multiple sources may need to be combined
                    prod_timeframe = material_data.groupby(['material_name','country_id','category']).agg({data_column: 'sum', 'mean': 'mean','source_name': lambda x: (x).unique()}).reset_index()
                    prod_timeframe['date_year'] = str(timeframe)
                    prod_timeframe[data_column + '_total'] = prod_timeframe[data_column].sum()
                else:
                    #The folowing groupby is used for trade data, where multiple sources may need to be combined
                    prod_timeframe = material_data.groupby(['material_name','country_id','category','date_year']).agg({data_column: 'sum', 'mean': 'mean','source_name': lambda x: (x).unique()}).reset_index()
                    #The following line is added to ensure that the total quantity/supply is calculated for each year separately, which is necessary for the HHI calculation.
                    year_total = prod_timeframe.groupby(['material_name','category','date_year']).sum()[data_column]
                    prod_timeframe = prod_timeframe.merge(year_total, on=['material_name','category','date_year'], suffixes=('', '_total'))

                prod_timeframe['source_name'] = prod_timeframe['source_name'].apply(lambda x: str(x[0]) if len(x) == 1 else str(x)) #This is just to handle a possible error case

                #The HHI is calculated as sum(share^2) for each material, category, and year.
                prod_timeframe['hhi'] = (prod_timeframe[data_column]/prod_timeframe[data_column + '_total']*100)**2*prod_timeframe['mean']
                used_sources = str([source for source in prod_timeframe['source_name'].unique()])
                hhi_year = prod_timeframe.groupby(['material_name','category','date_year']).sum().reset_index()
                
                hhi_year['source_name'] = used_sources
                hhi = pd.concat([hhi,hhi_year[['material_name','category','date_year','source_name','hhi']]],ignore_index=True)
    
    return hhi
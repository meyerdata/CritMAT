import pandas as pd
import critmat.calculations.get_data as get_data

def calc_hhi(prod_data,timeframe=range(2016,2020)):
    hhi = pd.DataFrame(columns=['material_id','source_id','hhi'])
    prod_data = prod_data[prod_data['date_year'].isin(timeframe)]

    for source in prod_data['source_id'].unique():
        source_data = prod_data[prod_data['source_id'] == source]
        for category in source_data['category'].unique():
            category_data = source_data[source_data['category'] == category]       
            for material in category_data['material_id'].unique():
                material_data = category_data[(category_data['material_id'] == material)]
                if material_data.empty:
                    continue
                total = material_data.groupby(['material_id','category','source_id']).sum()['quantity'].values[0]
                prod_year = material_data.copy()
                prod_year['hhi'] = (prod_year['quantity']/total*100)**2
                hhi_year = prod_year.groupby(['material_id','category','source_id']).sum().reset_index()
                hhi = pd.concat([hhi,hhi_year[['material_id','category','source_id','hhi']]],ignore_index=True)
    return hhi


if __name__ == "__main__":
    prod_data = get_data.get_data('production')
    hhi = calc_hhi(prod_data)
    print(hhi)
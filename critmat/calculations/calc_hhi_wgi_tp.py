import pandas as pd
import critmat.calculations.get_data as get_data

def calc_hhi_wgi_tp(prod_data,wgi_data,tradeparameters,scope='world',timeframe=range(2016,2020)):
    hhi = pd.DataFrame(columns=['material_id','source_id','hhi'])
    prod_data = prod_data[prod_data['date_year'].isin(timeframe)]
    wgi_data = wgi_data[wgi_data['date_year'].isin(timeframe)]

    for source in prod_data['source_id'].unique():
        source_data = prod_data[prod_data['source_id'] == source]
        for category in source_data['category'].unique():
            category_data = source_data[source_data['category'] == category]       
            for material in category_data['material_id'].unique():
                material_data = category_data[(category_data['material_id'] == material)]
                if material_data.empty:
                    continue
                material_data.sort_values('quantity').to_csv('temp.csv')
                total = material_data.groupby(['material_id','category','source_id']).sum()['quantity']
                if len(total) != 1:
                    print(f"Warning: Multiple totals found for material {material}, category {category}, source {source}. Skipping.")
                    continue
                else:
                    total = total.values[0]
                prod_year = material_data.copy()
                prod_year = prod_year.merge(wgi_data[['country_id','date_year','mean']], on=['country_id','date_year'], how='left', suffixes=('', '_wgi'))
                prod_year = prod_year.merge(tradeparameters[tradeparameters['scope'] == scope], on=['country_id','material_id','category'], how='left', suffixes=('', '_tp'))
                prod_year['hhi'] = (prod_year['quantity']/total*100)**2*(prod_year['mean']-2.5)*-2*prod_year['parameter']
                hhi_year = prod_year.groupby(['material_id','category','source_id']).sum().reset_index()
                hhi = pd.concat([hhi,hhi_year[['material_id','category','source_id','hhi']]],ignore_index=True)
    return hhi

if __name__ == "__main__":
    prod_data = get_data.get_data('production')
    wgi_data = get_data.get_data('wgi')
    tradeparameters = get_data.get_data('tradeparameters')
    hhi = calc_hhi_wgi_tp(prod_data, wgi_data, tradeparameters)
    print(hhi.sort_values('hhi', ascending=False).head(20))
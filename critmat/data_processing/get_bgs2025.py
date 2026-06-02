import os
import pandas as pd
import warnings
from critmat.data_processing.translation import *
'''
This function processes publicly available BGS API files and returns a DataFrame with translated material names and categories.
For more information on the data itself see BGS_Readme.md in the input_data directory.
'''

def get_bgs2025(folder,source,publish_year,fetch_from_web=False,db_out=True):
    files = [cs for cs in os.listdir(folder) if cs.endswith('.csv')]

    #Just used for translation, category part is legacy and unused
    material_lookup = {'chromium ores and concentrates':['Chromium','primary'],
                       'lithium minerals':['Lithium','primary'],
                        'bery':['Berylium','primary'],
                        'borates':['Boron','primary'],
                       'magnesium metal':['Magnesium','refined'],
                       'germanium metal':['Germanium','refined'],
                       'manganese ore':['Manganese','primary'],
                        'strontium minerals':['Strontium','primary'],
                        'talc':['Talc, Steatite & Pyrophyllite','primary'],
                        'titanium minerals':['Titanium Metal','primary'],
                        'zirconium minerals':['Zirconium','primary'],
                        # 'tungsten, mine':['Tungsten','refined'], #THIS IS ONLY DEFINED AS REFINED BECAUSE OF THE EU REPORT (MIGHT WANT TO MAKE A COPY TO PRIMARY OR FIND OTHER SOLUTION
    }
    sub_commodity_lookup = {
                        'platinum group metals':['PGM','refined'],
                        'ferro-alloys':['Ferro-Alloys','refined'],
                        # "bentonite and fuller's earth":[],
                        # "tantalum and niobium minerals":[],
    }
    # sub_commodity_others = {
    #                     "Other platinum metals":['Iridium', 'Rhodium']
    # }
    resultdf = pd.DataFrame()
    for file in files:
        data = pd.read_csv(folder + file)

        workdf = data[['bgs_commodity_trans','bgs_sub_commodity_trans','quantity','units','year','country_iso2_code']].copy()
        workdf.columns = ['material_name','sub_commodity','quantity','unit','date_year','country_name']
        workdf[['material_name','category']] = workdf['material_name'].str.split(',',expand=True)
        workdf['source_name'] = source
        workdf['publish_year'] = publish_year
        workdf.loc[workdf['material_name'].isna(),'material_name'] =  workdf.loc[workdf['material_name'].isna(),'sub_commodity']


        if db_out:
            workdf.loc[workdf['material_name'].str.contains('metal',na=False),'category'] = 'refined'
            workdf.loc[workdf['material_name'].str.contains('alloy',na=False),'category'] = 'refined'
            workdf.loc[workdf['material_name'].str.contains('ore',na=False),'category'] = 'primary'
            workdf.loc[workdf['material_name'].str.contains('minerals',na=False),'category'] = 'primary'
            workdf.loc[workdf['category'].str.contains('primary',na=False),'category'] = 'primary'
            workdf.loc[workdf['category'].str.contains('mine',na=False),'category'] = 'primary'
            workdf.loc[workdf['category'].str.contains('crude',na=False),'category'] = 'primary' #Oil
            workdf.loc[workdf['category'].str.contains('slab',na=False),'category'] = 'refined'
            workdf.loc[workdf['category'].str.contains('white',na=False),'category'] = 'refined' #Arsenic
            workdf.loc[workdf['category'].str.contains('refine',na=False),'category'] = 'refined'
            #this is used for the EU Method
            workdf.loc[workdf['material_name'].str.contains('platinum',na=False),'category'] = 'refined'
            workdf.loc[workdf['material_name'].str.contains('tungsten',na=False),'category'] = 'refined'

            workdf.loc[workdf['category'].isna(),'category'] = 'primary'



        for material in sub_commodity_lookup.keys():
            # print(material + ' - ' +  str(workdf.loc[workdf['material_name'] == material,'sub_commodity'].unique()))
            # workdf.loc[workdf['material_name'] == material,'category'] =  sub_commodity_lookup[material][1]
            workdf.loc[workdf['material_name'].str.contains(material,na=False),'material_name'] =  workdf.loc[workdf['material_name'].str.contains(material,na=False),'sub_commodity']

        #Can handel "other sub commodities"
        # for other_material in sub_commodity_others.keys():
        #     matdata = workdf.loc[workdf['material_name'] == other_material].copy().reset_index(drop=True)
        #     for overwrite in sub_commodity_others[other_material]:
        #         new_matdata = matdata.replace({'material_name': {other_material:overwrite}}).reset_index(drop=True)
        #         workdf = pd.concat([workdf,new_matdata])

        if db_out:
            del workdf['sub_commodity']

        for material in material_lookup.keys():
            # workdf.loc[workdf['material_name'] == material,'category'] =  material_lookup[material][1]
            workdf['material_name'] = workdf['material_name'].replace({material:material_lookup[material][0]})  

        workdf['country_name'] = workdf['country_name'].astype(str)
        workdf['date_year'] = workdf['date_year'].astype(str).str[0:4]
        workdf['material_name'] = workdf['material_name'].str.capitalize()

        resultdf = pd.concat([resultdf,workdf])

    print(resultdf)
    resultdf = standardize(resultdf,ccodes=True,quantity_to_t=True)
    return resultdf

import pandas as pd
import os
from critmat.data_processing.translation import *

def get_wmd(folder, source, publish_year):
    files = [xl for xl in os.listdir(folder) if (xl.endswith('.xlsx') and (not xl.startswith('~$')))]
    file = [file for file in files if '6.4.' in file]
    if len(file) == 0:
        raise Exception("Could not find the correct file")
    elif len(file) > 1:
        raise Exception("Found to many files")
    else:
        file = file[0]

    data = pd.read_excel(folder + '/' + file, sheet_name=None, skiprows=1)
    materials = list(data.keys())
    workdf = pd.DataFrame()
    for currentmaterial in materials:
        currentdata = data[currentmaterial].copy()
        helpdf = pd.concat([currentdata[currentdata.columns[0:2]]]*len(currentdata.columns[2:-1])).sort_index().reset_index(drop=True)
        helpdf['material'] = currentmaterial
        currentdata = (currentdata[currentdata.columns[2:-1]].stack(future_stack=True).reset_index())
        helpdf['year'] = currentdata['level_1']
        helpdf['quantity'] = currentdata[currentdata.columns[-1]]
        workdf = pd.concat([workdf, helpdf])
    
   
    # currently all wmd is defined to be primary    
    workdf.columns = ["country_name","unit","material_name","date_year","quantity"]

    # remove material specification in parentheses (this could be removed in the future)
    workdf = workdf.reset_index(drop=True)
    workdf = workdf.drop(index=workdf.loc[workdf['country_name'].str.contains('Total',case=False)].index).reset_index(drop=True)
    parentheses = workdf['material_name'].str.find('(')
    for i in range(len(workdf['material_name'])):
        if parentheses[i] != -1:
            workdf.loc[i,'material_name'] = workdf.loc[i,'material_name'][:parentheses[i]].strip()

    #This list is used to determine refined material data
    refined_mat = ['Aluminium','Arsenic','Cadmium','Gallium','Germanium','Indium','Platinum','Selenium','Sulfur','Tellurium',"Palladium","Rhodium",'Rare Earth']
    refmatidx = [idx for list in [workdf.index[workdf['material_name'].str.contains(material)].tolist() for material in refined_mat] for idx in list]
    workdf.loc[~workdf.index.isin(refmatidx),'category'] = 'primary'
    workdf.loc[refmatidx,'category'] = 'refined'

    workdf['date_year'] = workdf['date_year'].astype(int)
    workdf['quantity'] = workdf['quantity'].fillna(0)
    workdf['quantity'] = workdf['quantity'].astype(float).round()
    workdf['source_name'] = source
    workdf['publish_year'] = publish_year

    workdf = standardize(workdf,cnames=True)


    return workdf

import pandas as pd
import numpy as np
from critmat.data_processing.translation import *

def get_wmd_full(file, source, year):
    data = pd.read_excel(file)
    data = data.rename(columns={'Minerals in metric tons*':'country_name'})
    droprows = data.iloc[data.index[data["country_name"].isna()][0]:,:]
    # print('WARNING: dropping the following information:')
    # print(droprows.dropna(how='all'))
    data = data.drop(droprows.index)

    #If new materials are added to WMD this is where they should be included
    materials_lookup = ["Iron","Chromium","Cobalt","Manganese","Molybdenum","Nickel","Niobium","Tantalum","Titanium","Tungsten","Vanadium","Aluminium","Antimony","Arsenic","Bauxite",
        "Beryllium","Bismuth","Cadmium","Copper","Gallium","Germanium","Indium","Lead","Lithium","Mercury","Rare Earth","Rhenium","Selenium","Tellurium","Tin",
        "Zinc","Gold","Palladium","Platinum","Rhodium","Silver","Asbestos","Baryte","Bentonite","Boron","Diam","Diatomite","Feldspar",
        "Fluorspar","Graphite","Gypsum","Kaolin","Magnesite","Perlite","Phosphate Rock","Potash","Salt","Sulfur","Talc","Vermiculite","Zircon","Steam Coal",
        "Coking Coal","Lignite","Natural Gas","Petroleum","Oil Sands","Oil Shales","Uranium"]
    
    #This list is used to determine refined material data
    refined_mat = ['Aluminium','Arsenic','Cadmium','Gallium','Germanium','Indium','Platinum','Selenium','Sulfur','Tellurium',"Palladium","Rhodium",'Rare Earth']

    #This is an overwrite that is apllied at the end to assure correct assignment in the database
    overwrite_mat = {'Bauxite': ['Aluminium'],'Iron': ['Iron Ore'],'Graphite': ['Natural Graphite'],
                     'Rare Earth': ['Cerium','Dysprosium','Erbium','Europium','Gadolinium','Holmium','Lanthanum','Lutetium','Neodymium','Praseodymium','Samarium','Terbium','Thulium','Ytterbium','Yttrium']
                     }

    #Wildeste List comprehension evar
    matidx = sorted(list(set([idx for list in [data.index[data['country_name'].str.contains(material)].tolist() for material in materials_lookup] for idx in list]))) 
    # print(data.iloc[matidx]['country_name'].values)    
    found_materials = data.iloc[matidx]['country_name'].values
    matidx += [len(data)]

    workdf = pd.DataFrame()
    for i in range(0,len(matidx)-1):
        currentdata = data.iloc[matidx[i]+1:matidx[i+1]].copy()        
        helpdf = pd.concat([currentdata[currentdata.columns[0:1]]]*len(currentdata.columns[1:])).sort_index().reset_index(drop=True)
        helpdf['material_name'] = found_materials[i]
        currentdata = (currentdata[currentdata.columns[1:]].stack(future_stack=True).reset_index())
        helpdf['date_year'] = currentdata['level_1'].astype(int)
        helpdf['quantity'] = currentdata[currentdata.columns[-1]]
        workdf = pd.concat([workdf, helpdf])
    
    workdf = workdf.dropna()
    workdf = workdf.reset_index(drop=True)
    workdf['source_name'] = source
    workdf['publish_year'] = year
    workdf['unit'] = 't'    

    workdf.loc[workdf.index[workdf['material_name'].str.contains('(kg)')],'unit'] = 'kg'
    workdf.loc[workdf.index[workdf['material_name'].str.contains('Mio. m3')],'unit'] = 'Mio m3'

    for material in materials_lookup:
        workdf['material_name'] = workdf['material_name'].apply(lambda x: material if material in x else x)

    #standardize the country names
    workdf = standardize(workdf,quantity_to_t=True,cnames=True)
    ##Split primary and refined materials
    refmatidx = [idx for list in [workdf.index[workdf['material_name'].str.contains(material)].tolist() for material in refined_mat] for idx in list]

    workdf.loc[~workdf.index.isin(refmatidx),'category'] = 'primary'
    workdf.loc[refmatidx,'category'] = 'refined'

    for old_matname in overwrite_mat.keys():
        for new_matname in overwrite_mat[old_matname]:
            workdf = pd.concat([workdf,workdf[workdf['material_name'] == old_matname].copy().replace({'material_name': {old_matname:new_matname}})]).reset_index(drop=True)
        if old_matname in workdf['material_name'].values:
            workdf = workdf.drop(workdf[workdf['material_name'] == old_matname].index)

    # out_primary = out_primary.replace({'material_name': overwrite_mat})
    # out_refined = out_refined.replace({'material_name': overwrite_mat})

    return workdf

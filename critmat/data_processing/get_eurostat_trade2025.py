import os
import numpy as np
import pandas as pd
from critmat.data_processing.translation import *
'''
Conversion script for the EU's trade flow data publicly available from Eurostat.
For more information on the data itself see Eustat_Readme.md in the input_data directory.
'''

def get_eurostat_trade2025(folder_path,code_file,source,publish_year,load_temp=False,testing=False):
    #load_temp lets you skip the processing of the orinignal source files and load the latest output
    if load_temp:
        try:
            print('Loading potentially outdated data.')
            df = pd.read_csv('temp_outputs/eurostat_raw.csv')
            print(df)
            df = standardize(df,ccodes=True)
            return df
        except:
            print('Failed.')
            return pd.DataFrame()

    files = os.listdir(folder_path)    # list of all files to be read
    if testing:
        # files = ['prefs2016.dat','prefs2017.dat','prefs2018.dat','prefs2019.dat','prefs2020.dat']            
        files = testing
        
    Matdata = pd.read_excel(code_file)
    interestingMats_primary = Matdata.set_index('name')['cn8code_primary'].dropna().str.split(',').to_dict()
    interestingMats_refined = Matdata.set_index('name')['cn8code_refined'].dropna().str.split(',').to_dict()
    interestingMats = list(set(list(interestingMats_primary.keys())+list(interestingMats_refined.keys())))

    # https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202302364 None of our products have "supplemenatry units".

    #this will translate the declarant_iso column. This is just a workaround for the translation.py not being able to handle two country columns
    EUISO3 = {'Austria':['AT'],'Belgium':['BE'],'Bulgaria':['BG'],'Croatia':['HR'],'Cyprus':['CY'],'Czechia':['CZ'],
              'Denmark':['DK'],'Estonia':['EE'],'Finland':['FI'],'France':['FR'],'Germany':['DE'],'Greece':['GR','EL'],'United Kingdom':['GB'],
              'Hungary':['HU'],'Ireland':['IE'],'Italy':['IT'],'Latvia':['LV'],'Lithuania':['LT'],'Luxembourg':['LU'],
              'Malta':['MT'],'Netherlands':['NL'],'Poland':['PL'],'Portugal':['PT'],'Romania':['RO'],'Slovakia':['SK'],
              'Slovenia':['SI'],'Spain':['ES'],'Sweden':['SE'],'European Union':['EU']}

    df = pd.DataFrame()
    listOfCodes_primary = []
    for m,codes in interestingMats_primary.items():
        interestingMats_primary[m] = [codes_clean.strip() for codes_clean in codes] # remove whitespace from codes
        for code in codes:
            listOfCodes_primary.append(code.strip())    # create list of materials to speed up pandas isin check
    
    listOfCodes_refined = []
    for m,codes in interestingMats_refined.items():
        interestingMats_refined[m] = [codes_clean.strip() for codes_clean in codes] #remove whitespace from codes
        for code in codes:
            listOfCodes_refined.append(code.strip())    # create list of materials to speed up pandas isin check
    
    listOfCodes_primary = tuple(listOfCodes_primary)    # conversion to tuple so df.str.startswith can work with 
    listOfCodes_refined = tuple(listOfCodes_refined)    # codes that are potentially 4 to 8 digits long

    for file in files:
        print('processing eurostat ' + str(file) + ' ...')         
        rawdata = pd.read_csv(folder_path + file)
        if not (rawdata["PERIOD"]%100 == 52).any():   #This if statement prechecks if there is data for a whole year inside the file (ending in 52) 
            print('No data with PERIOD ending in 52 found for ' + str(file))  
            print(str(file) + ' is not considered in output')
            break
        data_primary = rawdata.loc[(rawdata['PRODUCT'].str.startswith(listOfCodes_primary)) & (rawdata["PERIOD"]%100 == 52)].reset_index()
        data_refined = rawdata.loc[(rawdata['PRODUCT'].str.startswith(listOfCodes_refined)) & (rawdata["PERIOD"]%100 == 52)].reset_index()
        result_primary = pd.DataFrame()
        result_refined = pd.DataFrame()  
        # The following loop extracts the values for each product code from the data_ files and stores it in
        # the material_. There, the material name is added. Then it gets appended to the results df. 
        # This is necessary, because for example Niobium and Tantalum share a product code. With this implementation, both get the entire
        # production quantity assigned to them, double counting the actual values because we don't know their respective shares. 
        for m,codes in interestingMats_primary.items():
            if not (data_primary['PRODUCT'].str.startswith(tuple(codes)).any()):    #This if statement prechecks if there even is a data entry for the material in the code
                print('No primary data for ' + str(m) + ' product code ' + str(codes) + ' found in ' + str(file))  
            material_primary = data_primary.loc[data_primary['PRODUCT'].str.startswith(tuple(codes)),['PRODUCT','REPORTER','PARTNER','PERIOD','QUANTITY_KG','VALUE_EUR']].copy()
            material_primary['MATERIAL'] = m
            result_primary = pd.concat([result_primary,material_primary])

        for m,codes in interestingMats_refined.items():
            if not (data_refined['PRODUCT'].str.startswith(tuple(codes)).any()):    #This if statement prechecks if there even is a data entry for the material in the code
                print('No refined data for ' + str(m) + ' product code ' + str(codes) + ' found in ' + str(file))  
            material_refined = data_refined.loc[data_refined['PRODUCT'].str.startswith(tuple(codes)),['PRODUCT','REPORTER','PARTNER','PERIOD','QUANTITY_KG','VALUE_EUR']].copy()
            material_refined['MATERIAL'] = m
            result_refined = pd.concat([result_refined,material_refined])

        result_primary = result_primary[['MATERIAL','PRODUCT','PERIOD','REPORTER','PARTNER','QUANTITY_KG','VALUE_EUR']].groupby(['MATERIAL','PRODUCT','PERIOD','REPORTER','PARTNER']).agg({'QUANTITY_KG':'sum','VALUE_EUR':'sum'}).reset_index(drop=False)
        result_primary = result_primary.rename(columns={'QUANTITY_KG' :'quantity','VALUE_EUR':'value'})
        result_refined = result_refined[['MATERIAL','PRODUCT','PERIOD','REPORTER','PARTNER','QUANTITY_KG','VALUE_EUR']].groupby(['MATERIAL','PRODUCT','PERIOD','REPORTER','PARTNER']).agg({'QUANTITY_KG':'sum','VALUE_EUR':'sum'}).reset_index(drop=False)
        result_refined = result_refined.rename(columns={'QUANTITY_KG' :'quantity','VALUE_EUR':'value'})  
        result_primary['PERIOD'] = ((result_primary['PERIOD']-52)/100).astype(int)
        result_primary['category'] = 'primary'
        result_refined['PERIOD'] = ((result_refined['PERIOD']-52)/100).astype(int)
        result_refined['category'] = 'refined'

        result_primary = result_primary.rename(columns={'REPORTER':'importer_country_name','PARTNER':'exporter_country_name','PERIOD':'date_year','MATERIAL':'material_name','PRODUCT':'cn8codes'})
        result_refined = result_refined.rename(columns={'REPORTER':'importer_country_name','PARTNER':'exporter_country_name','PERIOD':'date_year','MATERIAL':'material_name','PRODUCT':'cn8codes'})        
        result = pd.concat([result_primary,result_refined])
        # codes = [x for vals in EUISO3.values() for x in vals]   # found this way of turning a nested list into a flat list on stackexchange
        # result.loc[result['country_name'].isin(codes)]          # if we want to filter only EU declaring countries. 
        
        # assemble total df
        df = pd.concat([df,result])

    #convert kg to t
    df['quantity'] = df['quantity'] / 1000
    df['unit'] = 't'    
    df['value_unit'] = 'euro'    
    
    # df = df.drop(index=df.loc[pd.isna(df['country_name'])].index)
    df['source_name'] = source
    df['publish_year'] = publish_year
    df['source_name'] = source

    print('translating the eurostat files ... this might take a moment ...')
    # df.to_csv('temp_outputs/eurostat_raw.csv',index=False)
    df = standardize(df,ccodes=True, )
    
    return df

import os
import openpyxl
import regex as re
import numpy as np
import pandas as pd
from critmat.data_processing.translation import *
from openpyxl.styles import Alignment
from critmat.data_processing.get_usgs_myb_helpers import *
'''
This function processes the USGS Mineral Yearbook data, which is publicly available on the USGS website.
For more information on the data itself see USGS_Readme.md in the input_data directory.
'''

def get_usgs_myb(file,source,db_out=False,cut_outdated=False,cut_subtotal=False):
    '''Converts the entire usgs archive files (provide path and source string) to one dataframe. The files have to be xlsx, not xls (see xls2xlsx).''' 
    # Each file_year/publish_year contains five date_years. We used to overwrite the older ones with newer ones and for that, 
    # the files had to be in chronological order from oldest to most recent information. Now that's no longer necessary but the 
    # output df is 5x as long
    full_df = pd.DataFrame() # full_df will be the end result
    full_log = pd.DataFrame()
    error_log = {}
    print('Processing USGS file ' + str(file) + '...\n')

    df = pd.DataFrame() # df will be the end result
    error_log[file] = []
    
    if file_year:= re.search('20[0-9][0-9]',file):
        file_year = int(file_year.group(0))
    elif file_year:= re.search('0[0-9]',file):
        file_year = int('20' + file_year.group(0))
    else:
        print(str(file) + " contains no year information skipping...")
        error_log[file] += ["File name does not contain year"]
        return pd.DataFrame()

    # Load workbook and check for categories (mining or refining)
    wb = openpyxl.load_workbook(file,read_only=True)
    production_sheets = checkExcelIntegrity(wb)


    # what = checkWhatCategory(wb)
    if production_sheets == {}:
        print('no production data found for ' + file)
        error_log[file] += ["File failed integretiy check, or is missing production data"]
        return pd.DataFrame() 

    file_log =  pd.DataFrame.from_dict(production_sheets,orient='index').copy()
    file_log['file_name'] = file
    file_log['file_year'] = file_year
    del file_log['indents'] #just to keep the output readable

    for sheet, details in production_sheets.items(): # LOOP OVER SHEETS
        if db_out: 
            category = details['db_category']
            material = details['title_material']
        else: 
            category = details['title_category'] #This should be replaced with a more advanced category detection in the future 
            material = details['title_material']
        unit = details['unit']
        skip_rows = int(details['datacolumns_cell'][-1]) -1
        indents = details['indents']
        last_row = details['last_row']

        #not used
        # Read indents with openpyxl
        # indents, last_row, unit = readIndents(ws,skip_rows)

        # Send the unit openpyxl read through the translation function along with the identifier for debugging
        thisUnit = understand_units(pd.Series(unit.lower()),f"{file},{sheet}")[0]
        # Read data with pandas as dataframe
        try:
            data = readAndProcess(file,sheet,skip_rows,last_row,details['edgecases'])
        except Exception as e: 
            print(e)
            error_log[file] += [e]
            continue

        try: # If this (ugly) check causes an error, there must be a problem with the formatting. 
            emptyrows = data.loc[(pd.isna(data.iloc[:,-1])) & (pd.isna(data.iloc[:,-2])) 
                & (pd.isna(data.iloc[:,-3])) & (pd.isna(data.iloc[:,-4])) & (pd.isna(data.iloc[:,-5]))].index.values
        except:
            print('Skip row error: check the file for format issues',file,category,sheet)
            error_log[file] += ['Skip row error: check the file for format issues']
            continue
        df = takeCareOfAllRegularMaterialsKeepInfos(df,data,sheet,indents,emptyrows,material,thisUnit,category,file_year,details['extra_columns'])
    if df.empty:
        return None, None #legacy?
    else:
        if cut_outdated: df = df.loc[df.groupby(['country_name','material_name','category','date_year'])['publish_year'].idxmax()]
        if cut_subtotal:
            lengths = df["total_note"].str.len()
            df = df[lengths == df.groupby(['country_name','material_name','category','date_year','publish_year'])['total_note'].transform(lambda x: x.str.len().max())]
        df = format_usgsarchive(df,source)
        # df = standardize(df,cnames=True,material=True,quantity_to_t=True,output=True)
        df = standardize(df,cnames=True,quantity_to_t=True,material=True,output=True)
        # df.to_csv('files_usgsarch/' + str(subfolder) + '.csv',index=False)
        # subfolder_log.to_csv('files_usgsarch/' + str(subfolder) + '_log.csv')
        full_df = pd.concat([full_df,df])
        full_log = pd.concat([full_log,file_log])

    # if testing:
    #     full_log.to_csv('files_usgsarch/test_log.csv')
    #     pd.DataFrame.from_dict(error_log,orient='index').dropna(how='any').to_csv('files_usgsarch/test_error_log.csv')
    # else:
    #     full_log.to_csv('files_usgsarch/full_log.csv')
    #     pd.DataFrame.from_dict(error_log,orient='index').dropna(how='any').to_csv('files_usgsarch/full_error_log.csv')

    if db_out:
        full_df = standardize(full_df,material=True,output=True)
        full_df = prepare_for_db(full_df)
    
    return full_df, full_log


def format_usgsarchive(df,source):
    '''To avoid having to run the long get_usgsarchive, format_ can read in a local file with the 
    unprocessed results (usgs_archive_raw.csv) that was stored at the end of get_usgsarchive.'''
    print('post-processing...\n')
    df = df.drop(index=df.loc[pd.isna(df['country_name'])].index,axis=0)
    df = df.drop(index=df.loc[df['material_name']==''].index,axis=0)
    df['country_name'] = df['country_name'].str.replace('\s*$','',regex=True) # like strip, throw out trailing spaces
    df = df.drop(index=df.loc[df['country_name']==''].index,axis=0)
    df = df.drop(index=df.loc[df['country_name'].str.contains('total',case=False,regex=True)].index,axis=0)
    df = df.drop(index=df.loc[df['country_name'].str.contains('country',case=False,regex=True)].index,axis=0)
    df = df.drop(index=df.loc[df['country_name'].str.contains('footnotes',case=False,regex=True)].index,axis=0)
    df['country_name'] = edgecaseCountries(df['country_name'].to_list())
    df['date_year'] = edgecaseYears(df['date_year'].to_list())
    df = df.drop(index=df.loc[pd.isna(df['country_name'])].index)  # important. Drop rows where the country, material, or year don't exist.
    df = df.drop(index=df.loc[pd.isna(df['material_name'])].index)
    df = df.drop(index=df.loc[df['date_year'] == ''].index,axis=0)
    df = df.drop(index=df.loc[df['quantity'] == 0].index,axis=0)    #New line to drop 0 Values before database
    df = df.sort_values(by=['material_name','country_name','publish_year']).reset_index(drop=True)
    df['source_name'] = source

    return df

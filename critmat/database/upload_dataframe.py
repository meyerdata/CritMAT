import pandas as pd
from sqlalchemy import *
from sqlalchemy.exc import IntegrityError, DataError, CompileError
import numpy as np

def upload_dataframe(sourcedf, sql_table, connection, print_error=False):
    '''Function to upload each row of the dataframe sourcedf into the sql_table.
        If the unique constraints forbid upload of a row, that row will not be uploaded, other rows might be uploaded.
        Each row of dataframe is converted to a dict (work_dict) to enable easier upload.
        Function also checks for ForeignKeys and tries to assign them by sqlquery to the FKs table.
        This works by comparing the country, or material column, these are removed after.
    '''
    print('##############################################################################')
    print('Preparing ' + str(sql_table) + ' data for upload...')

    upload_count = 0
    fail_count1 = 0
    fail_count2 = 0
    sourcedf = pd.DataFrame(sourcedf)

    #Pull basetables
    meta_obj = MetaData()
    meta_obj.reflect(bind=connection)

    columns_with_fk = [col for col in sql_table.columns if len(col.foreign_keys)!=0]
    columns_without_fk = [(str(col).split('.')[-1]) for col in sql_table.columns if len(col.foreign_keys)==0 and not col.primary_key]


    for col in columns_with_fk:
        [key] = col.foreign_keys
        [fk_table, fk_column_id] = str(key.column).split('.')
        [table, column_id] = str(col).split('.')        

        #base_table is the table containing the allocation of names (material, or country for example) to ids
        base_table =  pd.read_sql(select(meta_obj.tables[fk_table]), connection)
        #check is a copy of the names that will be replaced by ids
        check = sourcedf[str(column_id[:-3]) + '_name'].copy()

        #the following pandas merges base_table and the input dataframe (sourcedf) based on the names (material, or country for example). Names not found in both tables will be deleted
        sourcedf = sourcedf.merge(base_table.loc[:,['id','name']], left_on=sourcedf[str(column_id[:-3]) + '_name'].str.lower(),right_on=base_table['name'].str.lower(),how='inner')

        if (~check.isin(sourcedf[str(column_id[:-3]) + '_name'])).any():
            print("WARNING the following names could not be assinged a " + str(column_id))
            print(list(check[~check.isin(sourcedf[str(column_id[:-3]) + '_name'])].unique()))

        sourcedf.drop(['key_0'], axis=1, inplace=True)  #Key_0 is a byproduct of the lowercase merge and can be removed
        sourcedf.drop([str(column_id[:-3]) + '_name','name'], axis=1, inplace=True) #removes the previously used name columns, since the id columns exist now
        sourcedf.rename(columns={'id': column_id}, inplace=True)        

    #Preprocessing of array type columns (might cause problems with other arrays)
    array_columns = []
    for col in sql_table.columns:
        try:
            if issubclass(type(col.type), ARRAY):
                sourcedf[col.name] = sourcedf[col.name].str.split(',').fillna('')
                array_columns.append(col.name)

                sourcedf.to_csv('test_array.csv')
        except (AttributeError, TypeError):
            pass

    for idx, row in sourcedf.iterrows():
        #Convert each non-NaN row of the dataframe to a dict and try to upload
        #NaN is excluded as most sql datatypes dont support it and NaN holds no information
        write_dict = row[~row.isna()].to_dict()

        #THIS IS NOT PROVEN TO FUNCTION PROPERLY, BUT SHOULD BE SEEN AS THE FIRST IDEA OF A POTENTIAL FUNCTION
        #CURRENTLY THE SAME FUNCTION IS HANDELD BY A TRIGGER
        # update_check_query = select(sql_table)
        # for key, value in write_dict.items():
        #     if key != 'publish_date':
        #         update_check_query = update_check_query.where(getattr(sql_table.c, key) == value)

        #     existing_record = connection.execute(update_check_query).fetchone()
        
        #     if existing_record:
        #         # Compare dates and delete the older one
        #         if existing_record .publish_date < write_dict['publish_date']:
        #             connection.delete(existing_record)
        #             connection.commit()  # commit deletion

        #     # Insert the new record
        #     connection.add(write_dict)
        #     connection.commit() 
        try:
            connection.execute(insert(sql_table).values(write_dict))
            connection.commit()
            upload_count += 1
        except IntegrityError as ex:
            if print_error:
                print(ex.orig)
                print(ex.statement)
            connection.rollback()
            fail_count1 += 1

    print('Uploaded ' + str(upload_count) + ' new data points to table ' + str(sql_table))
    print('Failed to upload ' + str(fail_count1) + ' new data points to table ' + str(sql_table) + ' due to unique constrains')


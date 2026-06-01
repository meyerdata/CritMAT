import regex as re
import numpy as np
import pandas as pd

# standardize, understand_units, convert_to_t, standard_material_names, standard_country_names

def standardize(data,ccodes=False,cnames=False,material=False,quantity_to_t=False,output=False):
    '''Takes a dataframe and can standardize any number of the following columns:
    "country_name", "material_name", "production_primary(_unit)", "production_refined(_unit)", "reserves(_unit)". 
    It then prints entries that could not be standardized but are stored anyway and returns data of the same shape.
    Note: The country conversion can try to match country names or country codes. If the data is 
    consistent, choosing one and omitting the other is faster and more reliable.'''
    problemunits = {}
    problemcountries = {}
    problemmats = {}

    if ccodes or cnames:
        for columns in data.columns[data.columns.str.endswith('country_name')]:
            data[columns],problemcountries = standard_country_name(data[columns],problemcountries,ccodes=ccodes,cnames=cnames)
    if material:
        for columns in data.columns[data.columns.str.endswith('material_name')]:
            data[columns],problemmats = standard_material_name(data[columns],problemmats)
            
    # this is a lot shorter now that we only have a quantity column
    if quantity_to_t:
        if ('quantity' in data.columns) and ('unit' in data.columns):
            data['quantity'],data['unit'],problemunits = convert_to_t(data['quantity'],data['unit'],problemunits)
        else:
            print('No quantity data found')
    
    if output: 
        if len(problemunits) > 0:
            print(f'\n{len(problemunits)} unknown units were replaced by NaN/empty: ', end='')
            for p,n in problemunits.items():  
                print(f"{p} ({n}x)",end=', ')
            print()
        if len(problemcountries) > 0:
            print(f'\n{len(problemcountries)} unknown countries were stored anyway: ',end='')
            for p,n in problemcountries.items():
                print(f"{p} ({n}x)",end=', ') 
            print()
        if len(problemmats) > 0:
            print(f'\n{len(problemmats)} unknown materials were stored anyway: ',end='')
            for p,n in problemmats.items():
                print(f"{p} ({n}x)",end=', ') 
            print()
        # note that the number of times (n) that an unknown value was found may not 
        # be accurate anymore after doing concatenation or unique operations
    return data

def understand_units(notes,identifier,sss=(0,40,1)):
    '''Takes a pandas series (column of dataframe) and returns one of the same shape, 
    where unit abbreviations have been inferred from text. The identifier can be useful
    while debugging (pass for example the file name) because it is printed if strange units are inferred.
    sss is short for "start,stop,step" and is an optional tuple to limit the area of the string that is 
    searched for units. The default is to look from the beginning to the fortieth character. This is 
    not robust but filters out more detailed explanations pretty reasonably.'''
    # function is used by usgs and usgsarchive
    units = pd.Series('',index=range(len(notes)),dtype=str).reset_index(drop=True)
    # Units is a series of the same shape as the notes that were passed in consisting
    # of only empty strings. Then, by checking regular expressions, prefixes and 
    # units are appended. 
    notes = notes.astype(str).str.strip()
    notes = notes.astype(str).str.slice(sss[0],sss[1],sss[2]) 
    units.loc[notes.str.contains('billion',case=False,na=False)] += 'G'
    units.loc[notes.str.contains('million',case=False,na=False)] += 'M'
    units.loc[notes.str.contains('thousand',case=False,na=False)] += 'k'
    units.loc[notes.str.contains('hundred',case=False,na=False)] += 'h'

    # remove this annoying detour as soon as pandas fixes the bug about extracting capture groups (https://github.com/pandas-dev/pandas/issues/56798) 
    # and instead go back to the way more readable version: 
    # units.loc[notes.str.contains('(^|\s)ton',case=False,na=False)] += 't'
    idx = notes.str.extract('(^|\s)ton') 
    idx2 = pd.Series([False]*idx.shape[0])
    idx2.loc[~pd.isna(idx).values] = True
    units.loc[idx2.values] += 't'

    units.loc[notes.str.contains('kilogram',case=False,na=False)] += 'kg'
    units.loc[notes.str.contains('carat',case=False,na=False)] += 'ct'
    units.loc[notes.str.contains('cubic m',case=False,na=False)] += 'm3'
    units.loc[notes.str.contains('cm',case=False,na=False)] += 'm3'
    
    if units.str.contains('GM').any() or units.str.contains('Mk').any() or units.str.contains('kh').any():
        print('Weird unit at',identifier)
    units[units==''] = pd.NA # Like this, the update method later only overwrites units that were made more 
    # concrete by these notes; if this wasn't here, an empty string would overwrite whatever was there before. 
    return units


def convert_to_t(values,units,problemunits):
    '''Takes values and units as pd.Series (columns of a dataframe) and problemunits as a dictionary. 
    Converts the values to the standard units (t, m3, ct) and counts how often unknown units occur.
    Returns values and units of the same shape and problemunits for print output in main standardize function.''' 
    pd.options.mode.copy_on_write = True # I've tried without this, but for some reason that causes a flood of SettingWithCopyWarnings. 

    # Convert all values to one of the three base units (tons, cubic meters, carat) 
    # and also write this new unit in the corresponding places. 
    values.loc[units.str.contains('^kg',case=False,na=False)] /= 1000
    units.loc[units.str.contains('^kg',case=False,na=False)] ='t'
    values.loc[units.str.contains('^kt',case=False,na=False)] *= 1000
    units.loc[units.str.contains('^kt',case=False,na=False)] ='t'
    values.loc[units.str.contains('^mt',case=False,na=False)] *= 1_000_000
    units.loc[units.str.contains('^mt',case=False,na=False)] ='t'
    values.loc[units.str.contains('^mmt',case=False,na=False)] *= 1_000_000
    units.loc[units.str.contains('^mmt',case=False,na=False)] ='t'
    values.loc[units.str.contains('^gt',case=False,na=False)] *= 1_000_000_000
    units.loc[units.str.contains('^gt',case=False,na=False)] ='t'
    units.loc[units.str.contains('^metr(\.)? t',case=False,na=False)] = 't'
    units.loc[units.str.contains('^metr(\.)?t',case=False,na=False)] = 't'

    units.loc[units.str.contains('^tonnes',case=False,na=False)] = 't'
    values.loc[units.str.contains('^kilograms',case=False,na=False)] /= 1000
    units.loc[units.str.contains('^kilograms',case=False,na=False)] ='t'
    units.loc[units.str.contains('^Carats',case=False,na=False)] = 'ct'
    values.loc[units.str.contains('^million cubic metres',case=False,na=False)] *= 1_000_000
    units.loc[units.str.contains('^million cubic metres',case=False,na=False)] ='m3'

    values.loc[units.str.contains('^kct',case=False,na=False)] *= 1000
    units.loc[units.str.contains('^kct',case=False,na=False)] ='ct'
    values.loc[units.str.contains('^mct',case=False,na=False)] *= 1_000_000
    units.loc[units.str.contains('^mct',case=False,na=False)] ='ct'
    values.loc[units.str.contains('^mio m(\^)?3',case=False,na=False)] *= 1_000_000
    units.loc[units.str.contains('^mio m(\^)?3',case=False,na=False)] ='m3'
    values.loc[units.str.contains('^mcm',case=False,na=False)] *= 1_000_000
    units.loc[units.str.contains('^mcm',case=False,na=False)] ='m3'
    values.loc[units.str.contains('^hl',case=False,na=False)] /= 10
    units.loc[units.str.contains('^hl',case=False,na=False)] = 'm3'
    values.loc[units.str.contains('^l',case=False,na=False)] /= 1000
    units.loc[units.str.contains('^l',case=False,na=False)] ='m3'
        
    # Round to whole number but leave as float to accomodate NaNs
    values = values.astype(float).round(0) 
    
    # Then, drop all base units (and NaNs), leaving in "theRest" only units 
    # without a corresponding standard name. Those units get written to the 
    # problemunits dictionary along with a count. 
    droppable = []
    droppable.extend(units.loc[units=='t'].index.values)
    droppable.extend(units.loc[units=='m3'].index.values)
    droppable.extend(units.loc[units=='ct'].index.values)
    droppable.extend(units.loc[pd.isna(units)].index.values)
    theRest = units.drop(index=droppable).copy()
    for unit in theRest:
        if unit in problemunits:
            problemunits[unit] += 1
        else:
            problemunits[unit] = 1
            
    return values,units,problemunits

        
def standard_material_name(namedf,problemmats):
    '''Takes a pandas Series (namedf) and returns it (same dimensions) after converting
    every name to the standard name or leaving the name unchanged if a standard name 
    could not be found. In that case, that material got noted in the dictionary problemmats
    for print logging in the main standardize function.'''

    mats = {'Abrasives': ['abras'], 'Aluminium': ['Al','alumi','alum','aluminum','aluminium'], 'Antimony': ['Sb','antim','Antimon'], 
        'Arsenic': ['As','arsen'], 'Asbestos': ['asbes','Asbest'], 'Baryte': ['barit','barite','Bariumsulfat','Barium'], 
        'Bauxite': ['bauxi','Bauxit'], 'Beryllium': ['Be','beryl'], 'Bismuth': ['Bi','bismu','Bismut'], 'Bentonite': ['bento'], 
        'Bromine': ['bromi'], 'Boron': ['B','boron','Bor','borate','borates','boron-borates','Boron Minerals'], 'Cadmium': ['Cd','cadmi'], 
        'Cement': ['cemen','Zement'], 'Chromium': ['Cr2O3','Chrom','chrom'], 'Clays': ['clays'], 'Cobalt': ['Co','cobal'], 
        'Copper': ['Cu','coppe','Kupfer'], 'Coking Coal': ['coal'], 'Diamonds?': ['diamo','Gem', 'Diamonds'], 'Gemstones?': ['gemst'], 
        'Diatomite': ['diato'], 'Iron Ore': ['feste','Stahl','steel','feore','Iron Ore','Eisenerz','Fe','iron','Eisen'], 'Iron Oxide Pigments?': ['fepig'], 
        #old IRON 'Iron Ore?': ['feore','Iron Ore','Eisenerz'], 'Iron and Steel?': ['feste','Stahl'], 'Iron Oxide Pigments?': ['fepig'], 'Iron': ['Fe','iron','Eisen'],
        'Feldspar': ['felds'], 'Fluorspar': ['fluor'], 'Garnet?': ['garne'], 'Gallium': ['Ga','galli'], 'Germanium': ['Ge','germa'], 
        'Gold': ['Au','gold'], 'Graphite': ['graph','Graphit'], 'Gypsum': ['gypsu', 'Gypsum and Anhydrite'], 'Helium': ['He','heliu'], 
        'Hafnium': ['hafni'], 'Indium': ['In','indiu'], 'Iodine': ['iodin'], 'Kaolin': ['China-Clay','Kaolin clay'], 'Kyanite': ['kyani'], 
        'Lead': ['Pb','lead','Blei'], 'Lignite': ['ligni'], 'Lime': ['lime','Limestone'], 'Lithium': ['Li','lithi','Li2O'], 'Magnesium': ['mgcomp','Magnesium Compounds'], 
        'Magnesium Metal': ['mgmet'], 'Magnesite': ['magnesite'], 'Mercury': ['Hg','mercu','Quecksilber'], 'Manganese': ['Mn','manga','Mangan'], 'Mica?': ['mica'], 
        'Molybdenum': ['Mo','molyb','Molybdän'], 'Natural Gas': ['gas'], 'Nickel': ['Ni','nicke'], 'Nitrogen': ['nitro','Stickstoff'], #N/Ammo checken???
        'Niobium': ['Nb','Nb2O5','niobi','Niob'], 'Peat': ['peat','Torf'], 'Oil Sands': ['part of Petroleum'], 'Oil Shales': ['oil shales'], 
        'Palladium': ['Pd','palla','palladium'], 'Petroleum': ['petrol'], 'Platinum': ['platinum','Pt','plati','Platin'], 'Perlite': ['perli'], 
        'Phosphate Rock': ['P2O5','phosp','Phosphatgestein'], 'Phosphate': ['Phosphor'], 'Potash': ['K2O','potas'], 'Pumic': ['pumic'], 
        'Rare Earths': ['REO','REE','raree','seltene Erden'], 'Rhenium (pgm/titan?)': ['Re','rheni'], 'Rhodium (pgm/titan?)': ['rhodium','Rh','rhodi'], 
        'Ruthenium (pgm/titan?)': ['ruthenium'], 'Rutile (pgm/titan?)': ['rutile'], 'Salt': ['salt','rock, brines, marine','Salz'],
        'Sand': ['sandi','Industrieller Sand und Kies'], 'Selenium': ['Se','selen'], 'Silicon Metal': ['Si','silicon','simet','Silizium','Silicium'],
        'Silica Sand': ['Siliciumdioxid','silica'],'Silver': ['Ag','silve','Silber'], 'Soda Ash': ['sodaa'], 'Strontium': ['Sr','stron'], 
        'Sulfur': ['S','sulfu','sulphur','elementar & industrial','Schwefel'], 'Steam Coal': ['steam coal'], 'Stone': ['stond'], 
        'Talc, Steatite & Pyrophyllite': ['talc'], 'Tantalum': ['Ta','Ta2O5','tanta','Tantal'], 'Tellurium': ['Te','tellu','Tellur'], 'Timin': ['timin'], 
        'Tin': ['Sn','tin','Zinn'], 'Iridium (pgm/titan?)': ['iridium'], 'Titanium': ['Ti','TiO2','titan'], 'Ilmenite and leucoxene (titanium)': ['ilmenite and leucoxene'], 
        'Titanium Slag': ['titaniferous slag','titaniferous slage','titanium slag','titanium slage'], 'Tungsten': ['W','tungs','Wolfram'], 'Uranium': ['U','U3O8','Uran'], 
        'Selenium and Tellurium': ['selenium and tellurium'], 'Vanadium': ['V','vanad'], 'Vermiculite': ['vermi'], 'Wollastonite': ['wolla','wollastonite'], 
        'Zeolites': ['zeoli'], 'Zinc': ['Zn','zinc','Zink'], 'Zirconium': ['Zr','zirco','Zircon','Zirkonium'], 'Zirconium and Hafnium?': ['zirco-hafni']
    }
    
    if type(namedf) != pd.Series:
        print('Material conversion needs a pd Series! No conversion took place.')
        return namedf,problemmats
    
    namedf.str.replace('(metall)','') # quick fix for aluminium
    namedf = namedf.str.replace('[^ A-z]','',regex=True)
    namedf = namedf.str.replace(' +',' ',regex=True)
    namedf = namedf.str.strip()
    uniquenames = namedf.unique()
    # Loop over all unique material names that were passed. 
    new_names = []
    for name in uniquenames:
        if name == np.nan: continue
        found = 0            
        for standard, alternatives in mats.items():
            # Loop over all standard,alternative name pairs in the giant dictionary. 
            if name.lower() == standard.lower():
                new_names.append(standard)
                found = 1            
            else:
                # Loop over the alternatives. When found, break out of this loop.
                for alternative in alternatives: 
                    if name.lower() == alternative.lower():
                        new_names.append(standard)
                        found = 1
                        break
            # When found, the loop over the dictionary can be interrupted. 
            if found == 1:
                break
        # If, after looping over the entire dictionary, the material wasn't found, 
        # it's a problematic material.
        if found == 0:
            new_names.append(name)
            if name in problemmats:
                problemmats[name] += 1
            else:
                problemmats[name] = 1
    

    # The above loop is computationally expensive and therefore only for the 
    # unique materials, all occurrences of which are then replaced. 
    for i in range(len(new_names)):
        namedf.replace(to_replace=uniquenames[i],value=new_names[i],inplace=True)
    return namedf,problemmats


def standard_country_name(ser,problemcountries,ccodes=False,cnames=False):
    '''The function takes a column of a dataframe, loops over each element and 
    tries to match it to a standard country name. It returns a list of the same
    length as the input.'''
    
    # CODES AND NAMES
    # countries = {'United States': ['^(?!.*islands).*united.?states|^u\\.?s\\.?a\\.?$|^u\\.?s\\.?$', 'USA', 'vereinigte staaten', 'amerika', 'US'], 
    # 'China': ['^(?!repub)(?!taiwan)(?!hong.*kong)(?!macao).*china(?!.*hong.*kong)(?!.*macao)|^PRC$', 'CHN','CN'], 'Brazil': ['brazil', 'BRA', 'brasilien', 'BR'], 'Canada': ['canada', 'CAN', 'kanada', 'CA'], 
    # 'Australia': ['australia', 'AUS', 'australien', 'AU'], 'India': ['^(?!\\D*(?:bassas))\\D*india(?!.*ocea)(?!na)', 'IND', 'indien', 'IN'], 
    # 'United Arab Emirates': ['emirates|^u\\.?a\\.?e\\.?$|united.?arab.?em', 'ARE', 'vae', 'vereinigte arab', 'AE'], 'Argentina': ['argentin', 'ARG', 'AR'], 'Portugal': ['portugal|portuguese', 'PRT', 'PT'],
    # 'United Kingdom': ['.*(united.?kingdom|britain|^u\\.?k\\.?$|gb)|england', 'GBR', 'gro[ss|ß]britannien', 'GB'], 'Germany': ['^(?!e|w)(fed)?.*germany(?!,? *e|,? *w)(,? *)(\\bfed)?', 'DEU', 'deutschland', 'DE'], 
    # 'France': ['^(?!.*\\bdep).*france|french.?republic|\\bgaul', 'FRA', 'frankreich', 'FR'], 'Afghanistan': ['afghan', 'AFG', 'AF'], 'Chile': ['\\bchile', 'CHL', 'CL'],  'Albania': ['albania', 'ALB', 'albanien', 'AL'], 
    # 'Algeria': ['algeria', 'DZA', 'algerien', 'DZ'], 'Angola': ['angola', 'AGO', 'AO'], 'Armenia': ['armenia', 'ARM', 'armenien', 'AM'], 'Türkiye': ['t[ü|u]rk[i|e]y','Turkey', 'TUR', 't[ü|ue]rkei', 'TR'], 
    # 'Peru': ['peru', 'PER', 'PE'], 'Austria': ['austria', 'AUT', '[oe|ö]sterreich', 'AT'], 'Azerbaijan': ['azerbaijan', 'AZE', 'aserbaidschan', 'AZ'], 'Bahamas': ['bahamas', 'BHS', 'BS'], 'Bahrain': ['bahrain', 'BHR', 'BH'], 
    # 'Bangladesh': ['bangladesh|^(?=.*east).*paki?stan', 'BGD', 'bangladesch', 'BD'], 'Barbados': ['barbados', 'BRB', 'BB'], 'Belarus': ['belarus|byelo', 'BLR', 'wei[ss|ß]russland', 'BY'], 'Belgium': ['^(?!.*luxem).*belgium', 'BEL', 'belgien', 'BE'], 
    # 'Belize': ['belize|^(?=.*british).*honduras', 'BLZ', 'BZ'], 'Benin': ['benin|dahome', 'BEN', 'BJ'], 'Bermuda': ['bermuda', 'BMU', 'BM'], 'Bhutan': ['bhutan', 'BTN', 'BT'], 'Bolivia': ['BOL', 'bolivien', 'BO'],  
    # 'Sweden': ['swedish|sweden(?!.*except)', 'SWE', 'schweden', 'SE'], 'Bosnia and Herzegovina': ['herzegovina|bosnia', 'BIH', 'bosnien|herzegowina', 'BA'], 'Botswana': ['botswana|bechuana|botsuana', 'BWA', 'BW'], 
    # 'Brunei Darussalam': ['brunei', 'BRN', 'BN'], 'Bulgaria': ['BGR', 'bulgarien', 'BG'], 'Burkina Faso': ['burkina|\\bfaso|upper.?volta', 'BFA', 'BF'], 'Burundi': ['BDI', 'BI'], 'Cabo Verde': ['(cabo|cape) *verde', 'CPV', 'kap verde', 'CV'], 
    # 'Cambodia': ['cambodia|kampuchea|khmer|^p\\.?r\\.?k\\.?$', 'KHM', 'kambodscha', 'KH'], 'Cameroon': ['CMR', 'kamerun', 'CM'], 'Colombia': ['COL', 'kolumbien', 'CO'], 
    # 'Congo Republic': ['^(?!.*\\bdem)(?!.*\\bdr)(?!.*kinshasa)(?!.*zaire)(?!.*belg)(?!.*l\\w{1,2}opoldville)(?!.*free)(^rep.*).*\\bcongo.*(?!.*\\bdem)(?!.*\\bdr).*|\\bwest.*congo|^congo[,;\\s]*(?!.*dem)rep.*?$|^congo$|\\bcongo.*brazza.*', 'COG', 'Congo Rep\S', 'CG'], 
    # 'Costa Rica': ['costa.?rica', 'CRI', 'CR'], 'Cote dIvoire': ['.*(ivoire|ivory)', 'CIV', 'elfenbeink[ü|ue]ste', 'CI'], 'Croatia': ['croatia|hrvatska', 'HRV', 'kroatien', 'HR'], 'Cuba': ['\\bcuba', 'CUB', 'kuba', 'CU'], 
    # 'Cyprus': ['cyprus', 'CYP', 'zypern', 'CY'], 'Guatemala': ['guatemala', 'GTM', 'GT'], 'Czechia': ['^(?=.*rep).*czech.*|czechia|bohemia|.*czech.*', 'CZE', 'tschechi', 'CZ'], 'Denmark': ['denmark', 'DNK', 'd[ä|ae]nemark', 'DK'], 
    # 'Djibouti': ['djibouti', 'DJI', 'dschibuti', 'DJ'], 'Dominica': ['dominica(?!n)', 'DMA', 'DM'], 'Dominican Republic': ['domini[c|k]an', 'DOM', 'DO'], 
    # 'DR Congo': ['\\bdem.*congo|congo.*\\bdem|congo.*\\bdr|\\bdr.*congo|\\bd\\.?r\\.?c|\\bd\\.?r\\.?o\\.?c|\\br\\.?d\\.?c|belgian.?congo|congo.?free.?state|kinshasa|zaire|l\\w{1,2}opoldville|^the\\ congo$|^RDC$|^DROC$|\\bcongo.*dem.*', 'COD', 'Congo Kinshasa', 'DR Congo', 'DR Kongo', 'kongo dem', 'CD'], 
    # 'Ecuador': ['ecuador', 'ECU', 'EC'], 'Egypt': ['egypt', 'EGY', '[ä|ae]gypten', 'EG'], 'El Salvador': ['el.?salvador', 'SLV', 'SV'], 'Equatorial Guinea': ['guine.*eq|eq.*guine|^(?=.*span).*guinea', 'GNQ', '[ae|ä]quatorialguinea', 'GQ'], 
    # 'Eritrea': ['eritrea', 'ERI', 'ER'], 'Estonia': ['estonia', 'EST', 'estland', 'EE'], 'Eswatini': ['swaziland|eswatini', 'SWZ', 'SZ'], 'Ethiopia': ['ethiopia|abyssinia', 'ETH', '[ä|ae]thiopien', 'ET'], 'Fiji': ['fiji', 'FJI', 'fidschi', 'FJ'], 
    # 'Finland': ['finland', 'FIN', 'finnland', 'FI'], 'French Guiana': ['^(?=.*french).*gu(i|y)ana|^(?!.*brit)(?!.*dut).*guiana', 'GUF', 'franz[ösisch]?[.]?[ ]?guyana', 'GF'], 'Gabon': ['gab(o|u)n', 'GAB', 'gabun', 'GA'], 
    # 'Gambia': ['gambia', 'GMB', 'the gambia', 'GM'], 'Georgia': ['^(?!.*south).*georgia(?!.*US.*)', 'GEO', 'georgien', 'GE'], 'Ghana': ['ghana|gold.?coast', 'GHA', 'GH'], 'Gibraltar': ['gibraltar', 'GIB', 'GI'], 
    # 'Greece': ['greece|hellenic|hellas', 'GRC', 'griechenland', 'GR'], 'Greenland': ['greenland', 'GRL', 'gr[ö|oe]nland', 'GL'], 'Grenada': ['grenada', 'GRD', 'GD'], 'Guadeloupe': ['guadeloupe', 'GLP', 'GP'], 
    # 'Guinea': ['^(?!.*eq)(?!.*span)(?!.*bissau)(?!.*pap)(?!.*new)(?!p.*n.*).*guinea', 'GIN', 'GN'], 'Guinea-Bissau': ['^(.*portu).*gu(i|y)nea|gu(y|i)nea.*bissau', 'GNB', 'GW'], 'Guyana': ['^(?!.*fren)(?!.*dut).*\\bguyana|^(.*brit).*gu(i|y)ana', 'GUY', 'GY'], 
    # 'Haiti': ['(ha(i|\\xef|\\xc3\\xaf)ti)', 'HTI', 'HT'], 'New Zealand': ['(new|n).*zealand', 'NZL', 'neuseeland', 'NZ'], 'Honduras': ['^(?!.*brit).*honduras', 'HND', 'HN'], 'Hong Kong': ['.*hong.*kong|hksar', 'HKG', 'HK'], 
    # 'Hungary': ['hungary', 'HUN', 'ungarn', 'HU'], 'Iceland': ['iceland', 'ISL', 'island', 'IS'], 'Indonesia': ['indonesia', 'IDN', 'indonesien', 'ID'], 'Iran': ['\\biran|persia', 'IRN', 'IR'], 'Iraq': ['\\biraq|mesopotamia', 'IRQ', 'irak', 'IQ'], 
    # 'Ireland': ['^(?!.*north.*).*ireland', 'IRL', 'irland', 'IE'], 'Saudi Arabia': ['\\bsa\\w*.?arabia', 'SAU', 'saudi-arabien', 'SA'], 'Israel': ['israel', 'ISR', 'IL'], 'Italy': ['.*italy|.*italia.*', 'ITA', 'italien', 'IT'], 
    # 'Jamaica': ['jamaica', 'JAM', 'jamaika', 'JM'], 'Japan': ['japan', 'JPN', 'JP'], 'Jersey': ['^(?!.*new).*jersey', 'JEY', 'JE'], 'Jordan': ['jordan[ien]?', 'JOR', 'JO'], 'Kazakhstan': ['kazak', 'KAZ', 'kasachstan', 'KZ'], 
    # 'Kenya': ['kenya|british.?east.?africa|east.?africa.?prot', 'KEN', 'kenia', 'KE'], 'Kiribati': ['kiribati', 'KIR', 'KI'], 'Kosovo': ['kosovo', 'XKX', 'XK'], 'Kuwait': ['kuwait', 'KWT', 'KW'], 'Kyrgyz Republic': ['kyrgyz|kirghiz', 'KGZ', 'KG'], 
    # 'Laos': ['\\blaos?\\b', 'LAO', 'LA'], 'Latvia': ['latvia', 'LVA', 'lettland', 'LV'], 'Lebanon': ['lebanon|lebanese', 'LBN', 'libanon', 'LB'], 'Lesotho': ['lesotho|basuto', 'LSO', 'LS'], 'Liberia': ['liberia', 'LBR', 'LR'], 
    # 'Libya': ['libya', 'LBY', 'libyen', 'LY'], 'Liechtenstein': ['liechtenstein', 'LIE', 'LI'], 'Lithuania': ['lithuania', 'LTU', 'litauen', 'LT'], 'Luxembourg': ['^(?!.*belg).*luxem', 'LUX', 'luxemburg', 'LU'], 'Macau': ['.*maca(o|u)', 'MAC', 'MO'], 
    # 'North Macedonia': ['macedonia|^f\\.?y\\.?r\\.?o\\.?m\\.?$', 'MKD', '(nord)?[ -]?mazedonien', 'MK'], 'Madagascar': ['madagascar|malagasy', 'MDG', 'madagaskar', 'MG'], 'Malawi': ['malawi|nyasa', 'MWI', 'MW'], 'Malaysia': ['malaysia', 'MYS', 'MY'], 
    # 'Maldives': ['maldive', 'MDV', 'malediwen', 'MV'], 'Mali': ['\\bmali\\b', 'MLI', 'ML'], 'Malta': ['\\bmalta', 'MLT', 'MT'], 'Mauritania': ['mauritania', 'MRT', 'mauretanien', 'MR'], 'Mauritius': ['mauritius', 'MUS', 'MU'], 
    # 'Mexico': ['^(?!.*new).*mexi(?!.*city)', 'MEX', 'mexiko', 'MX'], 'Moldova': ['moldov|b(a|e)ssarabia', 'MDA', 'moldau', 'moldawien', 'MD'], 'Monaco': ['monaco', 'MCO', 'MC'], 'Mongolia': ['mongolia', 'MNG', 'mongolei', 'MN'], 
    # 'Montenegro': ['^(?!.*serbia).*montenegro', 'MNE', 'ME'], 'Morocco': ['morocco|\\bmaroc', 'MAR', 'marokko', 'MA'], 'Mozambique': ['mozambique', 'MOZ', 'mosambik', 'MZ'], 'Myanmar': ['myanmar|burma', 'MMR', 'MM'], 'Namibia': ['namibia', 'NAM', 'NA'], 
    # 'Nauru': ['nauru', 'NRU', 'NR'], 'Nepal': ['nepal', 'NPL', 'NP'], 'Netherlands': ['^(?!.*\\bant)(?!.*\\bcarib).*netherlands', 'NLD', '(die )?niederlande', 'NL'], 'Venezuela': ['venezuela', 'VEN', 'VE'], 'New Caledonia': ['new.?caledonia', 'NCL', 'NC'], 'Nicaragua': ['nicaragua', 'NIC', 'NI'], 
    # 'Niger': ['\\bniger(?!ia)', 'NER', 'NE'], 'Nigeria': ['nigeria', 'NGA', 'NG'], 'Spain': ['spain', 'ESP', 'spanien', 'ES'], 'North Korea': ['^(?=.*dem).*\\bkorea|^(?=.*peo).*\\bkorea|^(?=.*nor).*\\bkorea|\\bd\\.?p\\.?r\\.|.*dpr.*|^n.*korea', 'PRK','Korea North', 'nordkorea', 'KP'], 
    # 'Norway': ['norway', 'NOR', 'norwegen', 'NO'], 'Oman': ['\\boman|trucial', 'OMN', 'OM'], 'Pakistan': ['^(?!.*east).*paki?stan', 'PAK', 'PK'], 'Palau': ['palau', 'PLW', 'PW'], 'Palestine': ['palestin|\\bgaza|west.?bank', 'PSE', 'PS'], 'Panama': ['PAN', 'PA'], 
    # 'Papua New Guinea': ['\\bp.*\\bn.*\\bguin.*|^p\\.?n\\.?g\\.?$|new.?guinea', 'PNG', 'papua-neuguinea', 'PG'], 'Paraguay': ['paraguay', 'PRY', 'PY'], 'Philippines': ['philippines', 'PHL', 'philippinen', 'PH'], 'Poland': ['POL', 'polen', 'PL'], 'Puerto Rico': ['puerto.?rico', 'PRI', 'PR'], 
    # 'Qatar': ['qatar', 'QAT', 'katar', 'QA'], 'Ukraine': ['ukrain', 'UKR', 'UA'], 'Romania': ['r(o|u|ou)mania', 'ROU', 'rum[ä|ae]nien', 'RO'], 'Russia': ['\\brussia', 'RUS', 'russland', 'RU'], 'Rwanda': ['rwanda', 'RWA', 'ruanda', 'RW'], 
    # 'Zimbabwe': ['zimbabwe|^(?!.*northern).*rhodesia', 'ZWE', 'simbabwe', 'ZW'], 'Senegal': ['senegal', 'SEN', 'SN'], 'Serbia': ['^(?!.*monte).*serbia.*', 'SRB', 'serbien', 'RS'], 'Seychelles': ['seychell', 'SYC', 'SC'], 'Sierra Leone': ['sierra', 'SLE', 'SL'], 
    # 'Singapore': ['singapore', 'SGP', 'singapur', 'SG'], 'Slovakia': ['^(?!.*cze).*slovak', 'SVK', 'slowakei', 'SK'], 'Slovenia': ['slovenia', 'SVN', 'slovenien', 'SI'], 'Solomon Islands': ['solomon', 'SLB', 'SB'], 'Somalia': ['somali', 'SOM', 'SO'], 
    # 'South Africa': ['\\bs(\\.|outh)(?!.*sahar).*africa|^r\\.?s\\.?a\\.?$', 'ZAF', 's[ü|ue]dafrika', 'ZA'], 'South Korea': ['^(?!.*dem)(?!.*peo)(?!.*nor)(?!.*n)(?!.*dpr)(?!d\\.p\\.r).*\\bkorea|\\br\\.?o\\.?k\\b', 'KOR', 'Korea Republic','s(ü|ue)dkorea', 'KR'], 
    # 'South Sudan': ['\\bs\\w*.?sudan', 'SSD', 'SS'], 'Sri Lanka': ['sri.?lanka|ceylon', 'LKA', 'LK'], 'Sudan': ['^(?!.*\\bs(?!u)).*sudan', 'SDN', 'SD'], 'Suriname': ['surinam|dutch.?gu(i|y)ana', 'SUR', 'SR'], 'Switzerland': ['switz|swiss', 'CHE', 'schweiz', 'CH'], 
    # 'Syria': ['syria', 'SYR', 'syrien', 'SY'], 'Taiwan': ['.*taiwan|.*taipei|.*formosa|^(?!.*\\bdem)(?!.*\\bpe)(?!.*\\bdr)(^rep.*).*\\bchina.*(?!.*\\bdem.*)(?!\\bpe.*)(?!.*\\bdr.*).*|^ROC$|^taiwan r\\.?o\\.?c\\.?$', 'TWN', 'TW'], 'Tajikistan': ['tajik', 'TJK', 'tadschikistan', 'TJ'],
    # 'Tanzania': ['tanzania(?!: zan.*)', 'TZA', 'tansania', 'TZ'], 'Thailand': ['thailand|\\bsiam', 'THA', 'TH'], 'Timor-Leste': ['^(?=.*leste).*timor|^(?=.*east).*timor', 'TLS', 'osttimor', 'TL'], 'Togo': ['togo', 'TGO', 'TG'], 'Trinidad and Tobago': ['trinidad|tobago', 'TTO', 'TT'],
    # 'Tunisia': ['tunisia', 'TUN', 'tunesien', 'TN'], 'Turkmenistan': ['turk-?men', 'TKM', 'TM'], 'Uganda': ['uganda', 'UGA', 'UG'], 'Sao Tome and Principe': ['(S|s)ao (T|t)ome', 'STP'], 'Aruba': ['^(?!.*bonaire).*\\baruba', 'ABW', 'AW'], 'Uruguay': ['uruguay', 'URY', 'UY','Ururguay'],
    # 'Uzbekistan': ['uzbek', 'UZB', 'usbekistan', 'UZ'], 'Vanuatu': ['vanuatu|new.?hebrides', 'VUT', 'VU'], 'Vietnam': ['^((?!n|s|.*republic)|(?=.*socialist)).*viet.?nam(?! *,? *n| *,? *s)', 'VNM', 'VN'], 'Central African Republic': ['central.?african.?rep.*', 'CAF', 'zentralafrikanische', 'CF'],
    # 'Chad': ['\\bchad', 'TCD', 'tschad', 'TD'], 'Christmas Island': ['christmas', 'CXR', 'CX'], 'Yemen': ['yemen', 'YEM', 'jemen', 'YE'], 'Zambia': ['zambia|northern.?rhodesia', 'ZMB', 'sambia', 'ZM'], 'Others': ['oth','Other countries'] 
    # }    

    # UNUSED
    # 'Aland Islands': ['\\b(a|å)land', 'ALA'], 'American Samoa': ['^(?=.*americ).*samoa', 'ASM'], 'Andorra': ['andorra', 'AND'], 'Anguilla': ['anguill?a', 'AIA'], 'Antarctica': ['antarctica', 'ATA', 'antarktis'], 
    # 'Antigua and Barbuda': ['antigua', 'ATG'], 'Bonaire, Saint Eustatius and Saba': ['^bonaire|(?=.*bonaire).*eustatius|^(?=.*carib).*netherlands|\\bbes.?islands', 'BES'], 'Bouvet Island': ['bouvet', 'BVT'], 
    # 'British Antarctic Territories': ['br.*antarctic.?territ.*', 'BA1'], 'British Indian Ocean Territory': ['br.*indian.?ocean', 'IOT'], 'British Virgin Islands': ['^(?=.*\\bu\\.?\\s?k).*virgin|^(?=.*br.*).*virgin|^(?=.*kingdom).*virgin|BVI', 'VGB'], 
    # 'Cayman Islands': ['cayman', 'CYM'], 'Channel Islands': ['channel.?island.*', 'CHI'], 'Cocos (Keeling) Islands': ['\\bcocos|keeling', 'Comoros': ['comoro', 'COM'], 'Cook Islands': ['\\bcook', 'COK'], 'Curacao': ['\\bcura(c|ç)ao', 'CUW'], 
    # 'Falkland Islands': ['falkland|malvinas', 'FLK'], 'Faroe Islands': ['faroe|faeroe', 'FRO', 'f[ä|ae]r[oe|ö][e]?r'], 'French Polynesia': ['french.?polynesia', 'PYF'], 'French Southern Territories': ['french.?southern|\\bfr.*\\bso.*\\ban.*\\b\\bt', 'ATF'], 
    # 'Guam': ['\\bguam', 'GUM'], 'Guernsey': ['guernsey', 'GGY'], 'Heard and McDonald Islands': ['heard.*mc.*donald', 'HMD'], 'Isle of Man': ['^(?=.*isle).*\\bman', 'IMN'], 'Martinique': ['martinique', 'MTQ'], 'Mayotte': ['mayotte', 'MYT'], 
    # 'Micronesia, Fed. Sts.': ['micronesia', 'FSM', 'mikronesien'], 'Montserrat': ['montserrat', 'MSR'], 'Niue': ['niue', 'NIU'], 'Norfolk Island': ['norfolk.*is', 'NFK'], 
    # 'Northern Mariana Islands': ['mariana', 'MNP'],  'Pitcairn': ['pitcairn', 'PCN'], 'Reunion': ['reunion|réunion', 'REU'], 'Saint-Martin': ['^(?!.*maarten)(?!.*saba)(?!.*dutch).*martin\\b', 'MAF'], 
    # 'Samoa': ['^(?!.*amer.*)samoa|(\\bindep.*samoa)|^west.*samoa', 'WSM'], 'Sint Maarten': ['^(?!.*martin)(?!.*saba).*maarten|dutch.*martin|martin.*dutch', 'SXM'], 'South Georgia and South Sandwich Is.': ['south.?georgia|sandwich', 'SGS'], 
    # 'Soviet Union (former)': ['USSR|soviet', 'SUN'], 'St. Barths': ['barth|barts', 'BLM'], 'St. Helena': ['helena', 'SHN'], 'St. Kitts and Nevis': ['kitts|\\bnevis', 'KNA'], 'St. Lucia': ['\\blucia', 'LCA'], 
    # 'St. Pierre and Miquelon': ['miquelon', 'SPM'], 'St. Vincent and the Grenadines': ['vincent', 'VCT'], 'Svalbard and Jan Mayen Islands': ['^(?!norway).*svalbard', 'SJM', 'spitzbergen'], 
    # 'Tanganjika': ['tanganjika|tanganyika', 'EAT'], 'Tokelau': ['tokelau', 'TKL'], 'Tonga': ['tonga', 'TON'], 'Turks and Caicos Islands': ['turks', 'TCA'], 'Tuvalu': ['tuvalu', 'TUV'], 'United States Minor Outlying Islands': ['minor.?outlying.?is', 'UMI'], 
    # 'United States Virgin Islands': ['^(?=.*\\bu\\.?\\s?s).*virgin|^(?=.*states).*virgin', 'VIR'], 'Vatican': ['holy.?see|vatican|papal.?st', 'VAT', 'vatikan'], 'Wallis and Futuna Islands': ['futuna|wallis', 'WLF'], 'San Marino': ['san.?marino', 'SMR','SM'],
    #'Marshall Islands': ['marshall', 'MHL','MH'], 'Western Sahara': ['\\bw.*sahara', 'ESH', 'westsahara'], 'Zanzibar': ['zanz|.*tanzania:?zanzibar', 'EAZ']

    country_codes = {'United States': ['USA','US'], 'China': ['CHN','CN'], 'Brazil': ['BRA','BR'], 
        'Canada': ['CAN','CA'], 'Australia': ['AUS','AU'], 'India': ['IND','IN'], 
        'United Arab Emirates': ['ARE','AE'], 'Argentina': ['ARG','AR'], 'Portugal': ['PRT','PT'], 
        'United Kingdom': ['GBR','GB'], 'Germany': ['DEU','DE'], 'France': ['FRA','FR'], 
        'Afghanistan': ['AFG','AF'], 'Chile': ['CHL','CL'], 'Albania': ['ALB','AL'], 
        'Algeria': ['DZA','DZ'], 'Angola': ['AGO','AO'], 'Armenia': ['ARM','AM'], 
        'Türkiye': ['TUR','TR'], 'Peru': ['PER','PE'], 'Austria': ['AUT','AT'], 
        'Azerbaijan': ['AZE','AZ'], 'Bahamas': ['BHS','BS'], 'Bahrain': ['BHR','BH'], 
        'Bangladesh': ['BGD','BD'], 'Barbados': ['BRB','BB'], 'Belarus': ['BLR','BY'], 
        'Belgium': ['BEL','BE'], 'Belize': ['BLZ','BZ'], 'Benin': ['BEN','BJ'], 
        'Bermuda': ['BMU','BM'], 'Bhutan': ['BTN','BT'], 'Bolivia': ['BOL','BO'], 
        'Sweden': ['SWE','SE'], 'Bosnia and Herzegovina': ['BIH','BA'], 'Botswana': ['BWA','BW'], 
        'Brunei Darussalam': ['BRN','BN'], 'Bulgaria': ['BGR','BG'], 'Burkina Faso': ['BFA','BF'], 
        'Burundi': ['BDI','BI'], 'Cabo Verde': ['CPV','CV'], 'Cambodia': ['KHM','KH'], 
        'Cameroon': ['CMR','CM'],  'Colombia': ['COL','CO'], 'Congo Republic': ['COG','CG'],
        'Costa Rica': ['CRI','CR'], 'Cote dIvoire': ['CIV','CI'], 'Croatia': ['HRV','HR'],
        'Cuba': ['CUB','CU'], 'Cyprus': ['CYP','CY'], 'Guatemala': ['GTM','GT'], 
        'Czechia': ['CZE','CZ'], 'Denmark': ['DNK','DK'], 'Djibouti': ['DJI','DJ'], 
        'Dominica': ['DMA','DM'], 'Dominican Republic': ['DOM','DO'], 'DR Congo': ['COD','CD'], 
        'Ecuador': ['ECU','EC'], 'Egypt': ['EGY','EG'], 'El Salvador': ['SLV','SV'], 
        'Equatorial Guinea': ['GNQ','GQ'], 'Eritrea': ['ERI','ER'], 'Estonia': ['EST','EE'], 
        'Eswatini': ['SWZ','SZ'], 'Ethiopia': ['ETH','ET'], 'Fiji': ['FJI','FJ'], 
        'Finland': ['FIN','FI'], 'French Guiana': ['GUF','GF'], 'Gabon': ['GAB','GA'], 
        'Gambia': ['GMB','GM'], 'Georgia': ['GEO','GE'], 'Ghana': ['GHA','GH'], 
        'Gibraltar': ['GIB','GI'], 'Greece': ['GRC','GR'], 'Greenland': ['GRL','GL'], 
        'Grenada': ['GRD','GD'], 'Guadeloupe': ['GLP','GP'], 'Guinea': ['GIN','GN'], 
        'Guinea-Bissau': ['GNB','GW'], 'Guyana': ['GUY','GY'], 'Haiti': ['HTI','HT'], 
        'New Zealand': ['NZL','NZ'], 'Honduras': ['HND','HN'], 'Hong Kong': ['HKG','HK'], 
        'Hungary': ['HUN','HU'], 'Iceland': ['ISL','IS'], 'Indonesia': ['IDN','ID'], 
        'Iran': ['IRN','IR'], 'Iraq': ['IRQ','IQ'], 'Ireland': ['IRL','IE'], 
        'Saudi Arabia': ['SAU','SA'], 'Israel': ['ISR','IL'], 'Italy': ['ITA','IT'], 
        'Jamaica': ['JAM','JM'], 'Japan': ['JPN','JP'], 'Jersey': ['JEY','JE'], 
        'Jordan': ['JOR','JO'], 'Kazakhstan': ['KAZ','KZ'], 'Kenya': ['KEN','KE'], 
        'Kiribati': ['KIR','KI'], 'Kosovo': ['XKX','XK'], 'Kuwait': ['KWT','KW'], 
        'Kyrgyz Republic': ['KGZ','KG'], 'Laos': ['LAO','LA'], 'Latvia': ['LVA','LV'], 
        'Lebanon': ['LBN','LB'], 'Lesotho': ['LSO','LS'], 'Liberia': ['LBR','LR'], 
        'Libya': ['LBY','LY'], 'Liechtenstein': ['LIE','LI'], 'Lithuania': ['LTU','LT'], 
        'Luxembourg': ['LUX','LU'], 'Macau': ['MAC','MO'], 'North Macedonia': ['MKD','MK'], 
        'Madagascar': ['MDG','MG'], 'Malawi': ['MWI','MW'], 'Malaysia': ['MYS','MY'], 
        'Maldives': ['MDV','MV'], 'Mali': ['MLI','ML'], 'Malta': ['MLT','MT'], 
        'Mauritania': ['MRT','MR'], 'Mauritius': ['MUS','MU'], 'Mexico': ['MEX','MX'], 
        'Moldova': ['MDA','MD'], 'Monaco': ['MCO','MC'], 'Mongolia': ['MNG','MN'], 
        'Montenegro': ['MNE','ME'], 'Morocco': ['MAR','MA'], 'Mozambique': ['MOZ','MZ'], 
        'Myanmar': ['MMR','MM'], 'Namibia': ['NAM','NA'], 'Nauru': ['NRU','NR'], 
        'Nepal': ['NPL','NP'],'Netherlands': ['NLD','NL'], 'Venezuela': ['VEN','VE'],
        'New Caledonia': ['NCL','NC'], 'Nicaragua': ['NIC','NI'], 'Niger': ['NER','NE'], 
        'Nigeria': ['NGA','NG'], 'Spain': ['ESP','ES'], 'North Korea': ['PRK','KP'], 
        'Norway': ['NOR','NO'], 'Oman': ['OMN','OM'], 'Pakistan': ['PAK','PK'], 
        'Palau': ['PLW','PW'], 'Palestine': ['PSE','PS'], 'Panama': ['PAN','PA'], 
        'Papua New Guinea': ['PNG','PG'], 'Paraguay': ['PRY','PY'], 'Philippines': ['PHL','PH'], 
        'Poland': ['POL','PL'], 'Puerto Rico': ['PRI','PR'], 'Qatar': ['QAT','QA'], 
        'Ukraine': ['UKR','UA'], 'Romania': ['ROU','RO'], 'Russia': ['RUS','RU'], 
        'Rwanda': ['RWA','RW'], 'Zimbabwe': ['ZWE','ZW'],'Senegal': ['SEN','SN'], 
        'Seychelles': ['SYC','SC'], 'Sierra Leone': ['SLE','SL'], 
        'Singapore': ['SGP','SG'], 'Slovakia': ['SVK','SK'], 'Slovenia': ['SVN','SI'], 
        'Solomon Islands': ['SLB','SB'], 'Somalia': ['SOM','SO'], 'South Africa': ['ZAF','ZA'], 
        'South Korea': ['KOR','KR'], 'South Sudan': ['SSD','SS'], 'Sri Lanka': ['LKA','LK'], 
        'Sudan': ['SDN','SD'], 'Suriname': ['SUR','SR'], 'Switzerland': ['CHE','CH'], 
        'Syria': ['SYR','SY'], 'Taiwan': ['TWN','TW'], 'Tajikistan': ['TJK','TJ'], 
        'Tanzania': ['TZA','TZ'], 'Thailand': ['THA','TH'], 'Timor-Leste': ['TLS','TL'],
        'Togo': ['TGO','TG'], 'Trinidad and Tobago': ['TTO','TT'], 'Tunisia': ['TUN','TN'], 
        'Turkmenistan': ['TKM','TM'], 'Uganda': ['UGA','UG'], 'Sao Tome and Principe': ['STP','ST'], 
        'Aruba': ['ABW','AW'], 'Uruguay': ['URY','UY'], 'Uzbekistan': ['UZB','UZ'], 
        'Vanuatu': ['VUT','VU'], 'Vietnam': ['VNM','VN'], 'Central African Republic': ['CAF','CF'],
        'Chad': ['TCD','TD'], 'Christmas Island': ['CXR','CX'], 'Yemen': ['YEM','YE'],
        'Zambia': ['ZMB','ZM'],
        'Serbia': ['SRB','XS','RS']
    }

    countries = {'United States': ['^(?!.*islands).*united.?states|^u\\.?s\\.?a\\.?$|^u\\.?s\\.?$','vereinigte staaten','amerika'], 
        'China': ['^(?!repub)(?!taiwan)(?!hong.*kong)(?!macao).*china(?!.*hong.*kong)(?!.*macao)|^PRC$'],
        'Brazil': ['brasilien'], 'Canada': ['kanada'],'Australia': ['australien'], 
        'India': ['^(?!\\D*(?:bassas))\\D*india(?!.*ocea)(?!na)','indien'], 
        'United Arab Emirates': ['emirates|^u\\.?a\\.?e\\.?$|united.?arab.?em','vae', 'vereinigte arab'],
        'Argentina': ['argentinien'], 'Portugal': ['portugal|portuguese'],
        'United Kingdom': ['.*(united.?kingdom|britain|^u\\.?k\\.?$|gb)|england','gro[ss|ß]britannien'], 
        'Germany': ['^(?!e|w)(fed)?.*germany(?!,? *e|,? *w)(,? *)(\\bfed)?','deutschland'], 
        'France': ['^(?!.*\\bdep).*france|french.?republic|\\bgaul','frankreich'],
        'Afghanistan': ['afghan'], 'Chile': ['\\bchile'], 'Spain': ['spanien'], 
        'Albania': ['albanien'], 'Algeria': ['algerien'], 'Angola': ['angola'], 
        'Armenia': ['armenien'], 'Türkiye': ['t[ü|u]rk[i|e]y','Turkey', 't[ü|ue]rkei'], 
        'Peru': ['peru'], 'Austria': ['[oe|ö]sterreich'], 'Azerbaijan': ['aserbaidschan'], 
        'Bahamas': ['bahamas'], 'Bahrain': ['bahrain'], 'Bangladesh': ['bangladesh|^(?=.*east).*paki?stan','bangladesch'], 
        'Barbados': ['barbados'], 'Belarus': ['belarus|byelo','wei[ss|ß]russland'], 
        'Belgium': ['^(?!.*luxem).*belgium','belgien'], 'Belize': ['belize|^(?=.*british).*honduras'], 
        'Benin': ['benin|dahome'], 'Bermuda': ['bermuda'], 'Bhutan': ['bhutan'], 
        'Bolivia': ['bolivien'], 'Sweden': ['swedish|sweden(?!.*except)','schweden'], 
        'Bosnia and Herzegovina': ['herzegovina|bosnia','bosnien|herzegowina'], 'Botswana': ['botswana|bechuana|botsuana'], 'Brunei Darussalam': ['brunei'], 'Bulgaria': ['bulgarien'], 
        'Burkina Faso': ['burkina|\\bfaso|upper.?volta'], 'Burundi': ['burundi'], 
        'Cabo Verde': ['(cabo|cape) *verde','kap verde'], 'Cambodia': ['cambodia|kampuchea|khmer|^p\\.?r\\.?k\\.?$','kambodscha'], 
        'Cameroon': ['cameroon','kamerun'],'Colombia': ['Columbia','kolumbien'], 
        'Congo Republic': ['^(?!.*\\bdem)(?!.*\\bdr)(?!.*kinshasa)(?!.*zaire)(?!.*belg)(?!.*l\\w{1,2}opoldville)(?!.*free)(^rep.*).*\\bcongo.*(?!.*\\bdem)(?!.*\\bdr).*|\\bwest.*congo|^congo[,;\\s]*(?!.*dem)rep.*?$|^congo$|\\bcongo.*brazza.*','Congo Rep\S'], 
        'Costa Rica': ['costa.?rica'], 'Cote dIvoire': ['.*(ivoire|ivory)','elfenbeink[ü|ue]ste'], 
        'Croatia': ['croatia|hrvatska','kroatien'], 'Cuba': ['\\bcuba','kuba'], 
        'Cyprus': ['cyprus','zypern'], 'Guatemala': ['guatemala'], 'Czechia': ['^(?=.*rep).*czech.*|czechia|bohemia|.*czech.*','tschechi'], 
        'Denmark': ['denmark','d[ä|ae]nemark'], 'Djibouti': ['djibouti','dschibuti'], 
        'Dominica': ['dominica(?!n)'], 'Dominican Republic': ['domini[c|k]an'], 
        'DR Congo': ['\\bdem.*congo|congo.*\\bdem|congo.*\\bdr|\\bdr.*congo|\\bd\\.?r\\.?c|\\bd\\.?r\\.?o\\.?c|\\br\\.?d\\.?c|belgian.?congo|congo.?free.?state|kinshasa|zaire|l\\w{1,2}opoldville|^the\\ congo$|^RDC$|^DROC$|\\bcongo.*dem.*','Congo Kinshasa', 'DR Congo', 'DR Kongo', 'kongo dem'], 
        'Ecuador': ['equador'], 'Egypt': ['egypt','[ä|ae]gypten'], 'El Salvador': ['el.?salvador'], 
        'Equatorial Guinea': ['guine.*eq|eq.*guine|^(?=.*span).*guinea','[ae|ä]quatorialguinea'], 
        'Eritrea': ['eritrea'], 'Estonia': ['estonia','estland'], 'Eswatini': ['swaziland'], 
        'Ethiopia': ['ethiopia|abyssinia', 'ETH', '[ä|ae]thiopien'], 'Fiji': ['fidschi'], 
        'Finland': ['finland','finnland'], 'French Guiana': ['^(?=.*french).*gu(i|y)ana|^(?!.*brit)(?!.*dut).*guiana','franz[ösisch]?[.]?[ ]?guyana'], 
        'Gabon': ['gab(o|u)n','gabun'], 'Gambia': ['gambia','the gambia'], 
        'Georgia': ['^(?!.*south).*georgia(?!.*US.*)','georgien'], 'Ghana': ['ghana|gold.?coast'], 
        'Gibraltar': ['gibraltar'], 'Greece': ['greece|hellenic|hellas','griechenland'], 
        'Greenland': ['greenland','gr[ö|oe]nland',], 'Grenada': ['grenada'], 'Guadeloupe': ['guadeloupe'], 
        'Guinea': ['^(?!.*eq)(?!.*span)(?!.*bissau)(?!.*pap)(?!.*new)(?!p.*n.*).*guinea'], 
        'Guinea-Bissau': ['^(.*portu).*gu(i|y)nea|gu(y|i)nea.*bissau'], 
        'Guyana': ['^(?!.*fren)(?!.*dut).*\\bguyana|^(.*brit).*gu(i|y)ana'], 
        'Haiti': ['(ha(i|\\xef|\\xc3\\xaf)ti)'], 'New Zealand': ['(new|n).*zealand','neuseeland'], 
        'Honduras': ['^(?!.*brit).*honduras'], 'Hong Kong': ['.*hong.*kong|hksar'], 
        'Hungary': ['hungary','ungarn'], 'Iceland': ['iceland','island'], 
        'Indonesia': ['indonesia','indonesien'], 'Iran': ['\\biran|persia'], 
        'Iraq': ['\\biraq|mesopotamia', 'irak'], 'Ireland': ['^(?!.*north.*).*ireland','irland'], 
        'Saudi Arabia': ['\\bsa\\w*.?arabia', 'saudi-arabien'], 'Israel': ['israel'], 
        'Italy': ['.*italy|.*italia.*','italien'], 'Jamaica': ['jamaica','jamaika'], 
        'Japan': ['japan'], 'Jersey': ['^(?!.*new).*jersey'], 'Jordan': ['jordan[ien]?'], 
        'Kazakhstan': ['kazak','kazahkstan','kasachstan'], 'Kenya': ['kenya|british.?east.?africa|east.?africa.?prot','kenia'], 
        'Kiribati': ['kiribati'], 'Kosovo': ['kosovo'], 'Kuwait': ['kuwait'], 
        'Kyrgyz Republic': ['kyrgyz|kirghiz'], 'Laos': ['\\blaos?\\b'], 'Latvia': ['latvia','lettland'], 
        'Lebanon': ['lebanon|lebanese','libanon'], 'Lesotho': ['lesotho|basuto'], 'Liberia': ['liberia'], 
        'Libya': ['libya','libyen'], 'Liechtenstein': ['liechtenstein'], 'Lithuania': ['lithuania','litauen'], 
        'Luxembourg': ['^(?!.*belg).*luxem', 'luxemburg'], 'Macau': ['.*maca(o|u)'], 
        'North Macedonia': ['macedonia|^f\\.?y\\.?r\\.?o\\.?m\\.?$','(nord)?[ -]?mazedonien'], 
        'Madagascar': ['madagascar|malagasy','madagaskar'], 'Malawi': ['malawi|nyasa'], 
        'Malaysia': ['malaysia'], 'Maldives': ['maldive','malediwen'], 'Mali': ['\\bmali\\b'], 
        'Malta': ['\\bmalta'], 'Mauritania': ['mauritania','mauretanien'], 'Mauritius': ['mauritius'], 
        'Mexico': ['^(?!.*new).*mexi(?!.*city)','mexiko'], 'Moldova': ['moldov|b(a|e)ssarabia','moldau', 'moldawien'], 
        'Monaco': ['monaco'], 'Mongolia': ['mongolia','mongolei'], 'Montenegro': ['^(?!.*serbia).*montenegro'], 
        'Morocco': ['morocco|\\bmaroc','marokko'], 'Mozambique': ['mozambique','mosambik'], 
        'Myanmar': ['myanmar|burma'], 'Namibia': ['nambia'], 'Nauru': ['nauru'], 'Nepal': ['nepal'], 
        'Netherlands Antilles': ['^(?=.*\\bant).*(neth.*|dutch)', 'ANT'], 'Netherlands': ['^(?!.*\\bant)(?!.*\\bcarib).*netherlands','(die )?niederlande'], 
        'Venezuela': ['venezuela'], 'New Caledonia': ['new.?caledonia'], 'Nicaragua': ['nicaragua'], 
        'Niger': ['\\bniger(?!ia)'], 'Nigeria': ['nigeria'], 
        'North Korea': ['^(?=.*dem).*\\bkorea|^(?=.*peo).*\\bkorea|^(?=.*nor).*\\bkorea|\\bd\\.?p\\.?r\\.|.*dpr.*|^n.*korea','Korea North','nordkorea'], 
        'Norway': ['norway','norwegen'], 'Oman': ['\\boman|trucial'], 'Pakistan': ['^(?!.*east).*paki?stan'], 
        'Palau': ['palau'], 'Palestine': ['palestin|\\bgaza|west.?bank'], 'Panama': ['panama'], 
        'Papua New Guinea': ['\\bp.*\\bn.*\\bguin.*|^p\\.?n\\.?g\\.?$|new.?guinea','papua-neuguinea'], 
        'Paraguay': ['paraguay'], 'Philippines': ['philippines','philippinen'], 
        'Poland': ['poland','polen'], 'Puerto Rico': ['puerto.?rico'], 'Qatar': ['qatar', 'katar'], 
        'Ukraine': ['ukrain'], 'Romania': ['r(o|u|ou)mania', 'rum[ä|ae]nien'], 'Russia': ['\\brussia', 'russland'], 
        'Rwanda': ['rwanda','ruanda'], 'Zimbabwe': ['zimbabwe|^(?!.*northern).*rhodesia','simbabwe'],
        'Senegal': ['senegal'], 'Serbia': ['^(?!.*monte).*serbia.*', 'serbien'], 'Seychelles': ['seychell'], 
        'Sierra Leone': ['sierra'], 'Singapore': ['singapore','singapur'], 'Slovakia': ['^(?!.*cze).*slovak','slowakei'], 
        'Slovenia': ['slovenia','slovenien'], 'Solomon Islands': ['solomon'], 'Somalia': ['somali'], 
        'South Africa': ['\\bs(\\.|outh)(?!.*sahar).*africa|^r\\.?s\\.?a\\.?$','s[ü|ue]dafrika'], 
        'South Korea': ['^(?!.*dem)(?!.*peo)(?!.*nor)(?!.*n)(?!.*dpr)(?!d\\.p\\.r).*\\bkorea|\\br\\.?o\\.?k\\b', 'Korea Republic','s(ü|ue)dkorea'], 
        'South Sudan': ['\\bs\\w*.?sudan',], 'Sri Lanka': ['sri.?lanka|ceylon'], 'Sudan': ['^(?!.*\\bs(?!u)).*sudan'], 
        'Suriname': ['surinam|dutch.?gu(i|y)ana'], 'Switzerland': ['switz|swiss','schweiz'], 'Syria': ['syrien'], 
        'Taiwan': ['.*taiwan|.*taipei|.*formosa|^(?!.*\\bdem)(?!.*\\bpe)(?!.*\\bdr)(^rep.*).*\\bchina.*(?!.*\\bdem.*)(?!\\bpe.*)(?!.*\\bdr.*).*|^ROC$|^taiwan r\\.?o\\.?c\\.?$'],
        'Tajikistan': ['tajik','tadschikistan'], 'Tanzania': ['tanzania(?!: zan.*)','tansania'],
        'Thailand': ['thailand|\\bsiam'], 'Timor-Leste': ['^(?=.*leste).*timor|^(?=.*east).*timor','osttimor'],
        'Togo': ['togo'], 'Trinidad and Tobago': ['trinidad|tobago'], 'Tunisia': ['tunisia','tunesien'],
        'Turkmenistan': ['turk-?men'], 'Uganda': ['uganda'], 'Sao Tome and Principe': ['(S|s)ao (T|t)ome'],
        'Aruba': ['^(?!.*bonaire).*\\baruba'], 'Uruguay': ['uruguay','Ururguay'], 'Uzbekistan': ['uzbek','usbekistan'],
        'Vanuatu': ['vanuatu|new.?hebrides'], 'Vietnam': ['^((?!n|s|.*republic)|(?=.*socialist)).*viet.?nam(?! *,? *n| *,? *s)'],
        'Central African Republic': ['central.?african.?rep.*','zentralafrikanische'], 'Chad': ['\\bchad','tschad'],
        'Christmas Island': ['christmas'], 'Yemen': ['yemen','jemen'], 'Zambia': ['zambia|northern.?rhodesia','sambia'],
        'Others': ['oth','Other countries']
    }

    if type(ser) != pd.Series:
        print('Country conversion takes in a pd Series! No conversion took place.')
        return ser,problemcountries
    
    # Replace strange characters and drop everything after an "and" etc. Some entries 
    # are "USA and Canada", which this would then count as completely USA. Don't know 
    # if there's a better way to handle that. 
    ser = ser.str.replace(" "," ")
    ser = ser.str.replace("ã","a")
    ser = ser.str.replace("é","e")
    ser = ser.str.replace("ô","o")
    ser = ser.str.replace("saint","st.")
    ser = ser.str.replace('[^ A-zü]','',regex=True)
    ser = ser.str.replace(' +',' ',regex=True)
    ser = ser.str.strip()

    ser = ser.str.split(" and ").str[0]
    ser = ser.str.split(" und ").str[0]
    ser = ser.str.split(" &").str[0]
    ser = ser.str.split(" inkl").str[0]

    # Do the computationally expensive dictionary check once for the unique names. 
    uniquenames = pd.DataFrame(ser.unique()).reset_index(drop=True)     
    
    # Depending on what data was put in, there is a loop that checks for equality 
    # of country codes and associates them with the standard country in "new_codes" ...
    new_codes = pd.DataFrame([pd.NA]*uniquenames.shape[0])
    if ccodes: 
        for i in range(uniquenames.shape[0]):
            name = uniquenames.iloc[i,0]
            if pd.isna(name):
                continue
            found = 0       # found to stop the dictionary check after we found a match
            for standard, alternatives in country_codes.items():  
                for alternative in alternatives: 
                    if name.upper() == alternative:
                        new_codes.iloc[i,0] = standard
                        found = 1
                        break
                if found == 1:
                    break
            if found == 0:  # equivalent to putting "else" 
                if name in problemcountries:        # If the code couldn't be matched, the 
                    problemcountries[name] += 1     # country name stays as a NaN
                else:
                    problemcountries[name] = 1
    
    # ... or there is a loop that checks for regex matches for country names and
    # associates them with the standard country in "new_names". The loops are 
    # similar (lots of copy-paste) but not abstract enough to be a function. 
    new_names = pd.DataFrame([pd.NA]*uniquenames.shape[0])
    if cnames:
        for i in range(uniquenames.shape[0]):
            name = uniquenames.iloc[i,0]
            found = 0
            for standard, alternatives in countries.items():    # Check for standard match
                if name.startswith(standard):
                    new_names.iloc[i,0] = standard
                    found = 1
                else:                                           # or else, check for alternative regex match (inspired by coco)
                    for alternative in alternatives: 
                        if re.match(alternative,name,re.IGNORECASE):
                            new_names.iloc[i,0] = standard
                            found = 1
                            break
                if found == 1:
                    break
            if found == 0:
                if name in problemcountries:    # Country name stays NaN
                    problemcountries[name] += 1
                else:
                    problemcountries[name] = 1

    # Now, where new_names is NaN still is overwritten by new_codes, and if that's
    # still a NaN it is overwritten with the original name. Then this resulting 
    # new_names df (it has to be a dataframe because the Series version of replace
    # does not have an overwrite argument) gets used to replace and return the result. 
    new_names.update(new_codes,overwrite=False)
    new_names.update(uniquenames,overwrite=False)
    for i in range(len(new_names)):                
        ser.replace(to_replace=uniquenames.iloc[i,0],value=new_names.iloc[i,0],inplace=True)
    
    return ser,problemcountries

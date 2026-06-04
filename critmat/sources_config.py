from critmat.database.models import *

SOURCE_REGISTRY = {
    'usgs': {
        'folder': 'input_data/usgs/',
        'file_pattern': '^myb.*\.xlsx$',
        'get_fn': ('get_usgs_myb', 'critmat.data_processing'),
        'target_model': FactMaterialProduction,
        'source_name': 'USGS_myb',
        'cut_subtotal': True,          # optional flag
        'cut_outdated': True,       # optional flag
        'db_out': True,              # optional flag
        'prepare_fn': None,
    },
    'wmd': {
        'folder': 'input_data/wmd/',
        'file_pattern': '^(WMD|6.4).*\.xlsx$',
        'get_fn': ('get_wmd', 'critmat.data_processing'),
        'target_model': FactMaterialProduction,
        'source_name': 'WMD',
        'publish_year': 2025,
        'prepare_fn': None,
    },
    'bgs': {
        'folder': 'input_data/bgs/',
        'file_pattern': '.*\.csv$',
        'get_fn': ('get_bgs2025', 'critmat.data_processing'),
        'target_model': FactMaterialProduction,
        'source_name': 'BGS',
        'publish_year': 2025,
        'db_out': True,
        'prepare_fn': None,
    },
    'eustat': {
        'folder': 'input_data/eustat/',
        'file_pattern': '^tariff.*\.dat$',
        'get_fn': ('get_eurostat_trade2025', 'critmat.data_processing'),
        'target_model': FactMaterialTradeFlow,
        'source_name': 'EUST',
        'publish_year': 2025,
        'code_file': 'input_data/tradecodes/tradecodetable_array.xlsx',
        'prepare_fn': None,
    },
    'wgi': {
        'folder': 'input_data/wgi/',
        'file_pattern': '^wgidataset_with_sourcedata.*\.xlsx$',
        'get_fn': ('get_wgi', 'critmat.data_processing'),
        'target_model': FactCountryWGI,
        'source_name': 'WB',
        'publish_year': 2025,
        'prepare_fn': None,
    },
    # 'eureport_results': {
    #     'folder': 'input_data/eureport/',
    #     'get_fn': ('get_eureport', 'critmat.data_processing'),
    #     'target_model': FactEUReport,
    #     'source_name': 'EUREPORT',
    #     'publish_year': 2025,
    #     'table': 'results',
    #     'prepare_fn': None,
    # },
    # 'eureport_tradeparameters': {
    #     'folder': 'input_data/eureport/',
    #     'get_fn': ('get_eureport', 'critmat.data_processing'),
    #     'target_model': FactTradeParameter,
    #     'source_name': 'EUREPORT',
    #     'publish_year': 2025,
    #     'table': 'tradeparameters',
    #     'prepare_fn': None,
    # },
}
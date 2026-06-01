# Critical Material Assessment Toolkit (CritMAT)

A Python package for processing and analyzing Critical Raw Material (CRM) data. CritMAT extracts, standardizes, and analyzes raw materials data from multiple sources to support supply chain risk assessment and market concentration analysis.

**Status:** Active development - core data processing and ingestion functions implemented.

## Features

### Data Sources
- **Mineral Yearbook (MYB)** - United States Geological Survey (USGS)
- **World Mining Data (WMD)** - Austrian Federal Ministry of Finance (BMF) 
- **World mineral statistics data** - British Geological Survey (BGS)
- **Comext Inernational trade** - Eurostat European Commission
- **World Governance Indicators (WGI)** -  World Bank Group
- **EU Report 2023** - European Commission

### Analysis Functions (Work in progress)
- **HHI Calculation** - Herfindahl-Hirschman Index for market concentration
- **WGI-Weighted HHI** - HHI adjusted for governance risk (penalizes supply from countries with poor governance)
- **Trade Parameter HHI** - HHI with EU-specific trade dependency factors

### Data Standardization
- Automatic country name standardization across sources
- Material name standardization with category support (primary/refined)
- Unit conversion to standard formats (tons, m3, carats)
- CN8 trade code mapping for Eurostat data

### Database
- SQLite with SQLAlchemy ORM
- Dimension tables: Source, Country, Material
- Fact tables: MaterialProduction, MaterialTradeFlow, CountryWGI, EUReport, TradeParameter
- Triggers for data quality (auto-delete outdated records, prevent zero-quantity entries)
- Views for supply risk calculation combining production, trade, governance, and assessment data

## Supported Data Sources

| Source | Type | Target Model |
|--------|------|--------------|
| USGS Mineral Yearbook | Production | FactMaterialProduction |
| WMD | Production | FactMaterialProduction |
| BGS 2025 | Production | FactMaterialProduction |
| Eurostat Trade 2025 | Trade Flows | FactMaterialTradeFlow |
| WGI | Governance | FactCountryWGI |
| EU Report 2023 | Assessment | FactEUReport, FactTradeParameter |

## Installation

```bash
pip install -e .
python -m critmat.database.populate_database
```

The first command installs the package and dependencies. The second command initializes the SQLite database with the schema and seeds it with reference data (countries, materials, sources).

**Requirements:**
- Python >= 3.9
- pandas >= 2.0
- sqlalchemy >= 2.0
- openpyxl >= 3.0
- regex

**Environment Variables:**
- `DATABASE_URL` - Database connection string (default: `sqlite:///database/crm.db`)

## Usage

### 1. Prepare Data Files

Place your source data files in the appropriate `input_data/` subdirectories:

```
input_data/
├── usgs/                    # USGS Excel files (organized by material/year)
├── wmd/                     # WMD2025 Commodities 1984-2023.xlsx
├── bgs/                     # BGS CSV files
├── eustat/                  # Eurostat trade data files
├── wgi/                     # wgidataset_with_sourcedata-2025.xlsx
└── tradecodes/              # tradecodetable_array.xlsx
```

### 2. Export Results to CSV

```bash
python -m critmat.convert_input_files 
```
Process specific sources:

```bash
python -m critmat.convert_input_files --sources usgs wmd bgs
```

List registered sources:

```bash
python -m critmat.convert_input_files --list
```
### 3. Upload Data to Database

Process and load data from all sources:

```bash
python -m critmat.upload_input_files
```

Process specific sources:

```bash
python -m critmat.upload_input_files --sources usgs wmd bgs
```

List registered sources:

```bash
python -m critmat.upload_input_files --list
```

### 4. Run Calculations (requires Database upload)

```bash
python -m critmat.calculations.calc_hhi

```

## Project Structure

```
CritMAT/
├── critmat/                # Main package
│   ├── calculations/       # HHI calculation functions
│   │   ├── calc_hhi.py
│   │   ├── calc_hhi_wgi.py
│   │   └── calc_hhi_wgi_tp.py
│   ├── data_processing/    # Data extraction modules
│   │   ├── get_usgs_myb.py
│   │   ├── get_usgs_mcs.py
│   │   ├── get_wmd.py / get_wmd_full.py
│   │   ├── get_bgs2025.py
│   │   ├── get_eurostat_trade2025.py
│   │   ├── get_wgi.py
│   │   └── translation.py
│   ├── database/           # Database layer
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── config.py       # Database configuration
│   │   ├── populate_database.py
│   │   └── upload_dataframe.py
│   ├── convert_input_files.py   # Extract data to csv
│   ├── sources_config.py   # Source registry
│   └── upload_input_files.py  # Data ingestion script
├── input_data/             # Source data files and seeds
├── output_data/            # Processed output
└── pyproject.toml          # Package configuration
```

## Architecture

### Database Schema

**Dimension Tables:**
- `source` - Data source definitions
- `country` - Country names with EU membership and coordinates
- `material` - Material names with type and EU usage stage

**Fact Tables:**
- `fact_materialproduction` - Production by material/country/year
- `fact_materialtradeflow` - Trade flows with importer/exporter, quantity, value, CN8 codes
- `fact_countrywgi` - Governance indicators (6 dimensions)
- `fact_eureport` - EU assessment data (supply risk, economic importance, import reliance, etc.)
- `fact_tradeparameter` - Country-specific trade parameters from EU report
- `fact_materialproduction_eusource` - EU source mappings

### Source Registry

The `sources_config.py` file defines the `SOURCE_REGISTRY` which maps each data source to its processing function, target model, and source-specific parameters (folder paths, publish years, options).


## Development Status

- Core database schema and models implemented
- Data ingestion pipelines for major data sources working
- Trade code mapping for Eurostat data implemented
- Country and material name standardization implemented

**In progress:**

- Rework tradecodes handeling 
- EU Supply risk calculation translation (From SQL to python)

**Future:**

- Rework production categories (primary/refined)
- Rework primary keys of base tables to be readable (like ISO3 codes for countries)
- Implement non-EU trade sources
- Other Assessment Methods


## Funding

**Main funding:** Lower Saxony Ministry of Science and Culture (Germany) for the research project "Zukunftslabor Circular Economy".
**Former funding:** This project has received funding from the European Union's Horizon Europe research and innovation programme under Grant Agreement No. 101091490.

## Author

Ole Meyer (OFFIS e.V.), Alexandra Pehlken (DfKI)

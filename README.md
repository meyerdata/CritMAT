# Critical Material Assessment Toolkit (CritMAT)

A Python package for processing and analyzing Critical Raw Materials (CRM) production and trade data. CritMAT extracts, standardizes, and analyzes raw materials data from multiple sources to support supply chain risk assessment and market concentration analysis.

**Status:** Active development - core data ingestion and analysis functions implemented.

## Features

### Data Sources
- **USGS Mineral Yearbook (myb)** - Excel-based annual production data by material and country
- **WMD** - World Mineral Development data (Excel)
- **BGS 2025** - British Geological Survey production data (CSV)
- **Eurostat Trade 2025** - EU trade flow data from Eurostat COMEXT with CN8 product codes
- **WGI** - World Governance Indicators for 6 governance dimensions
- **EU Report 2023** - Fifth CRM Assessment extractable parameters (supply risk, economic importance, substitutability, import reliance, end-of-life recycling)

### Analysis Functions
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
- tabula-py >= 1.0 (for PDF extraction)

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
├── eureport/                # 2023 Fifth CRM Assessment.pdf
└── tradecodes/              # tradecodetable_array.xlsx
```

### 2. Export Results

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
│   │   ├── calc_hhi_wgi_tp.py
│   │   └── eu_supply_risk.py
│   ├── data_processing/    # Data extraction modules
│   │   ├── get_usgs_myb.py
│   │   ├── get_usgs_mcs.py
│   │   ├── get_wmd.py / get_wmd_full.py
│   │   ├── get_bgs2025.py
│   │   ├── get_eurostat_trade2025.py
│   │   ├── get_wgi.py
│   │   ├── get_eureport.py
│   │   └── translation.py
│   ├── database/           # Database layer
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── config.py       # Database configuration
│   │   ├── populate_database.py
│   │   └── upload_dataframe.py
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
- `material` - Material names with category and EU usage stage

**Fact Tables:**
- `fact_materialproduction` - Production by material/country/year
- `fact_materialtradeflow` - Trade flows with importer/exporter, quantity, value, CN8 codes
- `fact_countrywgi` - Governance indicators (6 dimensions)
- `fact_eureport` - EU assessment data (supply risk, economic importance, import reliance)
- `fact_tradeparameter` - Country-specific trade parameters
- `fact_materialproduction_eusource` - EU source mappings

### Source Registry

The `sources_config.py` file defines the `SOURCE_REGISTRY` which maps each data source to its processing function, target model, and source-specific parameters (folder paths, publish years, options).

### Data Flow

```
Raw Data Files → Data Processing Modules → Standardized DataFrames → Database
                                                                         ↓
                                    Analysis Functions ← Query Results ← Database Views
```

## Development Status

- Core database schema and models implemented
- Data ingestion pipelines for 6 data sources working
- HHI calculation functions implemented (standard, WGI-weighted, trade-parameter weighted)
- EU supply risk calculation implemented
- Trade code mapping for Eurostat data implemented
- Country and material name standardization implemented

**In progress:**
- Additional data validation and error handling
- Documentation improvements

## Funding

This project has received funding from the European Union's Horizon Europe research and innovation programme under Grant Agreement No. 101091490.

## Author

Ole Meyer (OFFIS e.V.)
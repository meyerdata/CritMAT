# Critical Material Assessment Toolkit (CritMAT)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20489684.svg)](https://doi.org/10.5281/zenodo.20489683)

A Python package for processing and analyzing Critical Raw Material (CRM) data. CritMAT extracts, standardizes, and analyzes raw materials data from multiple sources to support supply chain risk assessment and market concentration analysis.

## Features
### Compatible Data Sources
- United States Geological Survey (USGS): [Mineral Yearbook (MYB)](https://www.usgs.gov/centers/national-minerals-information-center/minerals-yearbook-metals-and-minerals)
- United States Geological Survey (USGS): [Mineral Commodity Summaries (MCS)](https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries)
- Austrian Federal Ministry of Finance (BMF): [World Mining Data (WMD)](https://www.world-mining-data.info/?World_Mining_Data___Mineral_Raw_Materials)
- British Geological Survey (BGS): [World mineral statistics data](https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-archive/)
- European Commission: [Comext database](https://ec.europa.eu/eurostat/web/international-trade-in-goods/database)
- World Bank Group: [World Governance Indicators (WGI)](https://www.worldbank.org/en/publication/worldwide-governance-indicators)

### Analysis Functions
- **HHI Calculation** - Herfindahl-Hirschman Index for market concentration
- **WGI-Weighted HHI** - HHI adjusted for governance risk (penalizes supply from countries with poor governance)
- **Trade Parameter HHI** - HHI with EU-specific trade dependency factors
- **Supply Risk EU 2023** - Calculate the supply risk based on the 2023 EU report

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
- Views for supply risk calculation creating EU supply and tradeparameter data

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

## Basic Usage
### 1. Prepare Data Files
Place your source data files in the appropriate `input_data/` subdirectories:
```
input_data/
├── usgs/                    # USGS Excel files (organized in material subfolders)
├── wmd/                     # WMD Excel files
├── bgs/                     # BGS API CSV files
├── eustat/                  # Eurostat trade dat files
├── wgi/                     # WGI excel files
└── tradecodes/              # Tradecode excel files
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
### 4. Run Calculations Examples (requires Database upload)
Calculate the HHI for all uploaded material production data:
```bash
python -m critmat.calculations.calc_hhi
```
Calculate the WGI-weighted HHI for all uploaded material supply data:
```bash
python -m critmat.calculations.calc_hhi --wgi --eu_trade
```
Calculate the supply risk according to the EU in the timeframe [2023,2024]:
```bash
python -m critmat.calculations.calc_assessment --eu --timeframe 2023 2024
```

## Calculate EU Supply Risk Example
Calculate the supply risk based on the 2023 EU report for the timeframe 2020-2024:
- Download `6.4.Production of Mineral Raw Materials...` from [World Mining Data](https://www.world-mining-data.info/?World_Mining_Data___Data_Section) → copy to `input_data/wmd/`
- Download `Governance Estimates and Absolute Scores...` from [World Bank](https://www.worldbank.org/en/publication/worldwide-governance-indicators) → copy to `input_data/wgi/`
- Download the files `tariff_202052.7z`,`tariff_202152.7z`,`tariff_202252.7z`,`tariff_202352.7z`, and `tariff_202452.7z` from [Eurostat Bulk download](https://ec.europa.eu/eurostat/databrowser/bulk?lang=en&selectedTab=fileComext&breadcrumbFilter=COMEXT_DATA%2FPREFERENCES) → extract the dat-files and copy them to `input_data/eustat/`
- _(Optional)_ Download desired `Minerals Yearbook` xlsx-files from [USGS Commodity Statistics](https://www.usgs.gov/centers/national-minerals-information-center/commodity-statistics-and-information) → copy to `input_data/usgs/MATERIAL_NAME/`
- _(Optional)_ Download `World Mineral Statistics` as csv-files from [BGS](https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/) → copy to `input_data/bgs/`
- Run
```bash
python -m critmat.upload_input_files
python -m critmat.calculations.calc_assessment --eu --timeframe 2020 2021 2022 2023 2024
```

## Project Structure
```
CritMAT/
├── critmat/                # Main package
│   ├── calculations/       # HHI and assessment calculation functions
│   │   ├── calc_hhi.py
│   │   ├── hhi_basic.py
│   │   ├── hhi_wgi.py
│   │   ├── hhi_wgi_tp.py
│   │   ├── calc_assessment.py
│   │   └── supply_risk_eu.py
│   ├── data_processing/    # Data extraction modules
│   │   ├── get_usgs_myb.py
│   │   ├── get_usgs_myb_helpers.py
│   │   ├── get_wmd.py
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
- EU Supply risk calculation implemented
  
**In progress:**
- Rework tradecode handeling
  
**Future:**
- Rework production categories (primary/refined)
- Implement non-EU trade sources
- Other Assessment Methods

## Funding
**Main funding:** This project receives funding from the Future Lab Circular Economy at the Center for Digital Innovations Lower Saxony (ZDIN). It is promoted by zukunft.niedersachsen, the joint funding program of the Lower Saxony Ministry of Science and Culture and the Volkswagen Foundation.

**Former funding:** This project has received funding from the European Union's Horizon Europe research and innovation programme in the CIRC-UITS project under Grant Agreement No. 101091490.

## Authors

**Ole Meyer** (OFFIS e.V.) ole.meyer@offis.de
  [![ORCID](https://img.shields.io/badge/ORCID-0000--0002--9964--5591-green)](https://orcid.org/0000-0002-9964-5591)  
 
**Alexandra Pehlken** (DfKI) alexandra.pehlken@dfki.de
  [![ORCID](https://img.shields.io/badge/ORCID-0000--0003--1798--8679-green)](https://orcid.org/0000-0003-1798-8679)  

## References
No data of the "Compatible Data Sources" is shared within this repository. This software references:
- **European Commission**: [Study on the Critical Raw Materials for the EU 2023: Final Report](https://doi.org/10.2873/725585)
- **European Commission**: [Methodology for Establishing the EU List of Critical Raw Materials: Guidelines](https://doi.org/10.2873/769526)
- **SCRREEN Project**: [Raw Material Factsheets](https://scrreen.eu/crms-2023/)
- **Raw Materials Information System (RMIS)**: [Data Source Documentation](https://rmis.jrc.ec.europa.eu/uploads/rmp/info-dashboard.pdf)

_If you use CritMAT in your research, please cite both the software (see DOI badge above) and the respective data sources you utilized._

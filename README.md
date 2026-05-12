# Critical Material Assessment Toolkit (CritMAT)

A Python package for processing and analyzing Critical Raw Materials (CRM) production data.

CritMAT extracts, standardizes, and analyzes raw materials data from various sources to support supply chain risk assessment and market concentration analysis.

## Features

- Data extraction from various source formats
- Calculate Herfindahl-Hirschman Index for market concentration
- Standardize material names, country names, and units
- Unit conversion to standard formats (tons, m3, carats)
- Extensible architecture for multiple data source types

## Current Implementation

CritMAT currently supports processing of USGS Mineral Yearbooks (Excel format).

## Installation

```bash
pip install -e .
```

**Requirements:**
- Python >=3.9
- pandas>=2.0.0,<3.0.0
- numpy>=1.24.0
- regex
- openpyxl

## Usage

1. Place your data files (e.g., USGS Excel files) into the `data_files/` folder
2. Run a processing script or import the package directly:

```python
from crm_db_meyer import get_usgs, calc_hhi

data = get_usgs("data_files/usgs/", 'USGS', db_out=True, cut_outdated=True, cut_subtotal=True)
hhi = calc_hhi(data)
```

The processed output can be saved to `csv_output/` for further analysis.

## Planned Features

- Additional source formats (WMD, BGS, Eurostat and more)
- Advanced Assessment functions
- Other output formats

## Project Structure

```
.
├── src/crm_db_meyer/       # Main package
│   ├── __init__.py
│   ├── calc_hhi.py         # HHI calculation
│   ├── get_usgs.py         # USGS data extraction
│   ├── get_usgs_helpers.py # Helper functions
│   └── translation.py      # Standardization utilities
├── tests/                  # Usage examples
├── data_files/             # Input data (gitignored)
├── csv_output/             # Processed output (gitignored)
└── README.md
```

## Funding

This project has received funding from the European Union’s Horizon Europe research and innovation programme under Grant Agreement No. 101091490.

## Author

Ole Meyer (OFFIS e.V.)
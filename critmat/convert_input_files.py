#!/usr/bin/env python3
"""
Data conversion script for Critical Raw Materials Database.

Loads data from raw files in input_data/ and saves to CSV.

Usage:
    python convert_input_files.py                    # All sources
    python convert_input_files.py --sources usgs     # Specific source
    python convert_input_files.py --sources usgs wb  # Multiple sources
    python convert_input_files.py --list             # Show registered sources
    python convert_input_files.py --output-dir output_data # Custom output directory
"""

import argparse
from email import parser
import importlib
import os
import regex as re
import pandas as pd
from critmat.sources_config import SOURCE_REGISTRY


def convert_source(source_key, output_dir='output_data'):
    config = SOURCE_REGISTRY[source_key]

    if not os.path.exists(config['folder']):
        print(f"Skipping '{source_key}': folder '{config['folder']}' not found")
        return

    print(f"\n{'='*60}")
    print(f"Processing source: {source_key}")
    print(f"{'='*60}")

    module = importlib.import_module(config['get_fn'][1])
    get_fn = getattr(module, config['get_fn'][0])
    extra_kwargs = {
        k: v for k, v in config.items()
        if k not in {'folder','file_pattern', 'get_fn', 'target_model', 'source_name', 'prepare_fn'}
    }

    ##THIS IS FOR A MORE DETAILED MANUAL OUTPUT
    if 'db_out' in extra_kwargs:
        del extra_kwargs['db_out']

    os.makedirs(output_dir, exist_ok=True)

    full_df = pd.DataFrame()
    full_log = pd.DataFrame()
    for path, subdirs, files in os.walk(config['folder']):
        for name in files:
            if re.search(config['file_pattern'], name) and not name.startswith('~$'):
                file = os.path.join(path, name)
                print(name)

                df, log = get_fn(file,
                            source=config['source_name'],
                            **extra_kwargs)

                if config['prepare_fn']:
                    prepare_module = importlib.import_module(config['get_fn'][1])
                    prepare_fn = getattr(prepare_module, config['prepare_fn'])
                    df = prepare_fn(df)

                full_df = pd.concat([full_df, df])
                full_log = pd.concat([full_log, log])

    if full_df.empty:
        print(f"No valid data found for source '{source_key}'")
        return
    output_path = os.path.join(output_dir, f"{config['source_name']}.csv")
    full_df.to_csv(output_path, index=False)
    full_log.to_csv(os.path.join(output_dir, f"{config['source_name']}_log.csv"), index=False)
    print(f"Saved {source_key} to {output_path}")


def convert_all(output_dir):
    for source_key in SOURCE_REGISTRY:
        convert_source(source_key, output_dir)


def main():
    parser = argparse.ArgumentParser(description='Convert input files to CSV')
    parser.add_argument('--sources', nargs='+', help='Source(s) to convert (default: all)')
    parser.add_argument('--list', action='store_true', help='List registered sources and exit')
    parser.add_argument('--output-dir', default='output_data', help='Output directory for CSV files')
    
    args = parser.parse_args()

    if args.list:
        print("Registered sources:")
        for key in SOURCE_REGISTRY:
            print(f"  - {key}")
        return

    if args.sources:
        for source in args.sources:
            if source in SOURCE_REGISTRY:
                convert_source(source, args.output_dir)
            else:
                print(f"Unknown source: '{source}' - skipping")
    else:
        convert_all(args.output_dir)

    print(f"\n{'='*60}")
    print("All sources converted")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
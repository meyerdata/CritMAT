#!/usr/bin/env python3
"""
Data ingestion script for Critical Raw Materials Database.

Loads data from raw files in input_data/ into the database.

Usage:
    python upload_input_files.py                    # All sources
    python upload_input_files.py --sources usgs     # Specific source
    python upload_input_files.py --sources usgs wb  # Multiple sources
    python upload_input_files.py --list             # Show registered sources
"""

import argparse
import importlib
import os
import regex as re

from sqlalchemy import create_engine

from critmat.database.config import DATABASE_URL
from critmat.database.upload_dataframe import upload_dataframe
from critmat.sources_config import SOURCE_REGISTRY


def upload_source(source_key, connection):
    config = SOURCE_REGISTRY.get(source_key)
    if config is None:
        raise KeyError(f"Source '{source_key}' not found in any registry")
    
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
        if k not in {'folder', 'file_pattern', 'get_fn', 'target_model', 'source_name', 'prepare_fn'}
    }
    
    found_files = []
    for path, subdirs, files in os.walk(config['folder']):
        for name in files:
            if re.search(config['file_pattern'], name) and not name.startswith(r'~$'):
                found_files.append(os.path.join(path, name))

    if found_files == []:
        print(f"No files found for {source_key}")
        return
    
    for file in found_files:
        df, log = get_fn(file,
                    source=config['source_name'],
                    **extra_kwargs)

        if config['prepare_fn']:
            prepare_module = importlib.import_module(config['get_fn'][1])
            prepare_fn = getattr(prepare_module, config['prepare_fn'])
            df = prepare_fn(df)

        upload_dataframe(df, config['target_model'].__table__, connection)

    print(f"Completed {source_key}")


def upload_all(connection):
    for source_key in SOURCE_REGISTRY:
        upload_source(source_key, connection)


def main():
    parser = argparse.ArgumentParser(description='Upload input files to database')
    parser.add_argument('--sources', nargs='+', help='Source(s) to upload (default: all)')
    parser.add_argument('--list', action='store_true', help='List registered sources and exit')

    args = parser.parse_args()

    if args.list:
        print("Registered sources:")
        for key in SOURCE_REGISTRY:
            print(f"  - {key}")
        return

    engine = create_engine(DATABASE_URL)
    connection = engine.connect()

    try:
        if args.sources:
            for source in args.sources:
                if source in SOURCE_REGISTRY:
                    upload_source(source, connection)
                else:
                    print(f"Unknown source: '{source}' - skipping")
        else:
            sources_to_process = list(SOURCE_REGISTRY.keys())
            for source_key in sources_to_process:
                upload_source(source_key, connection)
    finally:
        connection.close()

    print(f"\n{'='*60}")
    print("All sources processed")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
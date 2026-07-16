#!/usr/bin/env python3
"""
Database setup script for CritMAT.

Initializes the SQLite database with schema and seeds reference data.
Can be run independently: python -m database.populate_database
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from critmat.database.config import DATABASE_URL
from critmat.database.models import Base, FactEUReport, FactTradeParameter, Source, Country, Material
from critmat.database.upload_dataframe import upload_dataframe


def init_database():
    """Initialize the SQLite database with schema (tables, triggers, views)."""
    db_path = DATABASE_URL.replace('sqlite:///', '')

    if os.path.exists(db_path):
        response = input(f'Database {db_path} already exists. Delete and recreate? (y/N): ')
        if response.lower() != 'y':
            print('Skipping database initialization.')
            return False
        os.remove(db_path)

    print(f'Creating database: {db_path}')
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print('Database initialized successfully.')
    return True


def seed_database():
    """Seed the database with reference data from CSV files."""
    print('Seeding database...')

    engine = create_engine(DATABASE_URL)
    connection = engine.connect()

    seed_dir = 'input_data/seeds/'

    df = pd.read_csv(seed_dir + 'source.csv')
    upload_dataframe(df, Source.__table__, connection)

    df = pd.read_csv(seed_dir + 'country.csv')
    upload_dataframe(df, Country.__table__, connection)

    df = pd.read_csv(seed_dir + 'material.csv')
    upload_dataframe(df, Material.__table__, connection)

    df = pd.read_csv(seed_dir + 'eureport_results.csv')
    upload_dataframe(df, FactEUReport.__table__, connection)
    
    df = pd.read_csv(seed_dir + 'eureport_tradeparameters.csv')
    upload_dataframe(df, FactTradeParameter.__table__, connection)

    connection.close()
    print('Database seeded successfully.')


if __name__ == '__main__':
    print('=' * 60)
    print('CritMAT Database Setup')
    print('=' * 60)

    if init_database():
        seed_database()

    print()
    print('Setup complete!')
    print()
    print('Next steps:')
    print('  1. Add your data files to input_data/')
    print('  2. Upload data: python upload_input_files.py')
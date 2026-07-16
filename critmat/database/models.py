from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, REAL, UniqueConstraint, event, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Source(Base):
    __tablename__ = 'source'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    priority = Column(Integer)
    type = Column(String)
    access = Column(String)


class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    iseu = Column(Boolean)
    latitude = Column(REAL)
    longitude = Column(REAL)


class Material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    group = Column(String)
    eu_used_stage = Column(String)
    isrmis = Column(Boolean)


class FactCountryWGI(Base):
    __tablename__ = 'fact_countrywgi'
    id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    date_year = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'))
    publish_year = Column(Integer, nullable=False)
    mean = Column(REAL)
    voiceandaccountability = Column(REAL)
    politicalstabilitynoviolence = Column(REAL)
    governmenteffectiveness = Column(REAL)
    regulatoryquality = Column(REAL)
    ruleoflaw = Column(REAL)
    controlofcorruption = Column(REAL)
    __table_args__ = (
        UniqueConstraint('country_id', 'date_year', 'source_id', 'publish_year', name='unique_countrywgi'),
    )


class FactEUReport(Base):
    __tablename__ = 'fact_eureport'
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    date_year = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'))
    publish_year = Column(Integer, nullable=False)
    supply_risk = Column(REAL)
    economic_importance = Column(REAL)    
    eu_used_stage = Column(String)
    eu_stages = Column(String)
    eu_used_supply_primary = Column(String)
    supply_risk_primary = Column(REAL)
    eu_used_supply_refined = Column(String)
    supply_risk_refined = Column(REAL)
    si_ei = Column(REAL)
    si_sr = Column(REAL)
    import_reliance_primary = Column(REAL)
    import_reliance_refined = Column(REAL)
    end_of_life = Column(REAL)
    __table_args__ = (
        UniqueConstraint('material_id', 'date_year', 'source_id', 'publish_year', name='unique_eureport'),
    )


class FactMaterialProduction(Base):
    __tablename__ = 'fact_materialproduction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    category = Column(String, nullable=False)
    date_year = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'))
    publish_year = Column(Integer, nullable=False)
    quantity = Column(REAL, nullable=False)
    unit = Column(String)
    __table_args__ = (
        UniqueConstraint('country_id', 'material_id', 'date_year', 'source_id', 'publish_year', 'category', name='unique_materialproduction'),
    )


class FactMaterialTradeFlow(Base):
    __tablename__ = 'fact_materialtradeflow'
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    exporter_country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    importer_country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    category = Column(String, nullable=False)
    date_year = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'))
    publish_year = Column(Integer, nullable=False)
    quantity = Column(REAL, nullable=False)
    cn8codes = Column(String, nullable=False)
    unit = Column(String)
    value = Column(REAL, nullable=False)
    value_unit = Column(String)
    __table_args__ = (
        UniqueConstraint('material_id', 'exporter_country_id', 'importer_country_id', 'date_year', 'source_id', 'publish_year', 'category', 'cn8codes', name='unique_materialtradeflow'),
    )


class FactTradeParameter(Base):
    __tablename__ = 'fact_tradeparameter'
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    category = Column(String, nullable=False)
    date_year = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'))
    parameter = Column(REAL, nullable=False)
    scope = Column(String, nullable=False)
    __table_args__ = (
        UniqueConstraint('country_id', 'material_id', 'date_year', 'source_id', 'scope', 'category', name='unique_tradeparameter'),
    )


# ============================================================
# LOAD TRIGGERS AND VIEWS FROM SQL FILES
# ============================================================

import glob
import os

def _execute_sql_files(target, connection, **kwargs):
    dialect = connection.dialect.name
    if dialect == 'sqlite':
        base_dir = os.path.dirname(__file__)
        for f in sorted(glob.glob(os.path.join(base_dir, 'triggers', '*.sql'))):
            connection.execute(text(open(f).read()))
        for f in sorted(glob.glob(os.path.join(base_dir, 'views', '*.sql'))):
            connection.execute(text(open(f).read()))

event.listen(Base.metadata, "after_create", _execute_sql_files)
from critmat.database.config import DATABASE_URL
from sqlalchemy import create_engine
import pandas as pd

def get_data(type):
    """Fetch data from the database for a given table."""

    engine = create_engine(DATABASE_URL)
    if type == 'production':
        query = "SELECT fmp.*, m.name AS material_name, c.name AS country_name, s.name AS source_name FROM fact_materialproduction fmp" \
        " JOIN material m ON fmp.material_id = m.id" \
        " JOIN country c ON fmp.country_id = c.id" \
        " JOIN source s ON fmp.source_id = s.id"
    elif type == 'wgi':
        query = "SELECT fwgi.*, c.name AS country_name FROM fact_countrywgi fwgi"\
        " JOIN country c ON fwgi.country_id = c.id" 
    elif type == 'trade':
        query = "SELECT ftf.*, m.name AS material_name, c.name AS country_name FROM fact_materialtradeflow ftf" \
        " JOIN material m ON ftf.material_id = m.id" \
        " JOIN country c ON ftf.country_id = c.id" 
    elif type == 'eureport':
        query = "SELECT feu.*, m.name AS material_name FROM fact_eureport feu" \
        " JOIN material m ON feu.material_id = m.id"
    elif type == 'tradeparameters':
        query = "SELECT ftp.*, m.name AS material_name, c.name AS country_name FROM fact_tradeparameter_permaterial ftp"\
        " JOIN material m ON ftp.material_id = m.id" \
        " JOIN country c ON ftp.country_id = c.id" 
    elif type == 'supply':
        query = "SELECT fsp.*, m.name AS material_name, c.name AS country_name, s.name AS source_name FROM fact_materialsupply fsp" \
        " JOIN material m ON fsp.material_id = m.id" \
        " JOIN country c ON fsp.country_id = c.id" \
        " JOIN source s ON fsp.source_id = s.id"
    df = pd.read_sql(query, engine)
    return df
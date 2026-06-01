def get_data(type):
    """Fetch data from the database for a given table."""
    from critmat.database.config import DATABASE_URL
    from sqlalchemy import create_engine
    import pandas as pd

    engine = create_engine(DATABASE_URL)
    if type == 'production':
        query = "SELECT * FROM fact_materialproduction" \
        " JOIN material ON fact_materialproduction.material_id = material.id" \
        " JOIN country ON fact_materialproduction.country_id = country.id" 
    elif type == 'wgi':
        query = "SELECT * FROM fact_countrywgi"\
        " JOIN country ON fact_countrywgi.country_id = country.id" 
    elif type == 'trade':
        query = "SELECT * FROM fact_materialtradeflow"
    elif type == 'eureport':
        query = "SELECT * FROM fact_eureport"
    elif type == 'tradeparameters':
        query = "SELECT * FROM fact_tradeparameter_permaterial"\
        " JOIN material ON fact_tradeparameter_permaterial.material_id = material.id" \
        " JOIN country ON fact_tradeparameter_permaterial.country_id = country.id" 
    elif type == 'supply':
        query = "SELECT * FROM fact_materialsupply" \
        " JOIN material ON fact_materialsupply.material_id = material.id" \
        " JOIN country ON fact_materialsupply.country_id = country.id" 
    df = pd.read_sql(query, engine)
    return df
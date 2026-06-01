CREATE VIEW IF NOT EXISTS fact_materialsupply AS
WITH TRADE AS (
    SELECT
        material_id,
        exporter_country_id AS country_id,
        category,
        date_year,
        source_id,
        publish_year,
        SUM(quantity) AS supply,
        unit
    FROM fact_materialtradeflow mtf
    JOIN country c ON mtf.importer_country_id = c.id
    WHERE c.iseu IS TRUE
    GROUP BY material_id, exporter_country_id, category, date_year, source_id, publish_year, unit
),
PRODUCTION AS (
    SELECT
        material_id,
        country_id,
        category,
        date_year,
        source_id,
        publish_year,
        quantity AS supply,
        unit
    FROM fact_materialproduction fp
    JOIN country c ON fp.country_id = c.id
    WHERE c.iseu = TRUE AND quantity IS NOT NULL
)
SELECT * FROM PRODUCTION
UNION ALL
SELECT * FROM TRADE
WHERE supply IS NOT NULL;
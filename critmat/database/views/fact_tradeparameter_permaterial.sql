CREATE VIEW IF NOT EXISTS fact_tradeparameter_permaterial AS
SELECT country_id, material_id, category, parameter, scope
FROM fact_tradeparameter
UNION ALL
SELECT c.id AS country_id, m.id AS material_id, tf.category,
       CASE WHEN c.iseu THEN 0.8 ELSE 1.0 END AS parameter, tp.scope
FROM (SELECT id, iseu FROM country) c
CROSS JOIN (SELECT DISTINCT id FROM material) m
CROSS JOIN (SELECT DISTINCT category FROM fact_materialtradeflow) tf
CROSS JOIN (SELECT DISTINCT scope FROM fact_tradeparameter) tp
WHERE NOT EXISTS (
    SELECT 1 FROM fact_tradeparameter ex
    WHERE ex.material_id = m.id
      AND ex.country_id = c.id
      AND ex.category = tf.category
      AND ex.scope = tp.scope
);
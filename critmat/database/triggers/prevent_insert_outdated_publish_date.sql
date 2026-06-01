CREATE TRIGGER IF NOT EXISTS prevent_insert_outdated_publish_date
BEFORE INSERT ON fact_materialproduction
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM fact_materialproduction
            WHERE material_id = NEW.material_id
              AND country_id = NEW.country_id
              AND category = NEW.category
              AND date_year = NEW.date_year
              AND source_id = NEW.source_id
              AND publish_year > NEW.publish_year
        )
        THEN RAISE(IGNORE)
    END;
END;
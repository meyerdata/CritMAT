CREATE TRIGGER IF NOT EXISTS delete_outdated_production
BEFORE INSERT ON fact_materialproduction
FOR EACH ROW
BEGIN
    DELETE FROM fact_materialproduction
    WHERE material_id = NEW.material_id
      AND country_id = NEW.country_id
      AND category = NEW.category
      AND date_year = NEW.date_year
      AND source_id = NEW.source_id
      AND publish_year < NEW.publish_year;
END;
CREATE TRIGGER IF NOT EXISTS prevent_insert_production_zero
BEFORE INSERT ON fact_materialproduction
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.quantity = 0 THEN RAISE(IGNORE)
    END;
END;
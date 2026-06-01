CREATE TRIGGER IF NOT EXISTS prevent_insert_trade_zero
BEFORE INSERT ON fact_materialtradeflow
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.quantity = 0 THEN RAISE(IGNORE)
    END;
END;
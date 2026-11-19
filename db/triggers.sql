CREATE OR REPLACE FUNCTION forbid_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'table % is append-only', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS predictions_immutable ON predictions;
CREATE TRIGGER predictions_immutable BEFORE UPDATE OR DELETE ON predictions
  FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
DROP TRIGGER IF EXISTS predictions_no_truncate ON predictions;
CREATE TRIGGER predictions_no_truncate BEFORE TRUNCATE ON predictions
  FOR EACH STATEMENT EXECUTE FUNCTION forbid_mutation();

DROP TRIGGER IF EXISTS outcomes_immutable ON outcomes;
CREATE TRIGGER outcomes_immutable BEFORE UPDATE OR DELETE ON outcomes
  FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
DROP TRIGGER IF EXISTS anchors_immutable ON anchors;
CREATE TRIGGER anchors_immutable BEFORE UPDATE OR DELETE ON anchors
  FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
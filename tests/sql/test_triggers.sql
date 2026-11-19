DO $$
BEGIN
  BEGIN
    INSERT INTO model_versions (id, name, config_hash) VALUES (-1, 'trigger_test', 'x');
    INSERT INTO predictions (ticker, signal_date, horizon_days, score, model_version_id,
                             config_hash, features, created_at, commit_hash)
    VALUES ('US.TEST', '2026-01-01', 5, 0.1, -1, 'x', '{}', now(), 'trigger_test_hash');
    RAISE NOTICE 'PASS: insert allowed (appending works)';

    BEGIN
      UPDATE predictions SET score = 9 WHERE commit_hash = 'trigger_test_hash';
      RAISE NOTICE 'FAIL: edit was allowed';
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'PASS: edit blocked (%)', SQLERRM;
    END;

    BEGIN
      DELETE FROM predictions WHERE commit_hash = 'trigger_test_hash';
      RAISE NOTICE 'FAIL: delete was allowed';
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'PASS: delete blocked (%)', SQLERRM;
    END;

    BEGIN
      TRUNCATE predictions CASCADE;
      RAISE NOTICE 'FAIL: truncate was allowed';
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'PASS: truncate blocked (%)', SQLERRM;
    END;

    RAISE EXCEPTION 'cleanup' USING ERRCODE = 'XX999';
  EXCEPTION WHEN SQLSTATE 'XX999' THEN
    RAISE NOTICE 'test rows rolled back';
  END;
END $$;

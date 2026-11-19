CREATE TABLE IF NOT EXISTS prices (
  ticker text NOT NULL, date date NOT NULL,
  open double precision, high double precision, low double precision,
  close double precision, volume double precision,
  PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS model_versions (
  id serial PRIMARY KEY, name text NOT NULL, config_hash text NOT NULL,
  status text NOT NULL DEFAULT 'challenger' CHECK (status IN ('champion','challenger','retired')),
  trained_at timestamptz DEFAULT now(), metrics jsonb
);

CREATE TABLE IF NOT EXISTS predictions (
  id bigserial PRIMARY KEY,
  ticker text NOT NULL, signal_date date NOT NULL, horizon_days int NOT NULL,
  score double precision NOT NULL,
  model_version_id int NOT NULL REFERENCES model_versions(id),
  config_hash text NOT NULL,
  features jsonb NOT NULL,
  created_at timestamptz NOT NULL,
  commit_hash text NOT NULL UNIQUE,
  UNIQUE (ticker, signal_date, horizon_days, model_version_id)
);

CREATE TABLE IF NOT EXISTS outcomes (
  prediction_id bigint PRIMARY KEY REFERENCES predictions(id),
  fwd_ret double precision, realized_rank double precision,
  scored_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS paper_trades (
  id bigserial PRIMARY KEY, signal_date date, ticker text, weight double precision,
  entry_date date, exit_date date,
  gross_ret double precision, cost double precision, net_ret double precision
);

CREATE TABLE IF NOT EXISTS reflections (
  id serial PRIMARY KEY, created_at timestamptz DEFAULT now(),
  model_version_id int, stats jsonb, content text, llm_model text,
  label text DEFAULT 'hypotheses-not-conclusions'
);

CREATE TABLE IF NOT EXISTS anchors (
  day date PRIMARY KEY, merkle_root text NOT NULL, n_leaves int, anchored_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credits (user_id text PRIMARY KEY, balance int NOT NULL DEFAULT 0 CHECK (balance >= 0));
CREATE TABLE IF NOT EXISTS unlocks (
  user_id text NOT NULL, prediction_id bigint NOT NULL REFERENCES predictions(id),
  unlocked_at timestamptz DEFAULT now(), PRIMARY KEY (user_id, prediction_id)
);
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS accounts (
  wallet_id UUID PRIMARY KEY,
  asset TEXT NOT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT accounts_asset_len CHECK (char_length(asset) BETWEEN 3 AND 12)
);

CREATE TABLE IF NOT EXISTS journal_transactions (
  transaction_id UUID PRIMARY KEY,
  operation_scope TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  external_reference TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT journal_status_valid CHECK (status IN ('committed')),
  CONSTRAINT uq_idempotency_scope UNIQUE (operation_scope, idempotency_key)
);

CREATE TABLE IF NOT EXISTS journal_entries (
  entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id UUID NOT NULL REFERENCES journal_transactions(transaction_id),
  seq INT NOT NULL,
  wallet_id UUID NOT NULL REFERENCES accounts(wallet_id),
  amount NUMERIC(20, 6) NOT NULL,
  asset TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_journal_entry_txn_seq UNIQUE(transaction_id, seq),
  CONSTRAINT amount_non_zero CHECK (amount <> 0)
);

CREATE TABLE IF NOT EXISTS balance_projections (
  wallet_id UUID NOT NULL REFERENCES accounts(wallet_id),
  asset TEXT NOT NULL,
  balance NUMERIC(20, 6) NOT NULL DEFAULT 0,
  version BIGINT NOT NULL DEFAULT 0,
  as_of TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY(wallet_id, asset)
);

CREATE TABLE IF NOT EXISTS outbox_events (
  event_id UUID PRIMARY KEY,
  transaction_id UUID NOT NULL REFERENCES journal_transactions(transaction_id),
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_journal_entries_wallet_asset ON journal_entries(wallet_id, asset, created_at);
CREATE INDEX IF NOT EXISTS idx_journal_txn_created_at ON journal_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_outbox_unprocessed ON outbox_events(processed_at) WHERE processed_at IS NULL;

INSERT INTO accounts(wallet_id, asset, version)
VALUES ('00000000-0000-0000-0000-000000000001', 'USD', 0)
ON CONFLICT (wallet_id) DO NOTHING;

INSERT INTO balance_projections(wallet_id, asset, balance, version)
VALUES ('00000000-0000-0000-0000-000000000001', 'USD', 0, 0)
ON CONFLICT (wallet_id, asset) DO NOTHING;

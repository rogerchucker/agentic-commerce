CREATE OR REPLACE FUNCTION enforce_entry_asset_matches_account()
RETURNS TRIGGER AS $$
DECLARE
  account_asset TEXT;
BEGIN
  SELECT asset INTO account_asset FROM accounts WHERE wallet_id = NEW.wallet_id;
  IF account_asset IS NULL THEN
    RAISE EXCEPTION 'wallet % not found', NEW.wallet_id;
  END IF;
  IF account_asset <> NEW.asset THEN
    RAISE EXCEPTION 'entry asset % mismatches account asset %', NEW.asset, account_asset;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_entry_asset_matches_account ON journal_entries;
CREATE TRIGGER trg_entry_asset_matches_account
BEFORE INSERT ON journal_entries
FOR EACH ROW EXECUTE FUNCTION enforce_entry_asset_matches_account();

CREATE OR REPLACE FUNCTION enforce_transaction_balanced()
RETURNS TRIGGER AS $$
DECLARE
  txn_sum NUMERIC(20, 6);
  entry_count INT;
BEGIN
  SELECT COALESCE(SUM(amount), 0), COUNT(*)
  INTO txn_sum, entry_count
  FROM journal_entries
  WHERE transaction_id = NEW.transaction_id;

  IF entry_count < 2 THEN
    RAISE EXCEPTION 'transaction % requires at least 2 entries', NEW.transaction_id;
  END IF;

  IF txn_sum <> 0 THEN
    RAISE EXCEPTION 'transaction % unbalanced sum=%', NEW.transaction_id, txn_sum;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_balanced_txn ON journal_transactions;
CREATE CONSTRAINT TRIGGER trg_balanced_txn
AFTER INSERT OR UPDATE ON journal_transactions
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION enforce_transaction_balanced();

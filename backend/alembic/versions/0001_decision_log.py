"""append-only decision log with hash chain

Revision ID: 0001
"""

from alembic import op

revision = "0001"
down_revision = None

GENESIS = "0" * 64


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cc_app') THEN
            -- dev default; deployments must ALTER ROLE cc_app PASSWORD '...'
            CREATE ROLE cc_app LOGIN PASSWORD 'cc_app_dev';
          END IF;
        END $$
        """
    )
    op.execute(
        """
        CREATE TABLE decision_log (
          seq BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          decision_id TEXT NOT NULL UNIQUE,
          kayit_zamani TEXT NOT NULL,
          girdi_json TEXT NOT NULL,
          cikti_json TEXT NOT NULL,
          politika_surumu TEXT NOT NULL,
          politika_sha256 TEXT NOT NULL,
          bundle_sha256 TEXT NOT NULL,
          prev_hash TEXT NOT NULL UNIQUE,
          row_hash TEXT NOT NULL UNIQUE,
          CONSTRAINT hash_len CHECK (length(prev_hash) = 64 AND length(row_hash) = 64),
          CONSTRAINT genesis_or_linked CHECK (prev_hash <> row_hash)
        )
        """
    )
    # UNIQUE(prev_hash) makes a fork impossible even if the advisory lock were bypassed.
    op.execute(
        """
        CREATE FUNCTION decision_log_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'decision_log is append-only (% blocked)', TG_OP;
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER decision_log_no_update_delete BEFORE UPDATE OR DELETE ON decision_log "
        "FOR EACH ROW EXECUTE FUNCTION decision_log_append_only()"
    )
    op.execute(
        "CREATE TRIGGER decision_log_no_truncate BEFORE TRUNCATE ON decision_log "
        "FOR EACH STATEMENT EXECUTE FUNCTION decision_log_append_only()"
    )
    op.execute("REVOKE ALL ON decision_log FROM PUBLIC")
    op.execute("GRANT SELECT, INSERT ON decision_log TO cc_app")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS decision_log")
    op.execute("DROP FUNCTION IF EXISTS decision_log_append_only()")

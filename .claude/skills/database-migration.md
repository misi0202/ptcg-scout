# Database
SQLite at `data/ptcg.db`. Schema: `db/schema.sql` (`CREATE TABLE IF NOT EXISTS`). No migration framework.

**Adding columns**: 1) Add to `schema.sql` CREATE TABLE 2) Add param to `insert_*()` in `models.py` 3) Delete `data/ptcg.db` to rebuild. For retroactive: ALTER TABLE before `init_db()`, or just delete.

**Tables**: `cards` (UNIQUE on name+set_name+card_number), `prices` (FK→cards, source+price+sale_date), `mentions` (FK→cards, source+keyword+date), `scores`, `boxes`.

**Patterns**: `INSERT OR IGNORE` for idempotency. Return id: `SELECT id FROM cards WHERE name=? AND set_name=?`. `conn.row_factory = sqlite3.Row`. Batch commit after loop, not per-row. Index FK + date columns.

**Storage**: `*.db` in `.gitignore`. `data/` JSON files committed, DB file is NOT.

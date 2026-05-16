# Database Migration Rules

## Schema Management
- Single source of truth: `db/schema.sql` with `CREATE TABLE IF NOT EXISTS` statements
- `init_db()` in `db/models.py` reads and executes `schema.sql`
- **No migration framework** — schema changes are additive (new columns/tables only)

## Adding a New Column
1. Add column to `CREATE TABLE IF NOT EXISTS` in `schema.sql` (with `DEFAULT` or nullable)
2. Add parameter to the corresponding `insert_*()` function in `models.py`
3. Delete `data/ptcg.db` to force fresh creation on next run
4. If column must be populated retroactively: ALTER TABLE in Python before `init_db()`, or delete DB

## Table Design Rules
- All tables use `INTEGER PRIMARY KEY AUTOINCREMENT` for id
- Timestamps: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` for `fetched_at`/`updated_at` columns
- Foreign keys: `card_id` references `cards(id)` in all related tables
- `UNIQUE(name, set_name, card_number)` on cards table — prevents duplicates but allows same card across sets
- Indexes on foreign keys and date columns for query performance

## Insert Pattern
- Use `INSERT OR IGNORE` for idempotent writes
- Return inserted/existing id: `SELECT id FROM cards WHERE name=? AND set_name=?`
- `conn.row_factory = sqlite3.Row` for dict-like row access
- Explicit `conn.commit()` after batch inserts, not per-row

## Storage Location
- Database file: `data/ptcg.db`
- `.gitignore` excludes `*.db` — database is rebuilt from scratch on each machine
- `data/` directory is committed to git for `cards.json`/`boxes.json`/`history/` but NOT the .db file

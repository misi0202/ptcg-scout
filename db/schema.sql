CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    set_name TEXT NOT NULL,
    card_number TEXT,
    pokemon_name TEXT,
    artist TEXT,
    rarity TEXT,
    image_url TEXT,
    game TEXT DEFAULT 'pokemon',
    psa10_pop INTEGER DEFAULT 0,
    psa_total_pop INTEGER DEFAULT 0,
    UNIQUE(name, set_name, card_number)
);

CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    price REAL NOT NULL,
    condition TEXT,
    sale_date DATE,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    keyword TEXT,
    mention_count INTEGER DEFAULT 1,
    sentiment TEXT,
    mention_date DATE NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL UNIQUE,
    aesthetic_score REAL DEFAULT 0,
    ip_score REAL DEFAULT 0,
    narrative_score REAL DEFAULT 0,
    pop_multiplier REAL DEFAULT 1.0,
    composite_score REAL DEFAULT 0,
    trend_signal TEXT,
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS boxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    set_name TEXT NOT NULL,
    release_date DATE,
    reprint_status TEXT,
    current_price REAL,
    low_point_alert INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prices_card ON prices(card_id);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(sale_date);
CREATE INDEX IF NOT EXISTS idx_mentions_card ON mentions(card_id);
CREATE INDEX IF NOT EXISTS idx_mentions_date ON mentions(mention_date);

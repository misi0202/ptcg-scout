<div align="right"><sub><a href="README_CN.md">中文</a></sub></div>

# PTCG Scout

Pokemon TCG market sentiment monitor & card investment potential predictor. Tracks real transaction prices, community heat, and PSA population data — using supply-demand analysis and a four-quadrant scoring model to identify cards with appreciation potential and booster boxes near price lows.

## Screenshots

> Run `python main.py` then `cd web && npm run dev` to see the dashboard locally.

| TOP 30 Rankings | Card Detail |
|---|---|
| ![TOP 30](docs/screenshots/top30.png) | ![Card Detail](docs/screenshots/detail.png) |

| Box Tracker | History Snapshot |
|---|---|
| ![Boxes](docs/screenshots/boxes.png) | ![History](docs/screenshots/history.png) |

## Core Logic

```
Composite Score = (Aesthetic × 0.35 + IP Strength × 0.40 + Narrative × 0.25) × Pop Multiplier
```

- **Four-Quadrant Model**: Aesthetic Consensus, IP Strength, Narrative Value, Scarcity (Pop Multiplier)
- **Supply-Demand Analysis**: Volume-price relationship, 30-day trend detection
- **Trend Signals**: 🟢 Bullish / 🟡 Cautious / 🔴 Bearish / 🔵 Watch

### Pop Multiplier

| PSA 10 Population | Multiplier |
|---|---|
| < 100 | 1.15 |
| 100–500 | 1.10 |
| 500–2,000 | 1.00 |
| 2,000–5,000 | 0.93 |
| > 5,000 | 0.85 |

## Project Structure

```
ptcg-scout/
├── collectors/           # Data collection (eBay/PSA/TCGPlayer/Reddit/Discord)
├── analyzer/             # Scoring engine (scoring/supply-demand/trends/boxes)
├── notifier/             # Feishu webhook notifications
├── db/                   # SQLite storage
├── web/                  # Next.js frontend dashboard
├── config/               # Pokemon IP tier configuration
├── data/                 # JSON output + daily snapshots
└── .github/workflows/    # Scheduled daily run
```

## Quick Start

```bash
# Python environment
conda create -n ptcg-scout python=3.12 -y
conda activate ptcg-scout
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env: FEISHU_WEBHOOK_URL / REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET

# Run pipeline
python main.py

# Frontend
cd web && npm install && npm run build
```

## Scheduled Execution

GitHub Actions runs daily at UTC 22:00 (Beijing Time 06:00 next day). Configure `FEISHU_WEBHOOK_URL`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_IDS` in repository Settings → Secrets → Actions.

The pipeline degrades gracefully when secrets are missing — unavailable collectors are skipped, the rest continue normally.

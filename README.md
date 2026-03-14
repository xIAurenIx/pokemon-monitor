# Pokemon Monitor

Automated eBay price tracker and Discord alert bot for Pokemon sealed products.

## Deploy to Railway

### Environment variables (set these in Railway dashboard)
DATABASE_URL      = your Railway PostgreSQL connection string
DISCORD_WEBHOOK_URL = your Discord channel webhook URL
UI_PASSWORD       = a password of your choice for the web dashboard

### First deploy
Railway will automatically install requirements.txt and run both processes:
- web:    the product management dashboard (your private URL)
- worker: the scraper + alert pipeline (runs every 30 minutes)

The database tables and starting products are created automatically on first run.

## Project structure
models/schema.py        — database tables (products + transactions)
collectors/ebay.py      — eBay sold listings scraper
pipeline/processor.py   — dedup, store, price analysis
alerts/discord_bot.py   — Discord embed formatter and sender
web/app.py              — product management web UI
main.py                 — scheduler and pipeline entrypoint

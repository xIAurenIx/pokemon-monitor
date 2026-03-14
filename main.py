from models.schema import get_session, Product, create_tables
from collectors.ebay import fetch_sold_listings
from pipeline.processor import is_duplicate, store_transaction, analyse_price
from alerts.discord_bot import send_alert
from apscheduler.schedulers.blocking import BlockingScheduler
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def run_pipeline():
    """
    Full pipeline run — called every 30 minutes by the scheduler.
    1. Fetch all active products from DB
    2. Scrape eBay sold listings for each
    3. Filter duplicates
    4. Store new transactions
    5. Analyse price vs comps
    6. Send Discord alert
    """
    print("\n─── Pipeline run started ───")
    session = get_session()
    products = session.query(Product).filter_by(is_active=True).all()
    session.close()

    if not products:
        print("[Pipeline] No active products found. Add some via the Web UI.")
        return

    for product in products:
        print(f"\n[Pipeline] Processing: {product.product_name}")
        raw_listings = fetch_sold_listings(product.search_query)

        new_count = 0
        for raw in raw_listings:
            if is_duplicate(raw["transaction_id"]):
                continue

            transaction = store_transaction(raw, product.product_id)
            alert = analyse_price(transaction, product)

            if alert:
                send_alert(alert)
                new_count += 1

        print(f"[Pipeline] {new_count} new transactions for {product.product_name}")

    print("─── Pipeline run complete ───\n")


if __name__ == "__main__":
    # Create tables on first run
    create_tables()

    # Seed starting products if the table is empty
    _seed_products()

    # Run immediately once, then every 30 minutes
    run_pipeline()

    scheduler = BlockingScheduler()
    scheduler.add_job(run_pipeline, "interval", minutes=30)
    print("[Scheduler] Running every 30 minutes. Press Ctrl+C to stop.")
    scheduler.start()


def _seed_products():
    """Insert the three starting products if products table is empty."""
    session = get_session()
    if session.query(Product).count() > 0:
        session.close()
        return

    starting_products = [
        Product(
            product_id="PKM001",
            product_name="Pokemon Center ETB: Mega Evolution",
            search_query="pokemon center etb mega evolution",
            alert_threshold_percent=10.0,
        ),
        Product(
            product_id="PKM002",
            product_name="Pokemon Center ETB: Ascended Heroes",
            search_query="pokemon center etb ascended heroes",
            alert_threshold_percent=10.0,
        ),
        Product(
            product_id="PKM003",
            product_name="Chinese Simplified Jumbo Pack 151",
            search_query="chinese simplified jumbo pack 151",
            alert_threshold_percent=10.0,
        ),
    ]

    session.add_all(starting_products)
    session.commit()
    session.close()
    print("[Seed] 3 starting products added to database.")

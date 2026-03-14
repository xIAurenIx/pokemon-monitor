from models.schema import get_session, Transaction, Product
from datetime import datetime, timedelta
from statistics import median


# ── Duplicate check ──────────────────────────────────────────────────────────

def is_duplicate(transaction_id: str) -> bool:
    """Returns True if we've already stored this transaction."""
    session = get_session()
    exists = session.query(Transaction).filter_by(transaction_id=transaction_id).first()
    session.close()
    return exists is not None


# ── Store transaction ─────────────────────────────────────────────────────────

def store_transaction(raw: dict, product_id: str) -> Transaction:
    """Saves a new transaction to the database and returns it."""
    session = get_session()
    tx = Transaction(
        transaction_id=raw["transaction_id"],
        product_id=product_id,
        sale_price_gbp=raw["sale_price_gbp"],
        date_sold=raw["date_sold"],
        listing_title=raw.get("listing_title"),
        url=raw.get("url"),
        marketplace=raw.get("marketplace", "ebay"),
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    session.close()
    print(f"[DB] Stored: {raw['listing_title'][:50]} — £{raw['sale_price_gbp']}")
    return tx


# ── Price analysis ────────────────────────────────────────────────────────────

def analyse_price(transaction: Transaction, product: Product) -> dict | None:
    """
    Compares a new transaction against 30-day historical comps.
    Returns an alert dict if something noteworthy happened, else None.
    """
    session = get_session()

    # Get last 30 days of comps (excluding the transaction we just stored)
    since = datetime.utcnow() - timedelta(days=30)
    comps = (
        session.query(Transaction)
        .filter(
            Transaction.product_id == product.product_id,
            Transaction.date_sold >= since,
            Transaction.transaction_id != transaction.transaction_id,
        )
        .all()
    )
    session.close()

    prices = [c.sale_price_gbp for c in comps]
    new_price = transaction.sale_price_gbp
    threshold = product.alert_threshold_percent / 100

    # Always send a standard "new sale" alert
    alert = {
        "type": "new_sale",
        "product": product,
        "transaction": transaction,
        "new_price": new_price,
        "avg_price": None,
        "pct_change": None,
        "is_ath": False,
        "is_atl": False,
    }

    if len(prices) >= 3:  # need at least 3 comps for meaningful analysis
        avg = median(prices)
        pct_change = (new_price - avg) / avg
        alert["avg_price"] = round(avg, 2)
        alert["pct_change"] = round(pct_change * 100, 1)

        if pct_change >= threshold:
            alert["type"] = "spike"
        elif pct_change <= -threshold:
            alert["type"] = "dip"

    # Check all-time high / low across entire history
    session = get_session()
    all_prices = (
        session.query(Transaction.sale_price_gbp)
        .filter(
            Transaction.product_id == product.product_id,
            Transaction.transaction_id != transaction.transaction_id,
        )
        .all()
    )
    session.close()

    all_prices_flat = [p[0] for p in all_prices]
    if all_prices_flat:
        if new_price > max(all_prices_flat):
            alert["type"] = "ath"
            alert["is_ath"] = True
        elif new_price < min(all_prices_flat):
            alert["type"] = "atl"
            alert["is_atl"] = True

    return alert

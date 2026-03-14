from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Product(Base):
    """
    One row per product you want to track.
    You manage these through the Web UI.
    """
    __tablename__ = "products"

    product_id       = Column(String, primary_key=True)   # e.g. PKM001
    product_name     = Column(String, nullable=False)      # e.g. Pokemon Center ETB: Mega Evolution
    search_query     = Column(String, nullable=False)      # the exact search term sent to eBay
    marketplace      = Column(String, default="ebay")      # ebay / tcgplayer / cardmarket
    category         = Column(String, default="sealed")    # sealed / graded / single
    is_active        = Column(Boolean, default=True)       # False = paused, bot ignores it
    alert_threshold_percent = Column(Float, default=10.0)  # e.g. 10.0 means ±10%
    units_held       = Column(Integer, default=0)          # how many you personally own
    purchase_price_gbp = Column(Float, nullable=True)      # your cost per unit in £
    notes            = Column(Text, nullable=True)         # freeform notes
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    """
    One row per sold listing the scraper finds.
    Never deleted — this is your historical comps database.
    """
    __tablename__ = "transactions"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id   = Column(String, unique=True, nullable=False)  # eBay item ID — prevents duplicates
    product_id       = Column(String, nullable=False)               # links back to products table
    sale_price_gbp   = Column(Float, nullable=False)                # what it sold for in £
    date_sold        = Column(DateTime, nullable=False)             # when the sale completed
    listing_title    = Column(String, nullable=True)                # full eBay listing title
    url              = Column(String, nullable=True)                # direct link to listing
    marketplace      = Column(String, default="ebay")
    scraped_at       = Column(DateTime, default=datetime.utcnow)   # when our bot found it


def get_engine():
    url = os.environ["DATABASE_URL"]
    # Railway uses postgres:// but SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def create_tables():
    """Run once on first deploy to create both tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Tables created: products, transactions")


if __name__ == "__main__":
    create_tables()

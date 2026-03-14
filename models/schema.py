from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    product_id              = Column(String, primary_key=True)
    product_name            = Column(String, nullable=False)
    search_query            = Column(String, nullable=False)
    marketplace             = Column(String, default="ebay")
    category                = Column(String, default="sealed")
    is_active               = Column(Boolean, default=True)
    alert_threshold_percent = Column(Float, default=10.0)
    units_held              = Column(Integer, default=0)
    purchase_price_gbp      = Column(Float, nullable=True)
    notes                   = Column(Text, nullable=True)
    created_at              = Column(DateTime, default=datetime.utcnow)
    updated_at              = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, unique=True, nullable=False)
    product_id     = Column(String, nullable=False)
    sale_price_gbp = Column(Float, nullable=False)
    date_sold      = Column(DateTime, nullable=False)
    listing_title  = Column(String, nullable=True)
    url            = Column(String, nullable=True)
    marketplace    = Column(String, default="ebay")
    scraped_at     = Column(DateTime, default=datetime.utcnow)


def get_engine():
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+pg8000://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+pg8000://", 1)
    return create_engine(url)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def create_tables():
    engine = get_engine()
    Base.metadata.create_all(

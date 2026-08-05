"""
PostgreSQL Loader
Loads all cleaned and star-schema DataFrames into the sales_db database
using SQLAlchemy + psycopg2.

Environment variables (set in .env or docker-compose):
  POSTGRES_HOST     default: localhost
  POSTGRES_PORT     default: 5432
  POSTGRES_DB       default: sales_db
  POSTGRES_USER     default: postgres
  POSTGRES_PASSWORD (required)
"""

import os
import logging
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logs", "pipeline.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("postgres_loader")


# ── Connection ─────────────────────────────────────────────────────────────────

def get_engine(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
) -> Engine:
    """
    Create and return a SQLAlchemy engine.
    Falls back to environment variables if parameters are not supplied.
    """
    host = host or os.getenv("POSTGRES_HOST", "localhost")
    port = port or int(os.getenv("POSTGRES_PORT", "5432"))
    db = db or os.getenv("POSTGRES_DB", "sales_db")
    user = user or os.getenv("POSTGRES_USER", "postgres")
    password = password or os.getenv("POSTGRES_PASSWORD", "postgres")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(url, pool_pre_ping=True)
    logger.info("Database engine created — %s:%s/%s", host, port, db)
    return engine


# ── Generic loader ─────────────────────────────────────────────────────────────

def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    engine: Engine,
    if_exists: str = "replace",
    chunksize: int = 10_000,
) -> None:
    """
    Load a DataFrame into a PostgreSQL table.

    Parameters
    ----------
    df         : DataFrame to load
    table_name : Target table name
    engine     : SQLAlchemy engine
    if_exists  : 'replace' | 'append' | 'fail'
    chunksize  : Rows per batch
    """
    logger.info("Loading %d rows into table '%s' (if_exists=%s)", len(df), table_name, if_exists)
    try:
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=False,
            chunksize=chunksize,
            method="multi",
        )
        logger.info("Loaded into PostgreSQL — table: %s, rows: %d", table_name, len(df))
    except Exception as exc:
        logger.error("Failed to load table '%s': %s", table_name, exc)
        raise


# ── Load all tables ────────────────────────────────────────────────────────────

def load_all(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    products: pd.DataFrame,
    payments: pd.DataFrame,
    reviews: pd.DataFrame,
    items: pd.DataFrame,
    sellers: pd.DataFrame,
    fact_sales: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_seller: pd.DataFrame,
    dim_date: pd.DataFrame,
    engine: Optional[Engine] = None,
) -> None:
    """
    Load all tables into PostgreSQL in dependency order.
    """
    if engine is None:
        engine = get_engine()

    tables = {
        "customers": customers,
        "orders": orders,
        "products": products,
        "payments": payments,
        "reviews": reviews,
        "order_items": items,
        "sellers": sellers,
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_seller": dim_seller,
        "dim_date": dim_date,
        "fact_sales": fact_sales,
    }

    for table_name, df in tables.items():
        if df is not None and not df.empty:
            load_dataframe(df, table_name, engine)
        else:
            logger.warning("Skipping empty DataFrame for table: %s", table_name)

    logger.info("All tables loaded into PostgreSQL successfully")


# ── Health check ───────────────────────────────────────────────────────────────

def check_connection(engine: Engine) -> bool:
    """Test the database connection."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection: OK")
        return True
    except Exception as exc:
        logger.error("PostgreSQL connection failed: %s", exc)
        return False


if __name__ == "__main__":
    eng = get_engine()
    check_connection(eng)

import logging
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()

HOME_DIR = Path.home() / ".pandaledger"
HOME_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = HOME_DIR / "panda_ledger.db"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)

def run_migrations(engine):
    """Dynamically applies schema evolutions to the physical local file."""
    inspector = inspect(engine)
    
    if 'payroll_settings' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('payroll_settings')]
        
        with engine.begin() as conn:
            # V2 Migrations
            if 'pay_type' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_type VARCHAR DEFAULT 'Hourly'"))
            if 'pay_rate' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_rate FLOAT DEFAULT 45.78"))
            if 'hours_per_period' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN hours_per_period FLOAT DEFAULT 86.67"))
            if 'tax_rate_percent' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN tax_rate_percent FLOAT DEFAULT 20.0"))
            if 'savings_rate_percent' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN savings_rate_percent FLOAT DEFAULT 10.0"))
                
            # V3 Migrations (Dynamic Pay Dates & Periods)
            if 'pay_day_1' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_day_1 INTEGER DEFAULT 7"))
            if 'pay_day_2' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_day_2 INTEGER DEFAULT 22"))
            if 'pay_period_end_1' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_period_end_1 INTEGER DEFAULT 15"))
                logger.info("Migration: Injected 'pay_period_end_1' column")
            if 'pay_period_end_2' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_period_end_2 INTEGER DEFAULT 31"))
                logger.info("Migration: Injected 'pay_period_end_2' column")

def init_db():
    from . import schema 
    Base.metadata.create_all(engine)
    run_migrations(engine)
    logger.info(f"SUCCESS: Connected to database at {DB_PATH}")

init_db()
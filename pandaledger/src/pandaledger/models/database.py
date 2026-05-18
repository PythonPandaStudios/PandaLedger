import logging
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Initialize module logger
logger = logging.getLogger(__name__)

# --- 1. Base Model Definition ---
Base = declarative_base()

# --- 2. Path Resolution (Enforcing Local-First DB storage) ---
# Maps the SQLite database to a secure, user-specific OS directory
HOME_DIR = Path.home() / ".pandaledger"
HOME_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = HOME_DIR / "panda_ledger.db"

# --- 3. Engine Configuration ---
# 'check_same_thread': False is explicitly required so Toga's async background 
# workers can query the database without triggering SQLite thread violations.
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'check_same_thread': False})

# --- 4. Session Factory ---
Session = sessionmaker(bind=engine)

def run_migrations(engine):
    """
    Lightweight Data Migration Utility for SQLite.
    Detects if the schema has evolved and securely injects new columns 
    into existing tables without destroying the user's historical ledger data.
    """
    inspector = inspect(engine)
    
    # Check if the payroll_settings table exists before trying to migrate it
    if 'payroll_settings' in inspector.get_table_names():
        # Map out the existing columns currently in the SQLite file
        existing_columns = [col['name'] for col in inspector.get_columns('payroll_settings')]
        
        with engine.begin() as conn:
            # Dynamically inject missing columns based on our V2 Payroll Schema updates
            if 'pay_type' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_type VARCHAR DEFAULT 'Hourly'"))
                logger.info("Migration: Injected 'pay_type' column into payroll_settings")
                
            if 'pay_rate' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_rate FLOAT DEFAULT 45.78"))
                logger.info("Migration: Injected 'pay_rate' column into payroll_settings")
                
            if 'hours_per_period' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN hours_per_period FLOAT DEFAULT 86.67"))
                logger.info("Migration: Injected 'hours_per_period' column into payroll_settings")
                
            if 'tax_rate_percent' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN tax_rate_percent FLOAT DEFAULT 20.0"))
                logger.info("Migration: Injected 'tax_rate_percent' column into payroll_settings")
                
            if 'savings_rate_percent' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN savings_rate_percent FLOAT DEFAULT 10.0"))
                logger.info("Migration: Injected 'savings_rate_percent' column into payroll_settings")
            
            # V3 Migrations (Dynamic Pay Dates)
            if 'pay_day_1' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_day_1 INTEGER DEFAULT 15"))
                logger.info("Migration: Injected 'pay_day_1' column")
                
            if 'pay_day_2' not in existing_columns:
                conn.execute(text("ALTER TABLE payroll_settings ADD COLUMN pay_day_2 INTEGER DEFAULT 31"))
                logger.info("Migration: Injected 'pay_day_2' column")

def init_db():
    """
    Bootstraps the SQLite database engine.
    Creates tables if completely missing, or runs migrations if the schema has evolved.
    """
    # Local import to prevent circular dependency crashes with schema.py
    from . import schema 
    
    # SQLAlchemy create_all is safe; it will skip tables that already exist
    Base.metadata.create_all(engine)
    
    # Run our custom schema evolution check to patch old tables
    run_migrations(engine)
    
    logger.info(f"SUCCESS: Connected to database at {DB_PATH}")

# Fire DB initialization immediately on module load
init_db()
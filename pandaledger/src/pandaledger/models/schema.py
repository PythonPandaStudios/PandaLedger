from sqlalchemy import Column, Integer, String, Float, Date
from pydantic import BaseModel, Field
from datetime import date
from .database import Base

# --- SQLAlchemy Database Model ---
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    payee = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

# --- Pydantic Validation Model ---
class TransactionCreate(BaseModel):
    date: date
    payee: str = Field(..., min_length=1, description="Payee cannot be empty")
    amount: float = Field(..., description="Amount must be a valid number")

# --- Payroll Settings Models ---
class PayrollSettings(Base):
    __tablename__ = "payroll_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # --- V2 Dynamic Payroll Fields ---
    pay_type = Column(String, default="Hourly")          
    schedule = Column(String, default="Semi-Monthly")    
    pay_rate = Column(Float, default=45.78)              
    hours_per_period = Column(Float, default=86.67)      
    tax_rate_percent = Column(Float, default=20.0)       
    savings_rate_percent = Column(Float, default=10.0)
    
    # --- V3 Exact Calendar Matching Fields ---
    pay_day_1 = Column(Integer, default=7)
    pay_day_2 = Column(Integer, default=22)
    pay_period_end_1 = Column(Integer, default=15)
    pay_period_end_2 = Column(Integer, default=31)
    
    # --- V1 Legacy Fields (Preserved for SQLite NOT NULL constraints) ---
    hourly_rate = Column(Float, nullable=False, default=0.0)
    federal_tax_rate = Column(Float, nullable=False, default=0.0)
    state_tax_rate = Column(Float, nullable=False, default=0.0)

class PayrollSettingsUpdate(BaseModel):
    pay_type: str
    schedule: str
    pay_rate: float = Field(..., ge=0)
    hours_per_period: float = Field(..., ge=0)
    tax_rate_percent: float = Field(..., ge=0, le=100)
    savings_rate_percent: float = Field(..., ge=0, le=100)
    pay_day_1: int = Field(..., ge=1, le=31)
    pay_day_2: int = Field(..., ge=1, le=31)
    pay_period_end_1: int = Field(..., ge=1, le=31)
    pay_period_end_2: int = Field(..., ge=1, le=31)
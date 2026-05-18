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
    # Pydantic validation prevents saving empty fields
    payee: str = Field(..., min_length=1, description="Payee cannot be empty")
    amount: float = Field(..., description="Amount must be a valid number")

# --- Payroll Settings Models ---
class PayrollSettings(Base):
    __tablename__ = "payroll_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule = Column(String, nullable=False, default="Semi-Monthly")
    hourly_rate = Column(Float, nullable=False, default=0.0)
    federal_tax_rate = Column(Float, nullable=False, default=0.0)
    state_tax_rate = Column(Float, nullable=False, default=0.0)

class PayrollSettingsUpdate(BaseModel):
    schedule: str
    hourly_rate: float = Field(..., ge=0)
    federal_tax_rate: float = Field(..., ge=0, le=100)
    state_tax_rate: float = Field(..., ge=0, le=100)
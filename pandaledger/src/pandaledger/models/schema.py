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
    pay_type = Column(String, default="Hourly")          # 'Hourly' or 'Salary'
    schedule = Column(String, default="Semi-Monthly")    # 'Weekly', 'Bi-Weekly', 'Semi-Monthly', 'Monthly'
    pay_rate = Column(Float, default=45.78)              # Hourly rate or Yearly Salary
    hours_per_period = Column(Float, default=86.67)      # Avg hours per paycheck (Dynamic field)
    tax_rate_percent = Column(Float, default=20.0)       # Estimated combined tax burden
    savings_rate_percent = Column(Float, default=10.0)   # Savings goal for psychological momentum

class PayrollSettingsUpdate(BaseModel):
    pay_type: str
    schedule: str
    pay_rate: float = Field(..., ge=0)
    hours_per_period: float = Field(..., ge=0)
    tax_rate_percent: float = Field(..., ge=0, le=100)
    savings_rate_percent: float = Field(..., ge=0, le=100)
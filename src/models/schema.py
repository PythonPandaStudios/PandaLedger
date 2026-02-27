import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class AccountType(enum.Enum):
    CHECKING = "Checking"
    SAVINGS = "Savings"
    CREDIT = "Credit"

class CategoryType(enum.Enum):
    FIXED = "Fixed"
    VARIABLE = "Variable"
    SAVINGS = "Savings"

class Config(Base):
    __tablename__ = "config"
    key = Column(String, primary_key=True)
    value = Column(String)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Enum(AccountType))
    current_balance = Column(Float)
    transactions = relationship("Transaction", back_populates="account")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Enum(CategoryType))
    monthly_limit = Column(Float)
    transactions = relationship("Transaction", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    payee = Column(String)
    amount = Column(Float)
    notes = Column(String)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

class Deduction(Base):
    __tablename__ = "deductions"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    amount = Column(Float)
    is_percent = Column(Boolean)
    is_pre_tax = Column(Boolean)
    category = Column(String, default="Other Deduction")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    amount = Column(Float)
    is_global = Column(Boolean)
    month_idx = Column(Integer)
    category = Column(String, default="Other Expense")
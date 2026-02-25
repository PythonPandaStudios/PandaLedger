import enum
from sqlalchemy import Column, Integer, String, Float, Enum, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class AccountType(enum.Enum):
    CHECKING = "Checking"
    SAVINGS = "Savings"
    CREDIT = "Credit"

class CategoryType(enum.Enum):
    FIXED = "Fixed"
    VARIABLE = "Variable"
    DEBT = "Debt"
    SAVINGS = "Savings"

class Account(Base):
    """Model representing a bank or credit account."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    current_balance = Column(Float, default=0.0)

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

class Category(Base):
    """Model representing a budget category."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(CategoryType), nullable=False)
    monthly_limit = Column(Float, default=0.0)

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="category", cascade="all, delete-orphan")

class Transaction(Base):
    """Model representing a single ledger transaction."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    payee = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    notes = Column(String, nullable=True)
    receipt_path = Column(String, nullable=True)

    # Foreign Keys
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

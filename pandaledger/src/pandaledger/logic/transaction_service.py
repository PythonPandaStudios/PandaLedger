import logging
from datetime import date
from pydantic import ValidationError
from pandaledger.models.schema import TransactionCreate, Transaction
from pandaledger.models.database import Session

logger = logging.getLogger(__name__)

class TransactionService:
    @staticmethod
    def create(tx_date: date, payee: str, amount: float) -> tuple[bool, str]:
        """
        Validates input and commits a new transaction to the SQLite database.
        Returns a tuple: (Success Boolean, Status/Error Message)
        """
        try:
            # 1. Client-Side Data Cleansing & Validation
            valid_data = TransactionCreate(date=tx_date, payee=payee, amount=amount)
            
            # 2. Database Insert
            session = Session()
            db_transaction = Transaction(**valid_data.model_dump())
            
            session.add(db_transaction)
            session.commit()
            session.refresh(db_transaction)
            session.close()
            
            logger.info(f"Transaction inserted: {valid_data.payee} - ${valid_data.amount}")
            return True, "Transaction saved successfully."
            
        except ValidationError as e:
            logger.warning(f"Validation failed: {e}")
            return False, "Validation Error: Payee and Amount cannot be empty."
        except Exception as e:
            logger.error(f"Database error: {e}")
            return False, f"System Error: {str(e)}"
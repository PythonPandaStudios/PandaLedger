import logging
from datetime import datetime
from pandaledger.models.database import Session
from pandaledger.models.schema import Transaction

logger = logging.getLogger(__name__)

class MainController:
    def __init__(self):
        # We will load payroll settings here later
        pass

    def get_annual_stats(self) -> dict:
        """
        Calculates total gross, net, and savings. 
        Returns pure python dict.
        """
        # TODO: Replace with actual PayrollCalculator logic and DB aggregation queries
        # For now, returning structural data to prove the UI connection
        return {
            "gross": "$102,400.00",
            "net": "$76,500.00",
            "savings": "$12,450.00"
        }

    def get_year_overview_table(self) -> list[tuple]:
        """
        Returns a list of tuples representing rows for the Year Overview Toga Table.
        """
        # TODO: Replace with actual PayrollCalculator generation
        return [
            ("Feb 15", "86.6", "$45.78", "$3,964.54", "$3,105.12", "$3,105.12"),
            ("Feb 28", "86.6", "$45.78", "$3,964.54", "$3,105.12", "$6,210.24")
        ]

    def get_month_transactions(self, month_num: int) -> list[tuple]:
        """
        Queries the SQLite DB for all transactions in a specific month.
        month_num: 1 = Jan, 2 = Feb, etc.
        Returns a list of tuples formatted for the Toga Table.
        """
        try:
            session = Session()
            # Fetch all transactions (We will add month filtering later)
            # We sort by date descending for standard ledger view
            transactions = session.query(Transaction).order_by(Transaction.date.desc()).all()
            
            # Format pure data for Toga
            formatted_data = []
            for tx in transactions:
                # Assuming your schema has: date, payee, amount (and we mock category/notes for now)
                formatted_amount = f"${tx.amount:.2f}"
                formatted_data.append((
                    tx.date.strftime("%Y-%m-%d"), 
                    tx.payee, 
                    "Uncategorized", # Placeholder until categorization engine is ported
                    formatted_amount, 
                    "" # Notes placeholder
                ))
            
            session.close()
            return formatted_data
            
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            return []
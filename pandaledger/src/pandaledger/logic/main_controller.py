import logging
from datetime import datetime
from pandaledger.models.database import Session
from pandaledger.models.schema import Transaction, PayrollSettings

logger = logging.getLogger(__name__)

class MainController:
    def __init__(self):
        pass

    def get_annual_stats(self) -> dict:
        """
        Calculates total gross, net, and savings using the live estimate engine. 
        Returns pure python dict formatting for the Toga UI.
        """
        estimates = self.calculate_estimates()
        return {
            "gross": f"${estimates['yearly_gross']:,.2f}",
            "net": f"${estimates['yearly_net']:,.2f}",
            "savings": f"${estimates['yearly_savings']:,.2f}"
        }

    def get_year_overview_table(self) -> list[tuple]:
        """
        Returns a list of tuples representing rows for the Year Overview Toga Table.
        """
        # TODO: Replace with actual PayrollCalculator generation loop
        return [
            ("Feb 15", "86.6", "$45.78", "$3,964.54", "$3,105.12", "$3,105.12"),
            ("Feb 28", "86.6", "$45.78", "$3,964.54", "$3,105.12", "$6,210.24")
        ]

    def get_month_transactions(self, month_num: int) -> list[tuple]:
        """
        Queries the SQLite DB for all transactions in a specific month.
        Returns a list of tuples formatted for the Toga Table.
        """
        try:
            session = Session()
            # Sort by date descending for standard ledger view
            transactions = session.query(Transaction).order_by(Transaction.date.desc()).all()
            
            # Format pure data for Toga
            formatted_data = []
            for tx in transactions:
                formatted_amount = f"${tx.amount:.2f}"
                formatted_data.append((
                    tx.date.strftime("%Y-%m-%d"), 
                    tx.payee, 
                    "Uncategorized", 
                    formatted_amount, 
                    "" # Notes placeholder
                ))
            
            session.close()
            return formatted_data
            
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            return []

    def get_payroll_settings(self) -> dict:
        """
        Fetches the user's payroll configuration. If it doesn't exist, returns defaults.
        """
        session = Session()
        settings = session.query(PayrollSettings).filter(PayrollSettings.id == 1).first()
        session.close()

        if settings:
            return {
                "pay_type": settings.pay_type,
                "schedule": settings.schedule,
                "pay_rate": settings.pay_rate,
                "hours_per_period": settings.hours_per_period,
                "tax_rate_percent": settings.tax_rate_percent,
                "savings_rate_percent": settings.savings_rate_percent
            }
        else:
            return {
                "pay_type": "Hourly",
                "schedule": "Semi-Monthly",
                "pay_rate": 45.78,
                "hours_per_period": 86.67,
                "tax_rate_percent": 20.0,
                "savings_rate_percent": 10.0
            }

    def save_payroll_settings(self, data: dict) -> bool:
        """
        Validates and upserts the comprehensive payroll configuration into SQLite.
        """
        try:
            session = Session()
            settings = session.query(PayrollSettings).filter(PayrollSettings.id == 1).first()

            if not settings:
                settings = PayrollSettings(id=1)
                session.add(settings)

            # Update values from dict mapping
            settings.pay_type = data.get('pay_type', settings.pay_type)
            settings.schedule = data.get('schedule', settings.schedule)
            settings.pay_rate = float(data.get('pay_rate', settings.pay_rate))
            settings.hours_per_period = float(data.get('hours_per_period', settings.hours_per_period))
            settings.tax_rate_percent = float(data.get('tax_rate_percent', settings.tax_rate_percent))
            settings.savings_rate_percent = float(data.get('savings_rate_percent', settings.savings_rate_percent))
            
            session.commit()
            session.close()
            logger.info("Payroll settings successfully updated in database.")
            return True
        except Exception as e:
            logger.error(f"Failed to save payroll settings: {e}")
            return False

    def calculate_estimates(self, custom_settings: dict = None) -> dict:
        """
        Calculates Gross, Net, and Savings estimates.
        Accepts overriding dictionary for real-time UI previews without hitting the DB.
        """
        settings = custom_settings if custom_settings else self.get_payroll_settings()

        periods_map = {
            "Weekly": 52,
            "Bi-Weekly": 26,
            "Semi-Monthly": 24,
            "Monthly": 12
        }
        
        schedule = settings.get("schedule", "Semi-Monthly")
        periods = periods_map.get(schedule, 24)

        pay_type = settings.get("pay_type", "Hourly")
        pay_rate = float(settings.get("pay_rate", 0.0))
        hours = float(settings.get("hours_per_period", 0.0))
        tax_rate = float(settings.get("tax_rate_percent", 0.0))
        savings_rate = float(settings.get("savings_rate_percent", 0.0))

        # Gross calculation
        if pay_type == "Salary":
            yearly_gross = pay_rate
        else:
            yearly_gross = pay_rate * hours * periods

        # Net and Savings calculations
        tax_multiplier = 1.0 - (tax_rate / 100.0)
        yearly_net = yearly_gross * tax_multiplier
        yearly_savings = yearly_net * (savings_rate / 100.0)

        return {
            "yearly_gross": round(yearly_gross, 2),
            "yearly_net": round(yearly_net, 2),
            "yearly_savings": round(yearly_savings, 2)
        }
import logging
import datetime
import calendar
from pandaledger.models.database import Session
from pandaledger.models.schema import Transaction, PayrollSettings

logger = logging.getLogger(__name__)

class MainController:
    def __init__(self):
        pass

    def _count_weekdays(self, start_date: datetime.date, end_date: datetime.date) -> int:
        """Calculates exact Monday-Friday business days between two dates inclusive."""
        days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # 0-4 are Mon-Fri
                days += 1
            current += datetime.timedelta(days=1)
        return days

    def generate_pay_schedule(self, custom_settings: dict = None) -> list:
        """
        Generates a 12-month calendar mapping for the current year.
        Determines exact hour chunks (80, 88, 96) for hourly workers.
        Returns raw mathematical representations for the UI to format.
        """
        settings = custom_settings if custom_settings else self.get_payroll_settings()
        year = datetime.date.today().year
        
        schedule_data = []
        cumulative_net = 0.0

        pay_type = settings.get("pay_type", "Hourly")
        schedule = settings.get("schedule", "Semi-Monthly")
        pay_rate = float(settings.get("pay_rate", 0.0))
        tax_rate = float(settings.get("tax_rate_percent", 0.0))
        
        # Safe casting for day integers
        pd1 = int(settings.get("pay_day_1", 15))
        pd2 = int(settings.get("pay_day_2", 31))

        if schedule in ["Semi-Monthly", "Monthly"]:
            for month in range(1, 13):
                _, last_day = calendar.monthrange(year, month)
                
                # --- PERIOD 1 ---
                d1 = min(pd1, last_day) # Prevents Feb 30th errors
                date1 = datetime.date(year, month, d1)
                start1 = datetime.date(year, month, 1)
                
                if schedule == "Semi-Monthly":
                    # Exact M-F working hours calculation
                    hours1 = self._count_weekdays(start1, date1) * 8.0
                    gross1 = (hours1 * pay_rate) if pay_type == "Hourly" else (pay_rate / 24)
                    net1 = gross1 * (1.0 - tax_rate / 100.0)
                    cumulative_net += net1
                    
                    schedule_data.append({
                        "date": date1, "hours": hours1, "rate": pay_rate, 
                        "gross": gross1, "net": net1, "remaining": cumulative_net
                    })
                    
                    # --- PERIOD 2 ---
                    d2 = min(pd2, last_day)
                    date2 = datetime.date(year, month, d2)
                    start2 = date1 + datetime.timedelta(days=1)
                    
                    hours2 = self._count_weekdays(start2, date2) * 8.0 if start2 <= date2 else 0.0
                    gross2 = (hours2 * pay_rate) if pay_type == "Hourly" else (pay_rate / 24)
                    net2 = gross2 * (1.0 - tax_rate / 100.0)
                    cumulative_net += net2
                    
                    schedule_data.append({
                        "date": date2, "hours": hours2, "rate": pay_rate, 
                        "gross": gross2, "net": net2, "remaining": cumulative_net
                    })
                    
                elif schedule == "Monthly":
                    end_of_month = datetime.date(year, month, last_day)
                    hours1 = self._count_weekdays(start1, end_of_month) * 8.0
                    gross1 = (hours1 * pay_rate) if pay_type == "Hourly" else (pay_rate / 12)
                    net1 = gross1 * (1.0 - tax_rate / 100.0)
                    cumulative_net += net1
                    
                    schedule_data.append({
                        "date": date1, "hours": hours1, "rate": pay_rate, 
                        "gross": gross1, "net": net1, "remaining": cumulative_net
                    })
                    
        else:
            # Fallback block for fixed weekly/bi-weekly rotations
            periods = 52 if schedule == "Weekly" else 26
            hours = float(settings.get("hours_per_period", 80.0))
            start_date = datetime.date(year, 1, 1)
            days_step = 7 if schedule == "Weekly" else 14
            
            for i in range(periods):
                curr_date = start_date + datetime.timedelta(days=i*days_step)
                gross = (hours * pay_rate) if pay_type == "Hourly" else (pay_rate / periods)
                net = gross * (1.0 - tax_rate / 100.0)
                cumulative_net += net
                schedule_data.append({
                    "date": curr_date, "hours": hours, "rate": pay_rate, 
                    "gross": gross, "net": net, "remaining": cumulative_net
                })
                
        return schedule_data

    def calculate_estimates(self, custom_settings: dict = None) -> dict:
        """Derives exact yearly projections based on the generated calendar schedule."""
        settings = custom_settings if custom_settings else self.get_payroll_settings()
        schedule = self.generate_pay_schedule(settings)
        savings_rate = float(settings.get("savings_rate_percent", 0.0))
        
        yearly_gross = sum(period["gross"] for period in schedule)
        yearly_net = sum(period["net"] for period in schedule)
        yearly_savings = yearly_net * (savings_rate / 100.0)
        
        return {
            "yearly_gross": yearly_gross,
            "yearly_net": yearly_net,
            "yearly_savings": yearly_savings
        }

    def get_annual_stats(self) -> dict:
        estimates = self.calculate_estimates()
        return {
            "gross": f"${estimates['yearly_gross']:,.2f}",
            "net": f"${estimates['yearly_net']:,.2f}",
            "savings": f"${estimates['yearly_savings']:,.2f}"
        }

    def get_year_overview_table(self) -> list[tuple]:
        """Maps the raw calendar engine output perfectly into Toga string rows."""
        raw_schedule = self.generate_pay_schedule()
        return [
            (
                row["date"].strftime("%b %d"),
                f"{row['hours']:.1f}",
                f"${row['rate']:.2f}",
                f"${row['gross']:,.2f}",
                f"${row['net']:,.2f}",
                f"${row['remaining']:,.2f}"
            )
            for row in raw_schedule
        ]

    def get_month_transactions(self, month_num: int) -> list[tuple]:
        try:
            session = Session()
            transactions = session.query(Transaction).order_by(Transaction.date.desc()).all()
            formatted_data = []
            for tx in transactions:
                formatted_data.append((
                    tx.date.strftime("%Y-%m-%d"), 
                    tx.payee, "Uncategorized", f"${tx.amount:.2f}", ""
                ))
            session.close()
            return formatted_data
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            return []

    def get_payroll_settings(self) -> dict:
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
                "savings_rate_percent": settings.savings_rate_percent,
                "pay_day_1": settings.pay_day_1,
                "pay_day_2": settings.pay_day_2
            }
        else:
            return {
                "pay_type": "Hourly",
                "schedule": "Semi-Monthly",
                "pay_rate": 45.78,
                "hours_per_period": 86.67,
                "tax_rate_percent": 20.0,
                "savings_rate_percent": 10.0,
                "pay_day_1": 15,
                "pay_day_2": 31
            }

    def save_payroll_settings(self, data: dict) -> bool:
        try:
            session = Session()
            settings = session.query(PayrollSettings).filter(PayrollSettings.id == 1).first()

            if not settings:
                settings = PayrollSettings(id=1)
                session.add(settings)

            settings.pay_type = data.get('pay_type', settings.pay_type)
            settings.schedule = data.get('schedule', settings.schedule)
            settings.pay_rate = float(data.get('pay_rate', settings.pay_rate))
            settings.hours_per_period = float(data.get('hours_per_period', settings.hours_per_period))
            settings.tax_rate_percent = float(data.get('tax_rate_percent', settings.tax_rate_percent))
            settings.savings_rate_percent = float(data.get('savings_rate_percent', settings.savings_rate_percent))
            settings.pay_day_1 = int(data.get('pay_day_1', settings.pay_day_1))
            settings.pay_day_2 = int(data.get('pay_day_2', settings.pay_day_2))
            
            session.commit()
            session.close()
            return True
        except Exception as e:
            logger.error(f"Failed to save payroll settings: {e}")
            return False
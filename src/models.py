from dataclasses import dataclass
from datetime import date, timedelta
import calendar
from typing import List, Dict

@dataclass
class TaxResult:
    """Data structure for passing tax breakdown results."""
    fed_tax: float
    state_tax: float
    ss_tax: float
    medicare_tax: float
    additional_tax: float
    total_tax: float

@dataclass
class PaycheckResult:
    """Consolidated result for a single pay period."""
    date: date
    hours: float
    rate: float
    gross: float
    net: float
    taxes: TaxResult
    deductions_list: List[Dict]

class PayrollCalculator:
    """Handles all accounting logic for PandaLedger."""
    def __init__(self):
        self.rate_ss = 0.062        # Social Security (6.2%)
        self.rate_medicare = 0.0145 # Medicare (1.45%)
        
    def calculate_taxes(self, gross: float, taxable_income: float, config: Dict) -> TaxResult:
        """Performs tax calculations based on configuration rates."""
        fed_rate = float(config.get('fed_rate', 0))
        state_rate = float(config.get('state_rate', 0))
        add_tax_rate = float(config.get('add_tax_rate', 0))

        t_fed = taxable_income * (fed_rate / 100.0)
        t_state = taxable_income * (state_rate / 100.0)
        t_ss = gross * self.rate_ss
        t_med = gross * self.rate_medicare
        t_add = gross * (add_tax_rate / 100.0)
        
        total = t_fed + t_state + t_ss + t_med + t_add
        return TaxResult(t_fed, t_state, t_ss, t_med, t_add, total)

    def get_work_hours(self, start_dt: date, end_dt: date) -> float:
        """Calculates actual work hours (8/day) between two dates, excluding weekends."""
        work_days = 0
        curr = start_dt
        while curr <= end_dt:
            if curr.weekday() < 5:
                work_days += 1
            curr += timedelta(days=1)
        return float(work_days * 8)

    def calculate_pay_dates(self, config: Dict, year: int) -> List[Dict]:
        """Generates the full year pay schedule based on config."""
        schedule = []
        rate = float(config.get('rate', 0))
        sched_type = config.get('schedule', "Semi-Monthly")
        income_type = config.get('income_type', "Hourly")

        # Determine if we need to calculate a per-period salary
        # We calculate the full year first to get the count for salary distribution
        temp_dates = []

        if sched_type == "Weekly":
            d = date(year, 1, 1)
            while d.weekday() != 4: d += timedelta(days=1) 
            while d.year == year:
                temp_dates.append({'date': d, 'hours': 40.0})
                d += timedelta(weeks=1)

        elif sched_type == "Bi-Weekly":
            start_str = config.get('bw_start', f"{year}-01-02")
            try:
                d = date.fromisoformat(start_str)
            except ValueError:
                d = date(year, 1, 2)
            while d.year == year:
                temp_dates.append({'date': d, 'hours': 80.0})
                d += timedelta(weeks=2)

        elif sched_type == "Semi-Monthly":
            # Fetch custom days from config, fallback to standard 15/22 and 31/7
            p1_end_day = int(config.get('sm_p1_end', 15))
            p1_pay_day = int(config.get('sm_pay1', 22))
            p2_pay_day = int(config.get('sm_pay2', 7))

            for m in range(1, 13):
                # Period 1: Typically 1st to 15th, paid on 22nd
                p1_pay = date(year, m, p1_pay_day)
                p1_hours = self.get_work_hours(date(year, m, 1), date(year, m, p1_end_day))
                temp_dates.append({'date': p1_pay, 'hours': p1_hours})

                # Period 2: Typically 16th to end of month, paid on 7th of next month
                last_day = calendar.monthrange(year, m)[1]
                pay_year, pay_month = (year, m + 1) if m < 12 else (year + 1, 1)
                p2_pay = date(pay_year, pay_month, p2_pay_day)
                p2_hours = self.get_work_hours(date(year, m, p1_end_day + 1), date(year, m, last_day))
                temp_dates.append({'date': p2_pay, 'hours': p2_hours})

        elif sched_type == "Monthly":
            m_day = int(config.get('m_day', 1))
            for m in range(1, 13):
                temp_dates.append({'date': date(year, m, m_day), 'hours': 173.33})

        # Apply Salary vs Hourly logic to the generated dates
        num_periods = len(temp_dates)
        for item in temp_dates:
            if income_type == "Salary":
                # For salary, we divide the annual rate by number of pay periods
                period_gross = rate / num_periods if num_periods > 0 else 0
                # We calculate an "effective rate" for the table display
                eff_rate = period_gross / item['hours'] if item['hours'] > 0 else 0
                schedule.append({'date': item['date'], 'hours': item['hours'], 'rate': round(eff_rate, 2)})
            else:
                # Standard hourly logic
                schedule.append({'date': item['date'], 'hours': item['hours'], 'rate': rate})

        return schedule
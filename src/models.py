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

        if sched_type == "Weekly":
            d = date(year, 1, 1)
            while d.weekday() != 4: d += timedelta(days=1) 
            while d.year == year:
                schedule.append({'date': d, 'hours': 40.0, 'rate': rate})
                d += timedelta(weeks=1)
        elif sched_type == "Bi-Weekly":
            start_str = config.get('bw_start', f"{year}-01-02")
            d = date.fromisoformat(start_str)
            while d.year == year:
                schedule.append({'date': d, 'hours': 80.0, 'rate': rate})
                d += timedelta(weeks=2)
        elif sched_type == "Semi-Monthly":
            for m in range(1, 13):
                # Period 1
                p1_pay = date(year, m, 22)
                schedule.append({'date': p1_pay, 'hours': self.get_work_hours(date(year, m, 1), date(year, m, 15)), 'rate': rate})
                # Period 2
                last_day = calendar.monthrange(year, m)[1]
                pay_year, pay_month = (year, m + 1) if m < 12 else (year + 1, 1)
                schedule.append({'date': date(pay_year, pay_month, 7), 'hours': self.get_work_hours(date(year, m, 16), date(year, m, last_day)), 'rate': rate})
        elif sched_type == "Monthly":
            m_day = int(config.get('m_day', 1))
            for m in range(1, 13):
                schedule.append({'date': date(year, m, m_day), 'hours': 173.33, 'rate': rate})
        return schedule
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
        temp_dates = []
        rate = float(config.get('rate', 0))
        sched_type = config.get('schedule', "Semi-Monthly")
        income_type = config.get('income_type', "Hourly")

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
            p1_end_day = int(config.get('sm_p1_end', 15))
            p1_pay_day = int(config.get('sm_pay1', 22))
            p2_pay_day = int(config.get('sm_pay2', 7))

            # Include Dec of previous year to catch the Jan 7th payment of the current year
            months_to_calc = [(year - 1, 12)] + [(year, m) for m in range(1, 13)]
            
            for y, m in months_to_calc:
                # Period 1
                p1_pay = date(y, m, p1_pay_day)
                if p1_pay.year == year:
                    p1_hours = self.get_work_hours(date(y, m, 1), date(y, m, p1_end_day))
                    temp_dates.append({'date': p1_pay, 'hours': p1_hours})

                # Period 2
                last_day = calendar.monthrange(y, m)[1]
                pay_year, pay_month = (y, m + 1) if m < 12 else (y + 1, 1)
                p2_pay = date(pay_year, pay_month, p2_pay_day)
                if p2_pay.year == year:
                    p2_hours = self.get_work_hours(date(y, m, p1_end_day + 1), date(y, m, last_day))
                    temp_dates.append({'date': p2_pay, 'hours': p2_hours})

        elif sched_type == "Monthly":
            m_day = int(config.get('m_day', 1))
            for m in range(1, 13):
                temp_dates.append({'date': date(year, m, m_day), 'hours': 173.33})

        schedule = []
        num_periods = len(temp_dates)
        for item in temp_dates:
            if income_type == "Salary":
                period_gross = rate / num_periods if num_periods > 0 else 0
                eff_rate = period_gross / item['hours'] if item['hours'] > 0 else 0
                schedule.append({'date': item['date'], 'hours': item['hours'], 'rate': round(eff_rate, 2)})
            else:
                schedule.append({'date': item['date'], 'hours': item['hours'], 'rate': rate})

        return schedule
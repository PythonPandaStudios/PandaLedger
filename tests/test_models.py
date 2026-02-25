import pytest
from datetime import date
from src.payroll import PayrollCalculator

@pytest.fixture
def calculator():
    """Provides a fresh instance of the calculator for each test."""
    return PayrollCalculator()

@pytest.fixture
def sample_config():
    """Standard configuration dictionary matching the app's current state."""
    return {
        "rate": 50.0,
        "fed_rate": 10.0,
        "state_rate": 5.0,
        "add_tax_rate": 1.0,
        "schedule": "Semi-Monthly",
        "income_type": "Hourly",
        "sm_p1_end": "15",
        "sm_pay1": "22",
        "sm_p2_end": "31",
        "sm_pay2": "7"
    }

def test_tax_calculation_logic(calculator, sample_config):
    """Verifies that math for fed, state, and FICA taxes is accurate."""
    gross = 1000.0
    taxable_income = 900.0  # e.g., after $100 pre-tax deduction
    
    result = calculator.calculate_taxes(gross, taxable_income, sample_config)
    
    # Assertions based on PayrollCalculator logic
    assert result.fed_tax == 90.0        # 900 * 0.10
    assert result.state_tax == 45.0      # 900 * 0.05
    assert result.ss_tax == 62.0         # 1000 * 0.062 (FICA on gross)
    assert result.medicare_tax == 14.5   # 1000 * 0.0145
    assert result.additional_tax == 10.0 # 1000 * 0.01
    assert result.total_tax == (90.0 + 45.0 + 62.0 + 14.5 + 10.0)

def test_semi_monthly_rollover_logic(calculator, sample_config):
    """Ensures January 7th of the current year is captured (rollover from previous Dec)."""
    year = 2026
    schedule = calculator.calculate_pay_dates(sample_config, year)
    
    # Sort to verify top-of-list ordering
    schedule.sort(key=lambda x: x['date'])
    
    # The first check should be Jan 7th, 2026 (earned in Dec 2025)
    assert schedule[0]['date'] == date(2026, 1, 7)
    # Total periods should be 24 (Jan 7 through Dec 22)
    assert len(schedule) == 24

def test_salary_distribution_logic(calculator, sample_config):
    """Verifies that annual salary is correctly split across pay periods."""
    salary_config = sample_config.copy()
    salary_config["income_type"] = "Salary"
    salary_config["rate"] = 120000.0  # $120k Annual
    
    schedule = calculator.calculate_pay_dates(salary_config, 2026)
    
    # $120,000 / 24 periods = $5,000 gross per period
    for period in schedule:
        period_gross = period['hours'] * period['rate']
        assert round(period_gross, 2) == 5000.0

def test_robustness_with_malformed_config(calculator):
    """Ensures calculator handles missing or non-numeric config values gracefully."""
    bad_config = {
        "fed_rate": "invalid", 
        "rate": None,
        "schedule": "Monthly"
    }
    # Should not raise TypeError/ValueError due to _safe_float helper
    result = calculator.calculate_taxes(1000.0, 1000.0, bad_config)
    assert result.fed_tax == 0.0
    
    schedule = calculator.calculate_pay_dates(bad_config, 2026)
    assert len(schedule) == 12
    assert schedule[0]['rate'] == 0.0

@pytest.mark.parametrize("start, end, expected_hours", [
    (date(2026, 1, 1), date(2026, 1, 1), 8.0),   # Thursday
    (date(2026, 1, 3), date(2026, 1, 4), 0.0),   # Saturday - Sunday
    (date(2026, 1, 1), date(2026, 1, 7), 40.0),  # 5 week days
])
def test_work_hours_calculation(calculator, start, end, expected_hours):
    """Tests the weekday-only hour logic."""
    assert calculator.get_work_hours(start, end) == expected_hours
import pytest
from datetime import date
from src.models import PayrollCalculator

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
        "schedule": "Semi-Monthly"
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
    assert result.additional_tax == 10.0  # 1000 * 0.01
    assert result.total_tax == (90.0 + 45.0 + 62.0 + 14.5 + 10.0)

def test_semi_monthly_schedule_generation(calculator, sample_config):
    """Ensures pay dates are generated correctly for the year."""
    year = 2026
    schedule = calculator.calculate_pay_dates(sample_config, year)
    
    # Semi-monthly always results in 24 pay periods
    assert len(schedule) == 24
    # First pay date of the year based on logic in models.py
    assert schedule[0]['date'] == date(2026, 1, 22)

@pytest.mark.parametrize("start, end, expected_hours", [
    (date(2026, 1, 1), date(2026, 1, 1), 8.0),   # Thursday
    (date(2026, 1, 3), date(2026, 1, 4), 0.0),   # Saturday - Sunday
    (date(2026, 1, 1), date(2026, 1, 7), 40.0),  # 5 week days
])
def test_work_hours_calculation(calculator, start, end, expected_hours):
    """Tests the weekday-only hour logic."""
    assert calculator.get_work_hours(start, end) == expected_hours
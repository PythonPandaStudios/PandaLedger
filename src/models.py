from dataclasses import dataclass

@dataclass
class TaxResult:
    """Data structure for passing tax breakdown results."""
    fed_tax: float
    state_tax: float
    ss_tax: float
    medicare_tax: float
    additional_tax: float
    total_tax: float

class PayrollCalculator:
    """Handles all accounting logic for PandaLedger."""
    def __init__(self):
        # Standard FICA rates
        self.rate_ss = 0.062        # Social Security (6.2%)
        self.rate_medicare = 0.0145 # Medicare (1.45%)
        
    def calculate_taxes(self, gross: float, taxable_income: float, fed_rate: float, 
                        state_rate: float, add_tax_rate: float) -> TaxResult:
        """Performs the actual tax calculations based on provided rates."""
        t_fed = taxable_income * (fed_rate / 100.0)
        t_state = taxable_income * (state_rate / 100.0)
        
        # FICA taxes are typically calculated on the full gross
        t_ss = gross * self.rate_ss
        t_med = gross * self.rate_medicare
        
        # Additional local or state payroll taxes (e.g., CO FAMLI)
        t_add = gross * (add_tax_rate / 100.0)
        
        total = t_fed + t_state + t_ss + t_med + t_add
        return TaxResult(t_fed, t_state, t_ss, t_med, t_add, total)
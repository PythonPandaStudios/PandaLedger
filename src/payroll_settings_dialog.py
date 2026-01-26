from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                               QDoubleSpinBox, QDialogButtonBox, QLabel)

class PayrollSettingsDialog(QDialog):
    """Submenu for tax rates and pay schedules."""
    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.setWindowTitle("Payroll & Tax Configuration")
        self.setMinimumWidth(400)
        self.config = current_config or {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.schedule_combo = QComboBox()
        self.schedule_combo.addItems(["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly"])
        self.schedule_combo.setCurrentText(self.config.get('schedule', "Semi-Monthly"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Hourly", "Salary"])
        self.type_combo.setCurrentText(self.config.get('income_type', "Hourly"))

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 1000000)
        self.rate_input.setPrefix("$")
        self.rate_input.setValue(self.config.get('rate', 45.78))

        self.state_combo = QComboBox()
        self.state_combo.addItems(["Colorado", "Texas", "California", "Florida", "Other"])
        self.state_combo.setCurrentText(self.config.get('state', "Colorado"))

        self.state_rate = QDoubleSpinBox()
        self.state_rate.setValue(self.config.get('state_rate', 4.4))

        self.fed_rate = QDoubleSpinBox()
        self.fed_rate.setValue(self.config.get('fed_rate', 12.0))
        
        self.add_tax_rate = QDoubleSpinBox()
        self.add_tax_rate.setToolTip("Additional taxes like CO FAMLI")
        self.add_tax_rate.setValue(self.config.get('add_tax_rate', 0.45))

        form.addRow("Pay Schedule:", self.schedule_combo)
        form.addRow("Income Type:", self.type_combo)
        form.addRow("Rate:", self.rate_input)
        form.addRow("Work State:", self.state_combo)
        form.addRow("State Income Tax (%):", self.state_rate)
        form.addRow("Federal Income Tax (%):", self.fed_rate)
        form.addRow("Other Payroll Tax (%):", self.add_tax_rate)

        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return {
            "schedule": self.schedule_combo.currentText(),
            "income_type": self.type_combo.currentText(),
            "rate": self.rate_input.value(),
            "state": self.state_combo.currentText(),
            "state_rate": self.state_rate.value(),
            "fed_rate": self.fed_rate.value(),
            "add_tax_rate": self.add_tax_rate.value()
        }

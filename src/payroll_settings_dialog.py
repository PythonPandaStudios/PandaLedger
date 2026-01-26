from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                               QLineEdit, QDialogButtonBox, QLabel, QWidget, QMessageBox)
from PySide6.QtGui import QDoubleValidator, QCloseEvent

class PayrollSettingsDialog(QDialog):
    """Submenu for tax rates and pay schedules with dynamic period logic."""
    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.setWindowTitle("Payroll & Tax Configuration")
        self.setMinimumWidth(450)
        self.config = current_config or {}
        # Keep a copy of the original state for change detection
        self.initial_state = self.config.copy()
        
        self.num_validator = QDoubleValidator(0.0, 1000000.0, 2)
        
        self.setup_ui()
        self.toggle_schedule_inputs()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.form = QFormLayout()

        self.state_combo = QComboBox()
        self.state_combo.addItems(["Colorado", "Texas", "California", "Florida", "Other"])
        self.state_combo.setCurrentText(self.config.get('state', "Colorado"))
        self.form.addRow("Work State:", self.state_combo)

        self.schedule_combo = QComboBox()
        self.schedule_combo.addItems(["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly"])
        self.schedule_combo.setCurrentText(self.config.get('schedule', "Semi-Monthly"))
        self.schedule_combo.currentTextChanged.connect(self.toggle_schedule_inputs)
        self.form.addRow("Pay Schedule:", self.schedule_combo)

        self.schedule_params_widget = QWidget()
        self.schedule_params_layout = QFormLayout(self.schedule_params_widget)
        self.schedule_params_layout.setContentsMargins(0, 0, 0, 0)
        self.form.addRow(self.schedule_params_widget)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Hourly", "Salary"])
        self.type_combo.setCurrentText(self.config.get('income_type', "Hourly"))
        
        self.rate_input = QLineEdit(str(self.config.get('rate', 45.78)))
        self.rate_input.setValidator(self.num_validator)
        
        self.state_rate = QLineEdit(str(self.config.get('state_rate', 4.4)))
        self.state_rate.setValidator(self.num_validator)

        self.fed_rate = QLineEdit(str(self.config.get('fed_rate', 12.0)))
        self.fed_rate.setValidator(self.num_validator)
        
        self.add_tax_rate = QLineEdit(str(self.config.get('add_tax_rate', 0.45)))
        self.add_tax_rate.setValidator(self.num_validator)

        self.form.addRow("Income Type:", self.type_combo)
        self.form.addRow("Rate ($):", self.rate_input)
        self.form.addRow("State Income Tax (%):", self.state_rate)
        self.form.addRow("Federal Income Tax (%):", self.fed_rate)
        self.form.addRow("Other Payroll Tax (%):", self.add_tax_rate)

        layout.addLayout(self.form)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.handle_cancel)
        layout.addWidget(self.button_box)

    def toggle_schedule_inputs(self):
        while self.schedule_params_layout.count():
            item = self.schedule_params_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        sched = self.schedule_combo.currentText()
        if sched == "Semi-Monthly":
            self.p1_end = QLineEdit(self.config.get('sm_p1_end', "15"))
            self.pay1 = QLineEdit(self.config.get('sm_pay1', "22"))
            self.p2_end = QLineEdit(self.config.get('sm_p2_end', "31"))
            self.pay2 = QLineEdit(self.config.get('sm_pay2', "7"))
            self.schedule_params_layout.addRow("First Period End (Day):", self.p1_end)
            self.schedule_params_layout.addRow("First Pay Day (Date):", self.pay1)
            self.schedule_params_layout.addRow("Second Period End (Day):", self.p2_end)
            self.schedule_params_layout.addRow("Second Pay Day (Date):", self.pay2)
        elif sched == "Bi-Weekly":
            self.bw_start = QLineEdit(self.config.get('bw_start', "2026-01-02"))
            self.schedule_params_layout.addRow("First Pay Date of Year:", self.bw_start)
        elif sched == "Monthly":
            self.m_day = QLineEdit(self.config.get('m_day', "1"))
            self.schedule_params_layout.addRow("Pay Day of Month:", self.m_day)

    def get_current_ui_data(self):
        """Helper to scrape the current UI state without finalizing."""
        data = {
            "schedule": self.schedule_combo.currentText(),
            "state": self.state_combo.currentText(),
            "income_type": self.type_combo.currentText(),
            "rate": float(self.rate_input.text() or 0),
            "state_rate": float(self.state_rate.text() or 0),
            "fed_rate": float(self.fed_rate.text() or 0),
            "add_tax_rate": float(self.add_tax_rate.text() or 0),
            "theme": self.config.get("theme", "Light") # Preserve theme
        }
        sched = data["schedule"]
        if sched == "Semi-Monthly" and hasattr(self, 'p1_end'):
            data.update({"sm_p1_end": self.p1_end.text(), "sm_pay1": self.pay1.text(), "sm_p2_end": self.p2_end.text(), "sm_pay2": self.pay2.text()})
        elif sched == "Bi-Weekly" and hasattr(self, 'bw_start'):
            data.update({"bw_start": self.bw_start.text()})
        elif sched == "Monthly" and hasattr(self, 'm_day'):
            data.update({"m_day": self.m_day.text()})
        return data

    def handle_cancel(self):
        """Checks for changes before allowing a silent close."""
        current_data = self.get_current_ui_data()
        
        # Compare current UI to initial state
        has_changes = False
        for key, val in current_data.items():
            if key in self.initial_state and str(val) != str(self.initial_state[key]):
                has_changes = True
                break
        
        if has_changes:
            reply = QMessageBox.warning(
                self, "Unsaved Changes",
                "You have made changes to the payroll settings. Are you sure you want to cancel and lose these edits?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.reject()
        else:
            self.reject()

    def get_data(self):
        return self.get_current_ui_data()
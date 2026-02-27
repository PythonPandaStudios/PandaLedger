import calendar
import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                               QLineEdit, QDialogButtonBox, QLabel, QWidget, 
                               QMessageBox, QScrollArea, QPushButton, QHBoxLayout, 
                               QDateEdit, QRadioButton, QButtonGroup)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Qt, Signal, QDate

from views.components import EXPENSE_CATEGORIES

class PayrollSettingsDialog(QDialog):
    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.setWindowTitle("Payroll & Tax Configuration")
        self.setMinimumWidth(450)
        self.config = current_config or {}
        self.initial_state = self.config.copy()
        
        self.num_validator = QDoubleValidator(0.0, 1000000.0, 2)
        self.num_validator.setNotation(QDoubleValidator.StandardNotation)
        
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
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.handle_cancel)
        layout.addWidget(self.button_box)

    def toggle_schedule_inputs(self):
        while self.schedule_params_layout.count():
            item = self.schedule_params_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        sched = self.schedule_combo.currentText()
        if sched == "Semi-Monthly":
            self.p1_end = QLineEdit(str(self.config.get('sm_p1_end', "15")))
            self.pay1 = QLineEdit(str(self.config.get('sm_pay1', "22")))
            self.p2_end = QLineEdit(str(self.config.get('sm_p2_end', "31")))
            self.pay2 = QLineEdit(str(self.config.get('sm_pay2', "7")))
            self.schedule_params_layout.addRow("First Period End (Day):", self.p1_end)
            self.schedule_params_layout.addRow("First Pay Day (Date):", self.pay1)
            self.schedule_params_layout.addRow("Second Period End (Day):", self.p2_end)
            self.schedule_params_layout.addRow("Second Pay Day (Date):", self.pay2)
        elif sched == "Bi-Weekly":
            current_year = datetime.date.today().year
            default_start = f"{current_year}-01-02"
            self.bw_start = QLineEdit(self.config.get('bw_start', default_start))
            self.schedule_params_layout.addRow("First Pay Date of Year:", self.bw_start)
        elif sched == "Monthly":
            self.m_day = QLineEdit(str(self.config.get('m_day', "1")))
            self.schedule_params_layout.addRow("Pay Day of Month:", self.m_day)

    def validate_and_accept(self):
        inputs = [self.rate_input, self.state_rate, self.fed_rate, self.add_tax_rate]
        for i in inputs:
            if not i.text() or i.text() == ".":
                QMessageBox.critical(self, "Validation Error", "Please ensure all tax rates and income values are valid numbers.")
                return
        self.accept()

    def get_current_ui_data(self):
        data = {
            "schedule": self.schedule_combo.currentText(),
            "state": self.state_combo.currentText(),
            "income_type": self.type_combo.currentText(),
            "rate": float(self.rate_input.text() or 0),
            "state_rate": float(self.state_rate.text() or 0),
            "fed_rate": float(self.fed_rate.text() or 0),
            "add_tax_rate": float(self.add_tax_rate.text() or 0),
            "theme": self.config.get("theme", "Light")
        }
        sched = data["schedule"]
        if sched == "Semi-Monthly" and hasattr(self, 'p1_end'):
            data.update({
                "sm_p1_end": self.p1_end.text(), 
                "sm_pay1": self.pay1.text(), 
                "sm_p2_end": self.p2_end.text(), 
                "sm_pay2": self.pay2.text()
            })
        elif sched == "Bi-Weekly" and hasattr(self, 'bw_start'):
            data.update({"bw_start": self.bw_start.text()})
        elif sched == "Monthly" and hasattr(self, 'm_day'):
            data.update({"m_day": self.m_day.text()})
        return data

    def handle_cancel(self):
        current_data = self.get_current_ui_data()
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


class ManageDeductionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Payroll Deductions")
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        self.scroll_area = QScrollArea(widgetResizable=True)
        self.container = QWidget()
        self.row_layout = QVBoxLayout(self.container)
        self.row_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.container)
        
        layout.addWidget(self.scroll_area)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ Add Deduction")
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)


class AddTransactionDialog(QDialog):
    payee_edited_signal = Signal(str)
    save_transaction_signal = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Transaction")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        
        # --- Type Radio Buttons ---
        type_layout = QHBoxLayout()
        self.radio_expense = QRadioButton("Expense")
        self.radio_deposit = QRadioButton("Deposit")
        self.radio_expense.setChecked(True) # Default to expense
        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.radio_expense)
        self.btn_group.addButton(self.radio_deposit)
        type_layout.addWidget(self.radio_expense)
        type_layout.addWidget(self.radio_deposit)
        self.form.addRow("Type:", type_layout)

        # --- Scope Selection Combo ---
        self.tx_scope = QComboBox()
        self.tx_scope.addItem("One-Time (Use Date)")
        self.tx_scope.addItem("Global (All Months)")
        self.tx_scope.addItems(list(calendar.month_name)[1:])
        self.tx_scope.currentIndexChanged.connect(self.toggle_date)
        self.form.addRow("Scope:", self.tx_scope)
        
        self.tx_date = QDateEdit()
        self.tx_date.setCalendarPopup(True)
        self.tx_date.setDate(QDate.currentDate())
        self.form.addRow("Date:", self.tx_date)
        
        self.tx_payee = QLineEdit()
        self.tx_payee.textEdited.connect(self.payee_edited_signal.emit)
        self.form.addRow("Payee:", self.tx_payee)
        
        self.tx_amount = QLineEdit()
        self.form.addRow("Amount:", self.tx_amount)
        
        self.tx_category = QComboBox()
        self.tx_category.addItems(EXPENSE_CATEGORIES)
        self.form.addRow("Category:", self.tx_category)
        
        self.tx_account = QComboBox()
        self.form.addRow("Account:", self.tx_account)
        
        self.tx_notes = QLineEdit()
        self.form.addRow("Notes:", self.tx_notes)
        
        layout.addLayout(self.form)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.emit_save)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
    def toggle_date(self):
        # Disable the date widget if a recurring budget scope is selected
        self.tx_date.setEnabled(self.tx_scope.currentIndex() == 0)
        
    def emit_save(self):
        data = {
            'tx_type': 'Expense' if self.radio_expense.isChecked() else 'Deposit',
            'scope_idx': self.tx_scope.currentIndex(),
            'date': self.tx_date.date().toPython(),
            'payee': self.tx_payee.text(),
            'amount': self.tx_amount.text(),
            'category': self.tx_category.currentText(),
            'account_id': self.tx_account.currentData(),
            'notes': self.tx_notes.text()
        }
        self.save_transaction_signal.emit(data)
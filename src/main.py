import sys
import datetime
import calendar
import sqlite3
from typing import List, Dict
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QScrollArea, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QComboBox, QMessageBox, QGridLayout,
                               QTabWidget, QFormLayout) # FIXED: Added QFormLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication

# Internal Imports
from theme_manager import THEMES
from models import PayrollCalculator, TaxResult
from payroll_settings_dialog import PayrollSettingsDialog

# --- Constants ---
DB_FILE = "budget_data.db"
CURRENT_YEAR = 2026

class DeductionRow(QWidget):
    def __init__(self, parent_window, db_id, name, amount, is_percent, is_pre_tax):
        super().__init__()
        self.main_window = parent_window
        self.db_id = db_id
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5) 
        layout.setSpacing(10)
        
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Label")
        self.name_input.textChanged.connect(self.update_db)
        
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setFixedWidth(80)
        self.amount_input.textChanged.connect(self.update_db)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["$", "%"])
        self.type_combo.setCurrentIndex(1 if is_percent else 0)
        self.type_combo.setFixedWidth(50)
        self.type_combo.currentIndexChanged.connect(self.update_db)
        
        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["Pre-Tax", "Post-Tax"])
        self.tax_combo.setCurrentIndex(0 if is_pre_tax else 1)
        self.tax_combo.setFixedWidth(80)
        self.tax_combo.currentIndexChanged.connect(self.update_db)
        
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.clicked.connect(self.delete_self)
        
        layout.addWidget(self.name_input, 3)
        layout.addWidget(self.amount_input, 0)
        layout.addWidget(self.type_combo, 0)
        layout.addWidget(self.tax_combo, 0)
        layout.addWidget(self.del_btn, 0)
        
        self.setLayout(layout)

    def update_db(self):
        try: val = float(self.amount_input.text())
        except ValueError: val = 0.0
        self.main_window.db_update_deduction(self.db_id, self.name_input.text(), val,
                                           self.type_combo.currentIndex() == 1, 
                                           self.tax_combo.currentIndex() == 0)
        self.main_window.recalculate_budget()

    def delete_self(self):
        self.main_window.db_delete_deduction(self.db_id)
        self.setParent(None)
        self.deleteLater()
        self.main_window.recalculate_budget()

    def get_values(self):
        try: val = float(self.amount_input.text())
        except ValueError: val = 0.0
        return {'name': self.name_input.text(), 'value': val, 
                'is_percent': self.type_combo.currentIndex() == 1, 
                'is_pre_tax': self.tax_combo.currentIndex() == 0}

class ExpenseRow(QWidget):
    def __init__(self, parent_window, db_id, name, amount):
        super().__init__()
        self.main_window = parent_window
        self.db_id = db_id
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5) 
        layout.setSpacing(10)
        
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Bill Name")
        self.name_input.textChanged.connect(self.update_db)
        
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setFixedWidth(80)
        self.amount_input.textChanged.connect(self.update_db)
        
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.clicked.connect(self.delete_self)
        
        layout.addWidget(self.name_input, 1)
        layout.addWidget(self.amount_input, 0)
        layout.addWidget(self.del_btn, 0)
        
        self.setLayout(layout)

    def update_db(self):
        try: val = float(self.amount_input.text())
        except ValueError: val = 0.0
        self.main_window.db_update_expense(self.db_id, self.name_input.text(), val)
        self.main_window.recalculate_budget()

    def delete_self(self):
        self.main_window.db_delete_expense(self.db_id)
        self.setParent(None)
        self.deleteLater()
        self.main_window.recalculate_budget()

    def get_values(self):
        try: val = float(self.amount_input.text())
        except ValueError: val = 0.0
        return {'name': self.name_input.text(), 'amount': val}

class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PandaLedger")
        self.resize(1350, 900)
        self.conn = None
        self.pay_schedule = []
        self.month_tabs_refs = [] 
        self.calculator = PayrollCalculator()
        self.current_config = {}

        self.init_db()
        self.load_settings()
        self.calculate_pay_dates()
        self.setup_ui()
        self.apply_theme("Light")
        self.load_data()

    def init_db(self):
        self.conn = sqlite3.connect(DB_FILE)
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER, name TEXT, amount REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS deductions (id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER, name TEXT, amount REAL, is_percent INTEGER, is_pre_tax INTEGER)''')
        self.conn.commit()

    def load_settings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM config")
        rows = cursor.fetchall()
        self.current_config = {r[0]: r[1] for r in rows}
        
        for k in ['rate', 'state_rate', 'fed_rate', 'add_tax_rate']:
            if k in self.current_config:
                self.current_config[k] = float(self.current_config[k])
        
        if not self.current_config:
            self.current_config = {
                "schedule": "Semi-Monthly", "income_type": "Hourly", "rate": 45.78,
                "state": "Colorado", "state_rate": 4.4, "fed_rate": 12.0, "add_tax_rate": 0.45
            }

    def save_settings(self, config_dict):
        cursor = self.conn.cursor()
        for k, v in config_dict.items():
            cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (k, str(v)))
        self.conn.commit()

    def calculate_pay_dates(self):
        """Calculates checks based on schedule settings."""
        self.pay_schedule = []
        rate = self.current_config.get('rate', 45.78)
        
        # Simple Semi-Monthly Logic
        for month in range(1, 13):
            p1_date = datetime.date(CURRENT_YEAR, month, 7)
            p2_date = datetime.date(CURRENT_YEAR, month, 22)
            self.pay_schedule.append({'date': p1_date, 'hours': 80, 'rate': rate})
            self.pay_schedule.append({'date': p2_date, 'hours': 80, 'rate': rate})

    def apply_theme(self, theme_name):
        self.current_theme = THEMES[theme_name]
        QApplication.instance().setStyleSheet(self.current_theme.stylesheet)
        self.recalculate_budget()

    def open_payroll_settings(self):
        dialog = PayrollSettingsDialog(self, self.current_config)
        if dialog.exec():
            self.current_config = dialog.get_data()
            self.save_settings(self.current_config)
            self.calculate_pay_dates()
            self.recalculate_budget()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)

        header = QFrame(objectName="Header")
        header.setFixedHeight(80)
        h_layout = QHBoxLayout(header)
        
        title_box = QVBoxLayout()
        title_box.addWidget(QLabel("PandaLedger", objectName="HeaderTitle"))
        self.subtitle = QLabel("", objectName="HeaderSubtitle")
        title_box.addWidget(self.subtitle)
        
        theme_combo = QComboBox()
        theme_combo.addItems(list(THEMES.keys()))
        theme_combo.currentTextChanged.connect(self.apply_theme)

        payroll_btn = QPushButton("Payroll Settings")
        payroll_btn.setObjectName("AddButton")
        payroll_btn.clicked.connect(self.open_payroll_settings)

        copy_btn = QPushButton("Copy for Excel", objectName="CopyButton")
        copy_btn.clicked.connect(self.copy_to_clipboard)

        h_layout.addLayout(title_box)
        h_layout.addStretch()
        h_layout.addWidget(QLabel("Theme:"))
        h_layout.addWidget(theme_combo)
        h_layout.addWidget(payroll_btn)
        h_layout.addWidget(copy_btn)
        main_layout.addWidget(header)

        content = QHBoxLayout()
        sidebar = QFrame(objectName="Sidebar")
        sidebar.setFixedWidth(400)
        s_layout = QVBoxLayout(sidebar)
        
        s_layout.addWidget(QLabel("PAYROLL DEDUCTIONS", objectName="SectionTitle"))
        self.ded_area = QScrollArea(widgetResizable=True)
        self.ded_cont = QWidget()
        self.ded_layout = QVBoxLayout(self.ded_cont)
        self.ded_layout.setAlignment(Qt.AlignTop)
        self.ded_area.setWidget(self.ded_cont)
        s_layout.addWidget(self.ded_area)
        
        btn_add_ded = QPushButton("+ Add Deduction", objectName="AddButton")
        btn_add_ded.clicked.connect(lambda: self.add_deduction_row())
        s_layout.addWidget(btn_add_ded)

        s_layout.addWidget(QLabel("MONTHLY EXPENSES", objectName="SectionTitle"))
        self.exp_area = QScrollArea(widgetResizable=True)
        self.exp_cont = QWidget()
        self.exp_layout = QVBoxLayout(self.exp_cont)
        self.exp_layout.setAlignment(Qt.AlignTop)
        self.exp_area.setWidget(self.exp_cont)
        s_layout.addWidget(self.exp_area)

        btn_add_exp = QPushButton("+ Add Expense", objectName="AddButton")
        btn_add_exp.clicked.connect(lambda: self.add_expense_row())
        s_layout.addWidget(btn_add_exp)

        self.lbl_total_exp = QLabel("Total: $0.00")
        s_layout.addWidget(self.lbl_total_exp)
        
        content.addWidget(sidebar)

        self.tabs = QTabWidget()
        self.setup_year_tab()
        self.month_names = list(calendar.month_name)[1:]
        for i in range(12): self.setup_month_tab(i)
        
        content.addWidget(self.tabs)
        main_layout.addLayout(content)

    def setup_year_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        stats = QGridLayout()
        self.card_gross = self.create_stat_card("EST. ANNUAL GROSS", "$0.00", "Annual Total")
        self.card_net = self.create_stat_card("EST. ANNUAL NET", "$0.00", "Take Home")
        self.card_savings = self.create_stat_card("EST. ANNUAL SAVINGS", "$0.00", "After Expenses")
        stats.addWidget(self.card_gross, 0, 0)
        stats.addWidget(self.card_net, 0, 1)
        stats.addWidget(self.card_savings, 0, 2)
        layout.addLayout(stats)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Date", "Hrs", "Rate", "Gross", "Net", "Remaining"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        self.tabs.addTab(tab, "Year Overview")

    def setup_month_tab(self, m_idx):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        left = QVBoxLayout()
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Date", "Gross", "Net"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setFixedHeight(200)
        left.addWidget(table)
        
        summary = QFrame(objectName="MonthSummaryBox")
        s_grid = QFormLayout(summary)
        l_inc = QLabel("$0.00")
        l_exp = QLabel("$0.00")
        l_rem = QLabel("$0.00")
        s_grid.addRow("Net Income:", l_inc)
        s_grid.addRow("Expenses:", l_exp)
        s_grid.addRow("Remaining:", l_rem)
        left.addWidget(summary)
        left.addStretch()
        
        right = QVBoxLayout()
        scroll = QScrollArea(objectName="ExpenseBreakdownBox", widgetResizable=True)
        cont = QWidget()
        grid = QGridLayout(cont)
        grid.setAlignment(Qt.AlignTop)
        scroll.setWidget(cont)
        right.addWidget(QLabel("Breakdown", objectName="HeaderTitle"))
        right.addWidget(scroll)

        layout.addLayout(left, 1)
        layout.addLayout(right, 1)
        self.tabs.addTab(tab, self.month_names[m_idx])
        self.month_tabs_refs.append({'table': table, 'inc': l_inc, 'exp': l_exp, 'rem': l_rem, 'grid': grid})

    def create_stat_card(self, title, val, sub):
        f = QFrame(objectName="StatCard")
        l = QVBoxLayout(f)
        l.addWidget(QLabel(title, objectName="StatTitle"))
        v = QLabel(val, objectName="StatValue")
        l.addWidget(v)
        l.addWidget(QLabel(sub, objectName="StatSub"))
        return f

    def recalculate_budget(self):
        """Uses the PayrollCalculator from models.py for all math."""
        self.subtitle.setText(f"{self.current_config['schedule']} | {self.current_config['state']} Tax Rules")
        
        expenses = [self.exp_layout.itemAt(i).widget().get_values() for i in range(self.exp_layout.count())]
        total_exp = sum(e['amount'] for e in expenses)
        self.lbl_total_exp.setText(f"Total Monthly: ${total_exp:,.2f}")
        
        deductions = [self.ded_layout.itemAt(i).widget().get_values() for i in range(self.ded_layout.count())]
        
        self.table.setRowCount(0)
        total_gross = 0
        total_net = 0
        monthly_data = {i: [] for i in range(12)}

        for check in self.pay_schedule:
            gross = check['hours'] * check['rate']
            pre_tax = sum(d['value'] if not d['is_percent'] else gross * (d['value']/100) 
                          for d in deductions if d['is_pre_tax'])
            post_tax = sum(d['value'] if not d['is_percent'] else gross * (d['value']/100) 
                           for d in deductions if not d['is_pre_tax'])
            
            taxable = max(0, gross - pre_tax)
            # Logic called from models.py
            taxes = self.calculator.calculate_taxes(gross, taxable, self.current_config['fed_rate'], 
                                                   self.current_config['state_rate'], 
                                                   self.current_config['add_tax_rate'])
            
            net = gross - pre_tax - taxes.total_tax - post_tax
            rem = net - (total_exp / 2)
            
            total_gross += gross
            total_net += net
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(check['date'].strftime("%b %d")))
            self.table.setItem(row, 1, QTableWidgetItem(str(check['hours'])))
            self.table.setItem(row, 2, QTableWidgetItem(f"${check['rate']}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"${gross:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"${net:,.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"${rem:,.2f}"))
            
            monthly_data[check['date'].month-1].append({'date': check['date'], 'gross': gross, 'net': net})

        for card, val in [(self.card_gross, total_gross), (self.card_net, total_net)]:
            for child in card.children():
                if child.objectName() == "StatValue": child.setText(f"${val:,.2f}")

        for m_idx, ref in enumerate(self.month_tabs_refs):
            checks = monthly_data[m_idx]
            ref['table'].setRowCount(0)
            m_net = sum(c['net'] for c in checks)
            for c in checks:
                r = ref['table'].rowCount()
                ref['table'].insertRow(r)
                ref['table'].setItem(r, 0, QTableWidgetItem(c['date'].strftime("%b %d")))
                ref['table'].setItem(r, 1, QTableWidgetItem(f"${c['gross']:,.2f}"))
                ref['table'].setItem(r, 2, QTableWidgetItem(f"${c['net']:,.2f}"))
            
            ref['inc'].setText(f"${m_net:,.2f}")
            ref['exp'].setText(f"${total_exp:,.2f}")
            ref['rem'].setText(f"${m_net - total_exp:,.2f}")

    def load_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, amount, is_percent, is_pre_tax FROM deductions")
        for r in cursor.fetchall(): self.add_deduction_row(r[0], r[1], r[2], bool(r[3]), bool(r[4]), False)
        cursor.execute("SELECT id, name, amount FROM expenses")
        for r in cursor.fetchall(): self.add_expense_row(r[0], r[1], r[2], False)
        self.recalculate_budget()

    def add_deduction_row(self, db_id=None, name="New", amount=0, is_pct=False, is_pre=True, save=True):
        if save:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO deductions (year, name, amount, is_percent, is_pre_tax) VALUES (?,?,?,?,?)",
                           (CURRENT_YEAR, name, amount, int(is_pct), int(is_pre)))
            self.conn.commit()
            db_id = cursor.lastrowid
        self.ded_layout.addWidget(DeductionRow(self, db_id, name, amount, is_pct, is_pre))

    def add_expense_row(self, db_id=None, name="New", amount=0, save=True):
        if save:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO expenses (year, name, amount) VALUES (?,?,?)", (CURRENT_YEAR, name, amount))
            self.conn.commit()
            db_id = cursor.lastrowid
        self.exp_layout.addWidget(ExpenseRow(self, db_id, name, amount))

    def db_update_deduction(self, db_id, name, amt, is_pct, is_pre):
        self.conn.cursor().execute("UPDATE deductions SET name=?, amount=?, is_percent=?, is_pre_tax=? WHERE id=?",
                                   (name, amt, int(is_pct), int(is_pre), db_id))
        self.conn.commit()

    def db_delete_deduction(self, db_id):
        self.conn.cursor().execute("DELETE FROM deductions WHERE id=?", (db_id,))
        self.conn.commit()

    def db_update_expense(self, db_id, name, amt):
        self.conn.cursor().execute("UPDATE expenses SET name=?, amount=? WHERE id=?", (name, amt, db_id))
        self.conn.commit()

    def db_delete_expense(self, db_id):
        self.conn.cursor().execute("DELETE FROM expenses WHERE id=?", (db_id,))
        self.conn.commit()

    def copy_to_clipboard(self):
        QGuiApplication.clipboard().setText("Budget data copied")
        QMessageBox.information(self, "Copied", "Data copied to clipboard.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BudgetApp()
    window.show()
    sys.exit(app.exec())
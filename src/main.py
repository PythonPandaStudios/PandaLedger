import os
import sys
import time
import datetime
import calendar
import sqlite3
from typing import List, Dict
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QScrollArea, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QComboBox, QMessageBox, QGridLayout,
                               QTabWidget, QFormLayout, QSplashScreen, QProgressBar)
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPixmap, QPainter, QIcon

# Internal Imports
from theme_manager import THEMES
from models import PayrollCalculator, TaxResult, PaycheckResult
from payroll_settings_dialog import PayrollSettingsDialog

import ctypes

# Use this to find the directory of the actual executable or script
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    # If frozen (PyInstaller), assets might be in a different relative spot
    ASSET_DIR = os.path.join(sys._MEIPASS, "assests") if hasattr(sys, '_MEIPASS') else os.path.join(APP_DIR, "assests")
    print(ASSET_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    # assets is one level up from src/
    ASSET_DIR = os.path.join(os.path.dirname(APP_DIR), "assests")
    print(ASSET_DIR)

DB_FILE = os.path.join(APP_DIR, "budget_data.db")
ICON_PATH = os.path.join(ASSET_DIR, "PandaLedger_256.png")

class DeductionRow(QWidget):
    dataChanged = Signal()
    deleted = Signal(int)

    def __init__(self, db_id, name, amount, is_percent, is_pre_tax):
        super().__init__()
        self.db_id = db_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        
        self.name_input = QLineEdit(name)
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setFixedWidth(80)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["$", "%"])
        self.type_combo.setCurrentIndex(1 if is_percent else 0)
        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["Pre-Tax", "Post-Tax"])
        self.tax_combo.setCurrentIndex(0 if is_pre_tax else 1)
        
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)

        layout.addWidget(self.name_input, 3)
        layout.addWidget(self.amount_input, 1)
        layout.addWidget(self.type_combo, 0)
        layout.addWidget(self.tax_combo, 0)
        layout.addWidget(self.del_btn, 0)

        # Connect signals
        self.name_input.textChanged.connect(lambda: self.dataChanged.emit())
        self.amount_input.textChanged.connect(lambda: self.dataChanged.emit())
        self.type_combo.currentIndexChanged.connect(lambda: self.dataChanged.emit())
        self.tax_combo.currentIndexChanged.connect(lambda: self.dataChanged.emit())
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.db_id))

    def get_values(self):
        try: val = float(self.amount_input.text())
        except ValueError: val = 0.0
        return {'id': self.db_id, 'name': self.name_input.text(), 'value': val, 
                'is_percent': self.type_combo.currentIndex() == 1, 
                'is_pre_tax': self.tax_combo.currentIndex() == 0}

class ExpenseRow(QWidget):
    dataChanged = Signal()
    deleted = Signal(int)

    def __init__(self, db_id, name, amount):
        super().__init__()
        self.db_id = db_id
        layout = QHBoxLayout(self)
        self.name_input = QLineEdit(name)
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setFixedWidth(80)
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)

        layout.addWidget(self.name_input, 1)
        layout.addWidget(self.amount_input, 0)
        layout.addWidget(self.del_btn, 0)

        self.name_input.textChanged.connect(lambda: self.dataChanged.emit())
        self.amount_input.textChanged.connect(lambda: self.dataChanged.emit())
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.db_id))

    def get_values(self):
        try: val = float(self.amount_input.text())
        except ValueError: val = 0.0
        return {'id': self.db_id, 'name': self.name_input.text(), 'amount': val}

class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PandaLedger")
        self.resize(1350, 900)
        self.set_app_icon()
        
        self.current_year = datetime.date.today().year
        self.calculator = PayrollCalculator()
        self.month_tabs_refs = []
        self.current_config = {}

        self.init_db()
        self.load_settings()
        self.setup_ui()
        self.apply_theme(self.current_config.get("theme", "Light"))
        self.load_data()

    def set_app_icon(self):
        if os.path.exists(ICON_PATH):
            app_icon = QIcon(ICON_PATH)
            self.setWindowIcon(app_icon)
            QApplication.setWindowIcon(app_icon)

    def init_db(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, amount REAL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS deductions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, amount REAL, is_percent INTEGER, is_pre_tax INTEGER)')

    def load_settings(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM config")
            self.current_config = {r[0]: r[1] for r in cursor.fetchall()}
        
        for k in ['rate', 'state_rate', 'fed_rate', 'add_tax_rate']:
            if k in self.current_config: self.current_config[k] = float(self.current_config[k])
        
        if not self.current_config:
            self.current_config = {"schedule": "Semi-Monthly", "rate": 45.78, "theme": "Light", "fed_rate": 12.0, "state_rate": 4.4, "add_tax_rate": 0.45}

    def save_setting(self, key, value):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))

    def apply_theme(self, theme_name):
        self.current_config["theme"] = theme_name
        self.save_setting("theme", theme_name)
        QApplication.instance().setStyleSheet(THEMES[theme_name].stylesheet)
        self.recalculate_budget()

    def open_payroll_settings(self):
        dialog = PayrollSettingsDialog(self, self.current_config)
        if dialog.exec():
            self.current_config = dialog.get_data()
            for k, v in self.current_config.items(): self.save_setting(k, v)
            self.recalculate_budget()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)

        # Header
        header = QFrame(objectName="Header")
        header.setFixedHeight(80)
        h_layout = QHBoxLayout(header)
        title_box = QVBoxLayout()
        title_box.addWidget(QLabel("PandaLedger", objectName="HeaderTitle"))
        self.subtitle = QLabel("", objectName="HeaderSubtitle")
        title_box.addWidget(self.subtitle)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.current_config.get("theme", "Light"))
        self.theme_combo.currentTextChanged.connect(self.apply_theme)

        payroll_btn = QPushButton("Payroll Settings")
        payroll_btn.clicked.connect(self.open_payroll_settings)

        copy_btn = QPushButton("Copy for Excel", objectName="CopyButton")
        copy_btn.clicked.connect(self.export_to_clipboard)

        h_layout.addLayout(title_box)
        h_layout.addStretch()
        h_layout.addWidget(QLabel("Theme:"))
        h_layout.addWidget(self.theme_combo)
        h_layout.addWidget(payroll_btn)
        h_layout.addWidget(copy_btn)
        main_layout.addWidget(header)

        # Sidebar
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
        
        btn_add_ded = QPushButton("+ Add Deduction")
        btn_add_ded.clicked.connect(lambda: self.add_deduction_ui())
        s_layout.addWidget(btn_add_ded)

        s_layout.addWidget(QLabel("MONTHLY EXPENSES", objectName="SectionTitle"))
        self.exp_area = QScrollArea(widgetResizable=True)
        self.exp_cont = QWidget()
        self.exp_layout = QVBoxLayout(self.exp_cont)
        self.exp_layout.setAlignment(Qt.AlignTop)
        self.exp_area.setWidget(self.exp_cont)
        s_layout.addWidget(self.exp_area)

        btn_add_exp = QPushButton("+ Add Expense")
        btn_add_exp.clicked.connect(lambda: self.add_expense_ui())
        s_layout.addWidget(btn_add_exp)

        self.lbl_total_exp = QLabel("Total: $0.00")
        s_layout.addWidget(self.lbl_total_exp)
        content.addWidget(sidebar)

        # Tabs
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
        stats.addWidget(self.card_gross, 0, 0); stats.addWidget(self.card_net, 0, 1); stats.addWidget(self.card_savings, 0, 2)
        layout.addLayout(stats)
        self.year_table = QTableWidget(0, 6)
        self.year_table.setHorizontalHeaderLabels(["Date", "Hrs", "Rate", "Gross", "Net", "Remaining"])
        self.year_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.year_table)
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
        l_inc, l_exp, l_rem = QLabel("$0.00"), QLabel("$0.00"), QLabel("$0.00")
        s_grid.addRow("Net Income:", l_inc); s_grid.addRow("Expenses:", l_exp); s_grid.addRow("Remaining:", l_rem)
        left.addWidget(summary); left.addStretch()

        right = QVBoxLayout()
        scroll = QScrollArea(objectName="ExpenseBreakdownBox", widgetResizable=True)
        cont = QWidget(); grid = QGridLayout(cont); grid.setAlignment(Qt.AlignTop)
        scroll.setWidget(cont)
        right.addWidget(QLabel("Breakdown", objectName="HeaderTitle")); right.addWidget(scroll)
        
        layout.addLayout(left, 1); layout.addLayout(right, 1)
        self.tabs.addTab(tab, self.month_names[m_idx])
        self.month_tabs_refs.append({'table': table, 'inc': l_inc, 'exp': l_exp, 'rem': l_rem, 'grid': grid})

    def create_stat_card(self, title, val, sub):
        f = QFrame(objectName="StatCard"); l = QVBoxLayout(f)
        l.addWidget(QLabel(title, objectName="StatTitle"))
        v = QLabel(val, objectName="StatValue"); l.addWidget(v)
        l.addWidget(QLabel(sub, objectName="StatSub"))
        return f

    def add_deduction_ui(self, db_id=None, name="New", amount=0, is_pct=False, is_pre=True):
        if db_id is None:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO deductions (name, amount, is_percent, is_pre_tax) VALUES (?,?,?,?)", (name, amount, int(is_pct), int(is_pre)))
                db_id = cursor.lastrowid
        row = DeductionRow(db_id, name, amount, is_pct, is_pre)
        row.dataChanged.connect(self.sync_deduction)
        row.deleted.connect(self.delete_deduction)
        self.ded_layout.addWidget(row)
        self.recalculate_budget()

    def add_expense_ui(self, db_id=None, name="New", amount=0):
        if db_id is None:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO expenses (name, amount) VALUES (?,?)", (name, amount))
                db_id = cursor.lastrowid
        row = ExpenseRow(db_id, name, amount)
        row.dataChanged.connect(self.sync_expense)
        row.deleted.connect(self.delete_expense)
        self.exp_layout.addWidget(row)
        self.recalculate_budget()

    def sync_deduction(self):
        d = self.sender().get_values()
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE deductions SET name=?, amount=?, is_percent=?, is_pre_tax=? WHERE id=?", (d['name'], d['value'], int(d['is_percent']), int(d['is_pre_tax']), d['id']))
        self.recalculate_budget()

    def sync_expense(self):
        e = self.sender().get_values()
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE expenses SET name=?, amount=? WHERE id=?", (e['name'], e['amount'], e['id']))
        self.recalculate_budget()

    def delete_deduction(self, db_id):
        with sqlite3.connect(DB_FILE) as conn: conn.execute("DELETE FROM deductions WHERE id=?", (db_id,))
        self.sender().setParent(None); self.recalculate_budget()

    def delete_expense(self, db_id):
        with sqlite3.connect(DB_FILE) as conn: conn.execute("DELETE FROM expenses WHERE id=?", (db_id,))
        self.sender().setParent(None); self.recalculate_budget()

    def recalculate_budget(self):
        """Pure logic and UI update loop."""
        self.subtitle.setText(f"{self.current_config.get('schedule')} | {self.current_config.get('state')} Tax Rules")
        
        # Get Expenses
        expenses = [self.exp_layout.itemAt(i).widget().get_values() for i in range(self.exp_layout.count())]
        total_exp = sum(e['amount'] for e in expenses)
        self.lbl_total_exp.setText(f"Total Monthly: ${total_exp:,.2f}")
        
        # Get Deductions
        deductions = [self.ded_layout.itemAt(i).widget().get_values() for i in range(self.ded_layout.count())]
        
        pay_schedule = self.calculator.calculate_pay_dates(self.current_config, self.current_year)
        self.year_table.setRowCount(0)
        total_gross, total_net = 0, 0
        monthly_data = {i: [] for i in range(12)}

        for check in pay_schedule:
            gross = check['hours'] * check['rate']
            check_ded_details = []
            pre_tax_total, post_tax_total = 0, 0
            
            for d in deductions:
                amt = d['value'] if not d['is_percent'] else gross * (d['value'] / 100)
                check_ded_details.append({'name': d['name'], 'amount': amt})
                if d['is_pre_tax']: pre_tax_total += amt
                else: post_tax_total += amt

            taxable = max(0, gross - pre_tax_total)
            taxes = self.calculator.calculate_taxes(gross, taxable, self.current_config)
            net = gross - pre_tax_total - taxes.total_tax - post_tax_total
            rem = net - (total_exp / 2)

            total_gross += gross; total_net += net
            
            row = self.year_table.rowCount(); self.year_table.insertRow(row)
            self.year_table.setItem(row, 0, QTableWidgetItem(check['date'].strftime("%b %d")))
            self.year_table.setItem(row, 1, QTableWidgetItem(str(check['hours'])))
            self.year_table.setItem(row, 2, QTableWidgetItem(f"${check['rate']}"))
            self.year_table.setItem(row, 3, QTableWidgetItem(f"${gross:,.2f}"))
            self.year_table.setItem(row, 4, QTableWidgetItem(f"${net:,.2f}"))
            self.year_table.setItem(row, 5, QTableWidgetItem(f"${rem:,.2f}"))
            
            # Map back to month tabs
            m_idx = check['date'].month - 1
            if check['date'].year > self.current_year: m_idx = 0 # Handle late period 2 pay in Jan
            monthly_data[m_idx].append({'date': check['date'], 'gross': gross, 'net': net, 'taxes': taxes, 'deductions_list': check_ded_details})

        # Update Stat Cards
        for child in self.card_gross.findChildren(QLabel):
            if child.objectName() == "StatValue": child.setText(f"${total_gross:,.2f}")
        for child in self.card_net.findChildren(QLabel):
            if child.objectName() == "StatValue": child.setText(f"${total_net:,.2f}")
        for child in self.card_savings.findChildren(QLabel):
            if child.objectName() == "StatValue": child.setText(f"${total_net - (total_exp * 12):,.2f}")

        # Update Monthly Tabs
        for m_idx, ref in enumerate(self.month_tabs_refs):
            checks = monthly_data[m_idx]
            ref['table'].setRowCount(0)
            m_net = sum(c['net'] for c in checks)
            for c in checks:
                r = ref['table'].rowCount(); ref['table'].insertRow(r)
                ref['table'].setItem(r, 0, QTableWidgetItem(c['date'].strftime("%b %d")))
                ref['table'].setItem(r, 1, QTableWidgetItem(f"${c['gross']:,.2f}"))
                ref['table'].setItem(r, 2, QTableWidgetItem(f"${c['net']:,.2f}"))
            
            ref['inc'].setText(f"${m_net:,.2f}")
            ref['exp'].setText(f"${total_exp:,.2f}")
            ref['rem'].setText(f"${m_net - total_exp:,.2f}")
            
            # Build Detailed Breakdown Grid
            grid = ref['grid']
            while grid.count():
                item = grid.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            
            row_idx = 0
            for check_data in checks:
                title = QLabel(f"Paycheck: {check_data['date'].strftime('%b %d, %Y')}")
                title.setStyleSheet("font-weight: bold; color: #3B82F6; font-size: 15px;")
                grid.addWidget(title, row_idx, 0, 1, 2); row_idx += 1
                
                grid.addWidget(QLabel("Gross Pay"), row_idx, 0)
                v_gross = QLabel(f"${check_data['gross']:,.2f}"); v_gross.setAlignment(Qt.AlignRight)
                grid.addWidget(v_gross, row_idx, 1); row_idx += 1
                
                # Taxes
                t = check_data['taxes']
                tax_map = [("Federal Income Tax", t.fed_tax), ("State Income Tax", t.state_tax), ("Social Security", t.ss_tax), ("Medicare", t.medicare_tax), ("Other Payroll Tax", t.additional_tax)]
                for label, val in tax_map:
                    if val > 0:
                        l = QLabel(f"  {label}"); l.setStyleSheet("color: #6B7280; font-size: 12px;"); grid.addWidget(l, row_idx, 0)
                        v = QLabel(f"-${val:,.2f}"); v.setStyleSheet("color: #EF4444; font-size: 12px;"); v.setAlignment(Qt.AlignRight); grid.addWidget(v, row_idx, 1)
                        row_idx += 1
                
                # Deductions
                for ded in check_data['deductions_list']:
                    l = QLabel(f"  {ded['name']}"); l.setStyleSheet("color: #6B7280; font-size: 12px;"); grid.addWidget(l, row_idx, 0)
                    v = QLabel(f"-${ded['amount']:,.2f}"); v.setStyleSheet("color: #EF4444; font-size: 12px;"); v.setAlignment(Qt.AlignRight); grid.addWidget(v, row_idx, 1)
                    row_idx += 1
                
                # Net
                net_l = QLabel("Check Net Total"); net_l.setStyleSheet("font-weight: bold; border-top: 1px solid #E5E7EB;"); grid.addWidget(net_l, row_idx, 0)
                net_v = QLabel(f"${check_data['net']:,.2f}"); net_v.setStyleSheet("font-weight: bold; border-top: 1px solid #E5E7EB;"); net_v.setAlignment(Qt.AlignRight); grid.addWidget(net_v, row_idx, 1)
                row_idx += 1
                grid.addWidget(QLabel(""), row_idx, 0); row_idx += 1 # Spacer

    def load_data(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, amount, is_percent, is_pre_tax FROM deductions")
            for r in cursor.fetchall(): self.add_deduction_ui(r[0], r[1], r[2], bool(r[3]), bool(r[4]))
            cursor.execute("SELECT id, name, amount FROM expenses")
            for r in cursor.fetchall(): self.add_expense_ui(r[0], r[1], r[2])

    def export_to_clipboard(self):
        output = "Date\tHrs\tRate\tGross\tNet\tRemaining\n"
        for r in range(self.year_table.rowCount()):
            row_data = [self.year_table.item(r, c).text() for c in range(self.year_table.columnCount())]
            output += "\t".join(row_data) + "\n"
        QGuiApplication.clipboard().setText(output)
        QMessageBox.information(self, "Exported", "Data copied for Excel.")

def show_splash(theme_palette):
    bg_color = QColor(theme_palette["bg_primary"])
    text_color = QColor(theme_palette["text_primary"])
    pixmap = QPixmap(500, 300); pixmap.fill(bg_color)
    painter = QPainter(pixmap)
    painter.setPen(text_color); painter.setFont(QFont("Arial", 28, QFont.Bold))
    painter.drawText(QRect(0, 50, 500, 50), Qt.AlignCenter, "PandaLedger")
    painter.setFont(QFont("Arial", 12)); painter.drawText(QRect(0, 100, 500, 30), Qt.AlignCenter, "PythonPandaStudios Accounting")
    painter.end()

    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    progress_bar = QProgressBar(splash); progress_bar.setGeometry(50, 220, 400, 20); progress_bar.setValue(0)
    
    is_dark = bg_color.lightness() < 128
    border_color = "#374151" if is_dark else "#D1D5DB"
    progress_bar.setStyleSheet(f"QProgressBar {{ border: 1px solid {border_color}; border-radius: 5px; text-align: center; color: {'white' if is_dark else 'black'}; }} QProgressBar::chunk {{ background-color: #3B82F6; }}")
    
    splash.show(); QApplication.processEvents(); time.sleep(0.5)
    steps = ["Connecting to Database...", "Loading Configuration...", "Applying Themes...", "Ready!"]
    for i, step in enumerate(steps):
        progress_bar.setValue((i + 1) * 25)
        splash.showMessage(f"  {step}", Qt.AlignBottom | Qt.AlignLeft, text_color)
        QApplication.processEvents(); time.sleep(0.5)
    return splash

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Pre-load theme for splash
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
        cursor.execute("SELECT value FROM config WHERE key='theme'")
        row = cursor.fetchone()
        saved_theme = row[0] if row else "Light"

    # FIX: Ensure the taskbar uses the custom window icon on Windows
    if sys.platform == 'win32':
        myappid = 'pythonpandastudios.pandaledger.1.0' # unique string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    splash = show_splash(THEMES[saved_theme].palette)
    window = BudgetApp()
    splash.finish(window)
    window.show()
    sys.exit(app.exec())
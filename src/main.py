import sys
import datetime
import calendar
import sqlite3
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QScrollArea, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QComboBox, QMessageBox, QGridLayout,
                               QTabWidget, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QClipboard, QGuiApplication

# --- Constants & Styles ---
DB_FILE = "budget_data.db"
CURRENT_YEAR = 2026

STYLE_SHEET = """
QMainWindow {
    background-color: #F9FAFB;
}
QWidget {
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
    color: #374151;
}

/* --- TABS --- */
QTabWidget::pane {
    border: 1px solid #E5E7EB;
    background: white;
    border-radius: 4px;
}
QTabBar::tab {
    background: #F3F4F6;
    border: 1px solid #E5E7EB;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #6B7280;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #FFFFFF;
    border-bottom-color: #FFFFFF;
    color: #1F2937;
}

/* --- HEADER STYLES --- */
QFrame#Header {
    background-color: #0F172A;
}
QFrame#Header QLabel {
    color: #FFFFFF;
}
QLabel#HeaderTitle {
    color: #FFFFFF;
    font-size: 20px;
    font-weight: bold;
}
QLabel#HeaderSubtitle {
    color: #94A3B8;
    font-size: 13px;
}

/* --- SIDEBAR --- */
QFrame#Sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E5E7EB;
}
QLabel#SectionTitle {
    color: #374151;
    font-weight: bold;
    font-size: 14px;
    padding-top: 10px;
    padding-bottom: 5px;
}

/* --- INPUTS --- */
QLineEdit {
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 6px;
    background-color: #FFFFFF;
    color: #374151;
    selection-background-color: #10B981;
}
QLineEdit:focus {
    border: 2px solid #3B82F6;
}
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 5px;
    color: #374151;
}
QComboBox::drop-down {
    border: 0px; 
    background-color: transparent;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #374151;
    selection-background-color: #EFF6FF;
    selection-color: #1F2937;
}

/* --- BUTTONS --- */
QPushButton#AddButton {
    background-color: #F3F4F6;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    color: #374151;
    padding: 6px;
    font-weight: bold;
}
QPushButton#AddButton:hover {
    background-color: #E5E7EB;
}
QPushButton#CopyButton {
    background-color: #059669;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton#CopyButton:hover {
    background-color: #047857;
}
QPushButton#DeleteButton {
    background-color: #EF4444;
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: bold;
}

/* --- TABLE (High Contrast Borders) --- */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #000000;       /* Black Border */
    gridline-color: #000000;         /* Black Gridlines */
    color: #374151;
    selection-background-color: #EFF6FF;
    selection-color: #1F2937;
    alternate-background-color: #1E293B; 
}
QHeaderView::section {
    background-color: #F3F4F6;
    padding: 8px;
    border: 1px solid #000000;       /* Black Border for Header */
    font-weight: bold;
    color: #1F2937;
}
/* Ensure cell item borders are visible */
QTableWidget::item {
    border-right: 1px solid #000000;
    border-bottom: 1px solid #000000;
}

/* --- CARDS --- */
QFrame#StatCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}
QLabel#StatTitle {
    color: #6B7280;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
}
QLabel#StatValue {
    font-size: 24px;
    font-weight: bold;
    color: #1F2937;
}
QLabel#StatSub {
    color: #9CA3AF;
    font-size: 11px;
}

/* --- MONTHLY TAB WIDGETS --- */
QFrame#MonthSummaryBox {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
}
QLabel#MonthBigLabel {
    font-size: 16px; 
    font-weight: bold;
    color: #1F2937;
}
QLabel#MoneyLabel {
    font-family: 'Segoe UI', monospace;
    font-weight: bold;
}
"""

class DeductionRow(QWidget):
    def __init__(self, parent_window, db_id, name, amount, is_percent, is_pre_tax):
        super().__init__()
        self.main_window = parent_window
        self.db_id = db_id
        
        layout = QHBoxLayout()
        # CHANGED: Added 10px margins on Left/Right to prevent touching container edges
        layout.setContentsMargins(10, 5, 10, 5) 
        # CHANGED: Increased spacing between internal elements
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
        try:
            val = float(self.amount_input.text())
        except ValueError:
            val = 0.0
            
        self.main_window.db_update_deduction(
            self.db_id,
            self.name_input.text(),
            val,
            self.type_combo.currentIndex() == 1, 
            self.tax_combo.currentIndex() == 0
        )
        self.main_window.recalculate_budget()

    def delete_self(self):
        self.main_window.db_delete_deduction(self.db_id)
        self.setParent(None)
        self.deleteLater()
        self.main_window.recalculate_budget()

    def get_values(self):
        try:
            val = float(self.amount_input.text())
        except ValueError:
            val = 0.0
        return {
            'name': self.name_input.text(),
            'value': val,
            'is_percent': self.type_combo.currentIndex() == 1,
            'is_pre_tax': self.tax_combo.currentIndex() == 0
        }

class ExpenseRow(QWidget):
    def __init__(self, parent_window, db_id, name, amount):
        super().__init__()
        self.main_window = parent_window
        self.db_id = db_id
        
        layout = QHBoxLayout()
        # CHANGED: Added 10px margins on Left/Right to prevent touching container edges
        layout.setContentsMargins(10, 5, 10, 5) 
        # CHANGED: Increased spacing between internal elements
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
        try:
            val = float(self.amount_input.text())
        except ValueError:
            val = 0.0
            
        self.main_window.db_update_expense(self.db_id, self.name_input.text(), val)
        self.main_window.recalculate_budget()

    def delete_self(self):
        self.main_window.db_delete_expense(self.db_id)
        self.setParent(None)
        self.deleteLater()
        self.main_window.recalculate_budget()

    def get_values(self):
        try:
            val = float(self.amount_input.text())
        except ValueError:
            val = 0.0
        return {'name': self.name_input.text(), 'amount': val}

class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PandaLedger")
        self.resize(1350, 900)
        self.conn = None
        self.pay_schedule = []
        self.month_tabs_refs = [] # To store references to monthly tab widgets
        
        # Init DB and Logic
        self.init_db()
        self.calculate_pay_schedule()
        
        # Setup UI
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header ---
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        header_text_layout = QVBoxLayout()
        title = QLabel("PandaLedger")
        title.setObjectName("HeaderTitle")
        sub = QLabel("Projections for $45.78/hr Semi-Monthly Schedule")
        sub.setObjectName("HeaderSubtitle")
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(sub)
        header_text_layout.setAlignment(Qt.AlignVCenter)

        copy_btn = QPushButton("Copy Data for Excel")
        copy_btn.setObjectName("CopyButton")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_to_clipboard)

        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        header_layout.addWidget(copy_btn)
        
        main_layout.addWidget(header)

        # --- Content Area ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        
        # === Sidebar (Inputs) ===
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(420)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(20) 
        
        # Tax Rate
        sidebar_layout.addWidget(QLabel("ESTIMATED TAX RATE (%)", objectName="SectionTitle"))
        self.tax_input = QLineEdit()
        self.tax_input.setPlaceholderText("22.0")
        self.tax_input.textChanged.connect(self.update_tax_db)
        sidebar_layout.addWidget(self.tax_input)

        # Deductions
        sidebar_layout.addWidget(QLabel("PAYROLL DEDUCTIONS", objectName="SectionTitle"))
        
        self.deductions_area = QScrollArea()
        self.deductions_area.setWidgetResizable(True)
        self.deductions_area.setFrameShape(QFrame.NoFrame)
        self.deductions_container = QWidget()
        self.deductions_layout = QVBoxLayout(self.deductions_container)
        self.deductions_layout.setContentsMargins(0,0,0,0)
        self.deductions_layout.setAlignment(Qt.AlignTop)
        self.deductions_area.setWidget(self.deductions_container)
        sidebar_layout.addWidget(self.deductions_area)
        
        add_ded_btn = QPushButton("+ Add Deduction")
        add_ded_btn.setObjectName("AddButton")
        add_ded_btn.setCursor(Qt.PointingHandCursor)
        add_ded_btn.clicked.connect(lambda: self.add_deduction_row())
        sidebar_layout.addWidget(add_ded_btn)

        # Expenses
        sidebar_layout.addWidget(QLabel("MONTHLY EXPENSES", objectName="SectionTitle"))
        
        self.expenses_area = QScrollArea()
        self.expenses_area.setWidgetResizable(True)
        self.expenses_area.setFrameShape(QFrame.NoFrame)
        self.expenses_container = QWidget()
        self.expenses_layout = QVBoxLayout(self.expenses_container)
        self.expenses_layout.setContentsMargins(0,0,0,0)
        self.expenses_layout.setAlignment(Qt.AlignTop)
        self.expenses_area.setWidget(self.expenses_container)
        sidebar_layout.addWidget(self.expenses_area)

        add_exp_btn = QPushButton("+ Add Expense")
        add_exp_btn.setObjectName("AddButton")
        add_exp_btn.setCursor(Qt.PointingHandCursor)
        add_exp_btn.clicked.connect(lambda: self.add_expense_row())
        sidebar_layout.addWidget(add_exp_btn)

        # Total Exp Display
        self.total_exp_label = QLabel("Total Monthly: $0.00")
        self.total_exp_label.setStyleSheet("color: #DC2626; font-weight: bold; margin-top: 10px;")
        self.total_exp_label.setAlignment(Qt.AlignRight)
        sidebar_layout.addWidget(self.total_exp_label)

        content_layout.addWidget(sidebar)

        # === Right Panel (Tabs) ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)

        # -- TAB 1: Year Overview --
        self.setup_year_overview_tab()

        # -- TAB 2-13: Monthly Breakdown --
        self.month_names = list(calendar.month_name)[1:]
        for i in range(12):
            self.setup_month_tab(i)

        content_layout.addWidget(right_panel)
        main_layout.addLayout(content_layout)

    def setup_year_overview_tab(self):
        year_tab = QWidget()
        layout = QVBoxLayout(year_tab)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(20)

        # Stats Cards
        stats_container = QGridLayout()
        stats_container.setSpacing(20)

        self.card_gross = self.create_stat_card("EST. ANNUAL GROSS", "$0.00", "Based on M-F calculation")
        self.card_net = self.create_stat_card("EST. ANNUAL NET", "$0.00", "After Taxes & Deductions", "#059669")
        self.card_savings = self.create_stat_card("EST. ANNUAL SAVINGS", "$0.00", "Income - Expenses", "#2563EB")
        
        stats_container.addWidget(self.card_gross, 0, 0)
        stats_container.addWidget(self.card_net, 0, 1)
        stats_container.addWidget(self.card_savings, 0, 2)
        
        layout.addLayout(stats_container)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Pay Date", "Period", "Hrs", "Rate", "Gross", "Est. Net", "Remaining"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True) 
        
        layout.addWidget(self.table)
        self.tabs.addTab(year_tab, "Year Overview")

    def setup_month_tab(self, month_index):
        # Create a widget for the month
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # --- LEFT: Income Section ---
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0,0,0,0)
        
        left_layout.addWidget(QLabel(f"{self.month_names[month_index]} Paychecks", objectName="HeaderTitle", styleSheet="color:#374151; font-size: 16px;"))
        
        # Monthly Income Table
        inc_table = QTableWidget()
        inc_table.setColumnCount(3)
        inc_table.setHorizontalHeaderLabels(["Date", "Gross", "Net Pay"])
        inc_table.verticalHeader().setVisible(False)
        inc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        inc_table.setAlternatingRowColors(True)
        inc_table.setFixedHeight(150) 
        left_layout.addWidget(inc_table)

        # Summary Box
        summary_frame = QFrame()
        summary_frame.setObjectName("MonthSummaryBox")
        sum_layout = QGridLayout(summary_frame)
        sum_layout.setVerticalSpacing(15) 
        
        lbl_inc_val = QLabel("$0.00", objectName="MoneyLabel", styleSheet="color: #059669; font-size: 18px;")
        lbl_exp_val = QLabel("$0.00", objectName="MoneyLabel", styleSheet="color: #DC2626; font-size: 18px;")
        lbl_rem_val = QLabel("$0.00", objectName="MoneyLabel", styleSheet="color: #2563EB; font-size: 22px;")
        
        sum_layout.addWidget(QLabel("Total Income:"), 0, 0)
        sum_layout.addWidget(lbl_inc_val, 0, 1, alignment=Qt.AlignRight)
        
        sum_layout.addWidget(QLabel("Total Outflow:"), 1, 0)
        sum_layout.addWidget(lbl_exp_val, 1, 1, alignment=Qt.AlignRight)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #CBD5E1;")
        sum_layout.addWidget(line, 2, 0, 1, 2)
        
        sum_layout.addWidget(QLabel("Net Remaining:", styleSheet="font-weight:bold; font-size:16px;"), 3, 0)
        sum_layout.addWidget(lbl_rem_val, 3, 1, alignment=Qt.AlignRight)

        left_layout.addWidget(summary_frame)
        left_layout.addStretch()

        # --- RIGHT: Expenses Breakdown ---
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0,0,0,0)
        
        right_layout.addWidget(QLabel("Expense Breakdown", objectName="HeaderTitle", styleSheet="color:#374151; font-size: 16px;"))
        
        exp_scroll = QScrollArea()
        exp_scroll.setWidgetResizable(True)
        exp_scroll.setFrameShape(QFrame.NoFrame)
        exp_container = QWidget()
        exp_container.setStyleSheet("background-color: #FFFFFF;")
        
        # CHANGED: Use QGridLayout to guarantee 2-column alignment (Label | Value)
        # This fixes the "Value on Left" issue by forcing values into Column 1 (Right)
        exp_list_layout = QGridLayout(exp_container)
        exp_list_layout.setAlignment(Qt.AlignTop)
        exp_list_layout.setSpacing(12)
        exp_list_layout.setColumnStretch(0, 1) # Name takes all space
        exp_list_layout.setColumnStretch(1, 0) # Value takes min space
        
        exp_scroll.setWidget(exp_container)
        
        right_layout.addWidget(exp_scroll)

        layout.addWidget(left_col, 1) # 50% width
        layout.addWidget(right_col, 1) # 50% width

        self.tabs.addTab(tab, self.month_names[month_index])

        # Store references to update later
        self.month_tabs_refs.append({
            'table': inc_table,
            'inc_lbl': lbl_inc_val,
            'exp_lbl': lbl_exp_val,
            'rem_lbl': lbl_rem_val,
            'exp_layout': exp_list_layout,
            'exp_container': exp_container
        })

    def create_stat_card(self, title, value, sub, color="#1F2937"):
        frame = QFrame()
        frame.setObjectName("StatCard")
        layout = QVBoxLayout(frame)
        l_title = QLabel(title)
        l_title.setObjectName("StatTitle")
        l_val = QLabel(value)
        l_val.setObjectName("StatValue")
        l_val.setStyleSheet(f"color: {color};")
        l_sub = QLabel(sub)
        l_sub.setObjectName("StatSub")
        layout.addWidget(l_title)
        layout.addWidget(l_val)
        layout.addWidget(l_sub)
        return frame

    def get_stat_label(self, card):
        for child in card.children():
            if child.objectName() == "StatValue": return child
        return None

    # --- Database Logic (Unchanged) ---
    def init_db(self):
        self.conn = sqlite3.connect(DB_FILE)
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (year INTEGER PRIMARY KEY, tax_rate REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER, name TEXT, amount REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS deductions (id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER, name TEXT, amount REAL, is_percent INTEGER, is_pre_tax INTEGER)''')
        self.conn.commit()

    def load_data(self):
        cursor = self.conn.cursor()
        
        # Load Settings
        cursor.execute("SELECT tax_rate FROM settings WHERE year = ?", (CURRENT_YEAR,))
        row = cursor.fetchone()
        if row: 
            self.tax_input.setText(str(row[0]))
        else:
            self.tax_input.setText("22.0")
            cursor.execute("INSERT INTO settings (year, tax_rate) VALUES (?, ?)", (CURRENT_YEAR, 22.0))
            self.conn.commit()
            
        # Load Deductions
        cursor.execute("SELECT id, name, amount, is_percent, is_pre_tax FROM deductions WHERE year = ?", (CURRENT_YEAR,))
        rows = cursor.fetchall()
        for r in rows: 
            self.add_deduction_row(r[0], r[1], r[2], bool(r[3]), bool(r[4]), save=False)
            
        # Load Expenses
        cursor.execute("SELECT id, name, amount FROM expenses WHERE year = ?", (CURRENT_YEAR,))
        rows = cursor.fetchall()
        
        if not rows:
            defaults = [("Rent", 0), ("Truck Payment", 0), ("Student Loans", 0), 
                        ("Utilities (Xcel)", 0), ("Cell Phone", 0), ("Groceries", 758)]
            for name, val in defaults: 
                self.add_expense_row(None, name, val, save=True)
        else:
            for r in rows: 
                self.add_expense_row(r[0], r[1], r[2], save=False)
                
        self.recalculate_budget()

    def update_tax_db(self):
        try: val = float(self.tax_input.text())
        except ValueError: val = 0.0
        cursor = self.conn.cursor()
        cursor.execute("UPDATE settings SET tax_rate = ? WHERE year = ?", (val, CURRENT_YEAR))
        self.conn.commit()
        self.recalculate_budget()

    def add_deduction_row(self, db_id=None, name="New Deduction", amount=0, is_percent=False, is_pre_tax=True, save=True):
        if save:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO deductions (year, name, amount, is_percent, is_pre_tax) VALUES (?, ?, ?, ?, ?)",
                           (CURRENT_YEAR, name, amount, 1 if is_percent else 0, 1 if is_pre_tax else 0))
            self.conn.commit()
            db_id = cursor.lastrowid
        row = DeductionRow(self, db_id, name, amount, is_percent, is_pre_tax)
        self.deductions_layout.addWidget(row)
        if save: self.recalculate_budget()

    def db_update_deduction(self, db_id, name, amount, is_percent, is_pre_tax):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE deductions SET name=?, amount=?, is_percent=?, is_pre_tax=? WHERE id=?",
                       (name, amount, 1 if is_percent else 0, 1 if is_pre_tax else 0, db_id))
        self.conn.commit()

    def db_delete_deduction(self, db_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM deductions WHERE id=?", (db_id,))
        self.conn.commit()

    def add_expense_row(self, db_id=None, name="New Expense", amount=0, save=True):
        if save:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO expenses (year, name, amount) VALUES (?, ?, ?)", (CURRENT_YEAR, name, amount))
            self.conn.commit()
            db_id = cursor.lastrowid
        row = ExpenseRow(self, db_id, name, amount)
        self.expenses_layout.addWidget(row)
        if save: self.recalculate_budget()

    def db_update_expense(self, db_id, name, amount):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE expenses SET name=?, amount=? WHERE id=?", (name, amount, db_id))
        self.conn.commit()

    def db_delete_expense(self, db_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id=?", (db_id,))
        self.conn.commit()

    def get_working_days(self, start_date, end_date):
        count = 0
        curr = start_date
        while curr <= end_date:
            if curr.weekday() < 5: count += 1
            curr += datetime.timedelta(days=1)
        return count

    def calculate_pay_schedule(self):
        self.pay_schedule = []
        year = CURRENT_YEAR
        for month in range(12):
            pay_date = datetime.date(year, month + 1, 7)
            if month == 0:
                p_start = datetime.date(year-1, 12, 16); p_end = datetime.date(year-1, 12, 31); rate = 44.00
            else:
                p_start = datetime.date(year, month, 16); last_day = calendar.monthrange(year, month)[1]; p_end = datetime.date(year, month, last_day); rate = 45.78
            hours = self.get_working_days(p_start, p_end) * 8
            self.pay_schedule.append({'date': pay_date, 'period': f"{p_start.strftime('%b %d')} - {p_end.strftime('%b %d')}", 'hours': hours, 'rate': rate})
            
            pay_date = datetime.date(year, month + 1, 22)
            p_start = datetime.date(year, month + 1, 1); p_end = datetime.date(year, month + 1, 15)
            hours = self.get_working_days(p_start, p_end) * 8
            self.pay_schedule.append({'date': pay_date, 'period': f"{p_start.strftime('%b %d')} - {p_end.strftime('%b %d')}", 'hours': hours, 'rate': 45.78})

    def recalculate_budget(self):
        # 1. Gather Data
        expenses_data = [self.expenses_layout.itemAt(i).widget().get_values() 
                         for i in range(self.expenses_layout.count())]
        total_monthly_expenses = sum(e['amount'] for e in expenses_data)
        
        deductions_data = [self.deductions_layout.itemAt(i).widget().get_values() 
                           for i in range(self.deductions_layout.count())]
        
        try: tax_rate = float(self.tax_input.text())
        except ValueError: tax_rate = 0.0

        self.total_exp_label.setText(f"Total Monthly: ${total_monthly_expenses:,.2f}")

        # 2. Year Overview Logic
        total_gross = 0
        total_net = 0
        self.table.setRowCount(0)

        # We will also group checks by month for the monthly tabs
        checks_by_month = {i: [] for i in range(12)} # 0=Jan, 11=Dec

        for i, check in enumerate(self.pay_schedule):
            gross = check['hours'] * check['rate']
            
            pre_tax_ded = 0
            post_tax_ded = 0
            
            for d in deductions_data:
                amt = (gross * d['value'] / 100.0) if d['is_percent'] else d['value']
                if d['is_pre_tax']: pre_tax_ded += amt
                else: post_tax_ded += amt
            
            taxable = max(0, gross - pre_tax_ded)
            taxes = taxable * (tax_rate / 100.0)
            net = gross - pre_tax_ded - taxes - post_tax_ded
            remaining = net - (total_monthly_expenses / 2)
            
            total_gross += gross
            total_net += net

            # Add to Year Overview Table
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            is_alt = (row_idx % 2 != 0)
            base_text_color = "#F1F5F9" if is_alt else "#374151"
            
            self.set_table_item(row_idx, 0, check['date'].strftime('%b %d'), color=base_text_color)
            self.set_table_item(row_idx, 1, check['period'], color=base_text_color)
            
            item_hours = QTableWidgetItem(str(check['hours']))
            item_hours.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if check['hours'] == 96:
                item_hours.setForeground(QColor("#34D399" if is_alt else "#059669"))
                item_hours.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:
                item_hours.setForeground(QColor(base_text_color))
            self.table.setItem(row_idx, 2, item_hours)
            
            self.set_table_item(row_idx, 3, f"${check['rate']:.2f}", align_right=True, color=base_text_color)
            self.set_table_item(row_idx, 4, f"${gross:,.2f}", align_right=True, color=base_text_color)
            net_color = "#34D399" if is_alt else "#059669"
            self.set_table_item(row_idx, 5, f"${net:,.2f}", align_right=True, color=net_color)
            
            item_rem = QTableWidgetItem(f"${remaining:,.2f}")
            item_rem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rem_color = ("#60A5FA" if is_alt else "#2563EB") if remaining > 0 else ("#F87171" if is_alt else "#DC2626")
            item_rem.setForeground(QColor(rem_color))
            item_rem.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row_idx, 6, item_rem)

            # Store for Monthly Tabs (Month is 1-based in date, 0-based in list)
            m_idx = check['date'].month - 1
            checks_by_month[m_idx].append({
                'date': check['date'],
                'gross': gross,
                'net': net,
                'deductions': pre_tax_ded + taxes + post_tax_ded, # Total withheld
                'check_ded_breakdown': (pre_tax_ded + post_tax_ded) # Just the user deductions, not tax
            })

        # Update Year Cards
        self.get_stat_label(self.card_gross).setText(f"${total_gross:,.2f}")
        self.get_stat_label(self.card_net).setText(f"${total_net:,.2f}")
        annual_savings = total_net - (total_monthly_expenses * 12)
        self.get_stat_label(self.card_savings).setText(f"${annual_savings:,.2f}")

        # 3. Monthly Tabs Logic
        for m_idx in range(12):
            refs = self.month_tabs_refs[m_idx]
            checks = checks_by_month[m_idx]
            
            # Sums
            m_gross = sum(c['gross'] for c in checks)
            m_net = sum(c['net'] for c in checks)
            m_deductions = sum(c['deductions'] for c in checks) # Includes Tax
            m_user_deductions = sum(c['check_ded_breakdown'] for c in checks) # Just user defined
            
            total_net_income = m_net
            total_outflow = total_monthly_expenses
            net_remaining = total_net_income - total_outflow
            
            # Update Summary Labels
            refs['inc_lbl'].setText(f"${total_net_income:,.2f}")
            refs['exp_lbl'].setText(f"${total_outflow:,.2f}")
            refs['rem_lbl'].setText(f"${net_remaining:,.2f}")
            color = "#2563EB" if net_remaining > 0 else "#DC2626"
            refs['rem_lbl'].setStyleSheet(f"color: {color}; font-size: 22px;")

            # Update Income Table
            t = refs['table']
            t.setRowCount(0)
            for c in checks:
                row = t.rowCount()
                t.insertRow(row)
                
                # Logic for colors (Same as main table)
                is_alt = (row % 2 != 0)
                base_color = "#F1F5F9" if is_alt else "#374151"
                
                # Date
                item_date = QTableWidgetItem(c['date'].strftime('%b %d'))
                item_date.setForeground(QColor(base_color))
                t.setItem(row, 0, item_date)
                
                # Gross
                item_gross = QTableWidgetItem(f"${c['gross']:,.2f}")
                item_gross.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_gross.setForeground(QColor(base_color))
                t.setItem(row, 1, item_gross)
                
                # Net
                item_net = QTableWidgetItem(f"${c['net']:,.2f}")
                item_net.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                net_color = "#34D399" if is_alt else "#059669"
                item_net.setForeground(QColor(net_color))
                item_net.setFont(QFont("Segoe UI", 9, QFont.Bold))
                t.setItem(row, 2, item_net)

            # Update Expenses List (Clear and Rebuild)
            layout = refs['exp_layout']
            # Clear existing items from GridLayout
            while layout.count():
                child = layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            # Add Fixed Expenses
            row_idx = 0
            for exp in expenses_data:
                self.add_line_to_grid(layout, row_idx, exp['name'], exp['amount'])
                row_idx += 1

            # Add Divider (Spanning 2 cols)
            # Since QGridLayout handles widgets, we need a widget that spans
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("color: #E2E8F0;")
            layout.addWidget(line, row_idx, 0, 1, 2)
            row_idx += 1
            
            # Spacer (Empty Row)
            layout.setRowMinimumHeight(row_idx, 30)
            row_idx += 1

            # Add Payroll Deductions Summary Label (Spanning 2 cols)
            lbl = QLabel("Payroll Deductions (Already subtracted from Net)")
            lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
            layout.addWidget(lbl, row_idx, 0, 1, 2)
            row_idx += 1
            
            self.add_line_to_grid(layout, row_idx, "Taxes & Withholding", m_deductions - m_user_deductions, color="#64748B")
            row_idx += 1
            self.add_line_to_grid(layout, row_idx, "Benefit Deductions", m_user_deductions, color="#64748B")
            row_idx += 1

    def add_line_to_grid(self, layout, row, name, amount, color="#374151"):
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(f"color: {color};")
        
        lbl_amt = QLabel(f"${amount:,.2f}")
        lbl_amt.setStyleSheet(f"font-weight: bold; color: {color};")
        
        layout.addWidget(lbl_name, row, 0)
        layout.addWidget(lbl_amt, row, 1, alignment=Qt.AlignRight)

    def set_table_item(self, row, col, text, align_right=False, color=None):
        item = QTableWidgetItem(text)
        if align_right: item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else: item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if color:
            item.setForeground(QColor(color))
            if color not in ["#374151", "#F1F5F9"]: item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.table.setItem(row, col, item)

    def copy_to_clipboard(self):
        # ... (Existing Logic) ...
        header = "Pay Date,Period,Hours,Rate,Gross,Net Pay,Est Half-Month Exp,Remaining\n"
        data = ""
        expenses_data = [self.expenses_layout.itemAt(i).widget().get_values() for i in range(self.expenses_layout.count())]
        total_monthly = sum(e['amount'] for e in expenses_data)
        deductions = [self.deductions_layout.itemAt(i).widget().get_values() for i in range(self.deductions_layout.count())]
        try: tax_rate = float(self.tax_input.text())
        except ValueError: tax_rate = 0.0
        for check in self.pay_schedule:
            gross = check['hours'] * check['rate']
            pre, post = 0, 0
            for d in deductions:
                amt = (gross * d['value'] / 100.0) if d['is_percent'] else d['value']
                if d['is_pre_tax']: pre += amt
                else: post += amt
            taxable = max(0, gross - pre)
            taxes = taxable * (tax_rate / 100.0)
            net = gross - pre - taxes - post
            rem = net - (total_monthly / 2)
            data += f"{check['date']},{check['period']},{check['hours']},{check['rate']},{gross:.2f},{net:.2f},{(total_monthly/2):.2f},{rem:.2f}\n"
        QGuiApplication.clipboard().setText(header + data)
        QMessageBox.information(self, "Copied", "Budget data copied to clipboard!")

    def get_stat_label(self, card):
        for child in card.children():
            if child.objectName() == "StatValue": return child
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)
    window = BudgetApp()
    window.show()
    sys.exit(app.exec())
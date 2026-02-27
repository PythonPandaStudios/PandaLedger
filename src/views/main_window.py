import calendar
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QScrollArea, QFrame, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QComboBox, QGridLayout, QTabWidget, 
                               QFormLayout, QTableView, QDockWidget, QDateEdit, QLineEdit)
from PySide6.QtCore import Qt, Signal, QDate

from views.theme_manager import THEMES
from views.components import LedgerTableView

class MainWindowView(QMainWindow):
    # --- MVC SIGNALS ---
    theme_changed_signal = Signal(str)
    open_payroll_settings_signal = Signal()
    export_clipboard_signal = Signal()
    manage_deductions_signal = Signal()
    manage_expenses_signal = Signal()
    
    payee_edited_signal = Signal(str)
    save_transaction_signal = Signal(dict)
    receipt_dropped_signal = Signal(int, str)
    ledger_double_clicked_signal = Signal(object) # Passes QModelIndex

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panda Ledger")
        self.resize(1350, 900)
        self.month_tabs_refs = []
        self.setup_ui()

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
        self.theme_combo.currentTextChanged.connect(self.theme_changed_signal.emit)

        payroll_btn = QPushButton("Payroll Settings")
        payroll_btn.clicked.connect(self.open_payroll_settings_signal.emit)

        copy_btn = QPushButton("Copy for Excel", objectName="CopyButton")
        copy_btn.clicked.connect(self.export_clipboard_signal.emit)

        h_layout.addLayout(title_box)
        h_layout.addStretch()
        h_layout.addWidget(QLabel("Theme:"))
        h_layout.addWidget(self.theme_combo)
        h_layout.addWidget(payroll_btn)
        h_layout.addWidget(copy_btn)
        main_layout.addWidget(header)

        content = QHBoxLayout()
        
        self.tabs = QTabWidget()
        self.setup_year_tab()
        
        self.month_names = list(calendar.month_name)[1:]
        for i in range(12): 
            self.setup_month_tab(i)
        
        content.addWidget(self.tabs)
        main_layout.addLayout(content)
        
        self.setup_transaction_dock()

    def setup_transaction_dock(self):
        self.add_tx_dock = QDockWidget("Add Transaction", self)
        self.add_tx_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        dock_widget = QWidget()
        dock_layout = QFormLayout(dock_widget)
        
        self.tx_date = QDateEdit()
        self.tx_date.setCalendarPopup(True)
        self.tx_date.setDate(QDate.currentDate())
        
        self.tx_payee = QLineEdit()
        self.tx_payee.textEdited.connect(self.payee_edited_signal.emit)
        
        self.tx_amount = QLineEdit()
        
        self.tx_category = QComboBox()
        self.tx_account = QComboBox()
        
        self.tx_notes = QLineEdit()
        
        self.tx_save_btn = QPushButton("Save Transaction")
        self.tx_save_btn.clicked.connect(self.emit_save_transaction)
        
        dock_layout.addRow("Date:", self.tx_date)
        dock_layout.addRow("Payee:", self.tx_payee)
        dock_layout.addRow("Amount:", self.tx_amount)
        dock_layout.addRow("Category:", self.tx_category)
        dock_layout.addRow("Account:", self.tx_account)
        dock_layout.addRow("Notes:", self.tx_notes)
        dock_layout.addRow(self.tx_save_btn)
        
        self.add_tx_dock.setWidget(dock_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.add_tx_dock)

    def emit_save_transaction(self):
        data = {
            'date': self.tx_date.date().toPython(),
            'payee': self.tx_payee.text(),
            'amount': self.tx_amount.text(),
            'category_id': self.tx_category.currentData(),
            'account_id': self.tx_account.currentData(),
            'notes': self.tx_notes.text()
        }
        self.save_transaction_signal.emit(data)

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
        
        self.year_table = QTableWidget(0, 6)
        self.year_table.setHorizontalHeaderLabels(["Date", "Hrs", "Rate", "Gross", "Net", "Remaining"])
        self.year_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.year_table)
        self.tabs.addTab(tab, "Year Overview")

    def setup_month_tab(self, m_idx):
        tab = QWidget()
        main_layout = QVBoxLayout(tab) 

        ledger_label = QLabel(f"{self.month_names[m_idx]} Ledger", objectName="SectionTitle")
        main_layout.addWidget(ledger_label)

        # Replacing QTableView with our custom LedgerTableView that accepts drag and drops
        ledger_view = LedgerTableView()
        ledger_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        ledger_view.verticalHeader().setVisible(False)
        ledger_view.setAlternatingRowColors(True)
        
        # Connect internal ledger view signals out to the controller
        ledger_view.receipt_dropped.connect(self.receipt_dropped_signal.emit)
        ledger_view.doubleClicked.connect(self.ledger_double_clicked_signal.emit)
        
        main_layout.addWidget(ledger_view, 1)

        bottom_layout = QHBoxLayout()
        btn_layout = QHBoxLayout()
        btn_manage_ded = QPushButton("Manage Deductions")
        btn_manage_ded.clicked.connect(self.manage_deductions_signal.emit)
        btn_manage_exp = QPushButton("Manage Expenses")
        btn_manage_exp.clicked.connect(self.manage_expenses_signal.emit)
        
        btn_layout.addWidget(btn_manage_ded)
        btn_layout.addWidget(btn_manage_exp)
        
        summary = QFrame(objectName="MonthSummaryBox")
        s_grid = QFormLayout(summary)
        l_inc, l_exp, l_rem = QLabel("$0.00"), QLabel("$0.00"), QLabel("$0.00")
        s_grid.addRow("Net Income:", l_inc)
        s_grid.addRow("Expenses:", l_exp)
        s_grid.addRow("Remaining:", l_rem)

        bottom_layout.addLayout(btn_layout)
        bottom_layout.addStretch()
        bottom_layout.addWidget(summary)

        main_layout.addLayout(bottom_layout)

        self.tabs.addTab(tab, self.month_names[m_idx])
        
        self.month_tabs_refs.append({
            'inc': l_inc, 'exp': l_exp, 'rem': l_rem, 'ledger': ledger_view
        })

    def create_stat_card(self, title, val, sub):
        f = QFrame(objectName="StatCard")
        l = QVBoxLayout(f)
        l.addWidget(QLabel(title, objectName="StatTitle"))
        v = QLabel(val, objectName="StatValue")
        l.addWidget(v)
        l.addWidget(QLabel(sub, objectName="StatSub"))
        return f
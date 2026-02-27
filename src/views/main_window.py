import calendar
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QScrollArea, QFrame, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QComboBox, QGridLayout, QTabWidget, 
                               QFormLayout, QTableView)
from PySide6.QtCore import Qt, Signal

from views.theme_manager import THEMES
from views.components import LedgerTableView

class MainWindowView(QMainWindow):
    theme_changed_signal = Signal(str)
    open_payroll_settings_signal = Signal()
    export_clipboard_signal = Signal()
    manage_deductions_signal = Signal()
    
    add_transaction_signal = Signal()
    delete_row_signal = Signal(dict) # --- NEW SIGNAL ---
    
    receipt_dropped_signal = Signal(int, str)
    ledger_double_clicked_signal = Signal(object) 

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

        ledger_view = LedgerTableView()
        ledger_view.verticalHeader().setVisible(False)
        ledger_view.setAlternatingRowColors(True)
        
        ledger_view.receipt_dropped.connect(self.receipt_dropped_signal.emit)
        ledger_view.doubleClicked.connect(self.ledger_double_clicked_signal.emit)
        
        # Connect delete signal
        ledger_view.delete_requested.connect(self.delete_row_signal.emit)
        
        main_layout.addWidget(ledger_view, 1)

        bottom_layout = QHBoxLayout()
        btn_layout = QHBoxLayout()
        btn_manage_ded = QPushButton("Manage Deductions")
        btn_manage_ded.clicked.connect(self.manage_deductions_signal.emit)
        
        btn_add_tx = QPushButton("Add Transaction")
        btn_add_tx.clicked.connect(self.add_transaction_signal.emit)
        
        btn_layout.addWidget(btn_manage_ded)
        btn_layout.addWidget(btn_add_tx)
        
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
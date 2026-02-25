import calendar
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QScrollArea, QFrame, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QComboBox, QGridLayout, QTabWidget, 
                               QFormLayout, QTableView)
from PySide6.QtCore import Qt, Signal

from views.theme_manager import THEMES

class MainWindowView(QMainWindow):
    # --- MVC SIGNALS ---
    # The Controller will listen to these and perform the actual work
    theme_changed_signal = Signal(str)
    open_payroll_settings_signal = Signal()
    add_deduction_signal = Signal()
    add_expense_signal = Signal()
    export_clipboard_signal = Signal()

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
        # EMIT signal instead of processing logic
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

        # Content Layout
        content = QHBoxLayout()
        
        # Sidebar
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
        btn_add_ded.clicked.connect(self.add_deduction_signal.emit)
        s_layout.addWidget(btn_add_ded)

        s_layout.addWidget(QLabel("MONTHLY EXPENSES", objectName="SectionTitle"))
        self.exp_area = QScrollArea(widgetResizable=True)
        self.exp_cont = QWidget()
        self.exp_layout = QVBoxLayout(self.exp_cont)
        self.exp_layout.setAlignment(Qt.AlignTop)
        self.exp_area.setWidget(self.exp_cont)
        s_layout.addWidget(self.exp_area)

        btn_add_exp = QPushButton("+ Add Expense")
        btn_add_exp.clicked.connect(self.add_expense_signal.emit)
        s_layout.addWidget(btn_add_exp)

        self.lbl_total_exp = QLabel("Total: $0.00")
        s_layout.addWidget(self.lbl_total_exp)
        content.addWidget(sidebar)

        # Tabs
        self.tabs = QTabWidget()
        self.setup_year_tab()
        self.setup_ledger_tab()
        
        self.month_names = list(calendar.month_name)[1:]
        for i in range(12): 
            self.setup_month_tab(i)
        
        content.addWidget(self.tabs)
        main_layout.addLayout(content)

    def setup_ledger_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.ledger_view = QTableView()
        self.ledger_view.setSortingEnabled(True)
        self.ledger_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ledger_view.verticalHeader().setVisible(False)
        self.ledger_view.setAlternatingRowColors(True)
        
        layout.addWidget(self.ledger_view)
        self.tabs.insertTab(0, tab, "Ledger")
        self.tabs.setCurrentIndex(0)

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
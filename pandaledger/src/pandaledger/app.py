import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import calendar
import datetime

# Import our UI-agnostic service layer
from pandaledger.logic.transaction_service import TransactionService

class PandaLedger(toga.App):
    def startup(self):
        """
        Main application boot sequence. Replaces PySide6 MainWindowView.
        """
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # 1. Toga's native Tab Widget
        self.tabs = toga.OptionContainer()
        
        # 2. Setup Year Overview Tab
        self.setup_year_tab()
        
        # 3. Setup 12 Monthly Tabs
        self.month_names = list(calendar.month_name)[1:]
        self.month_tables = [] # Keep references to update data later
        
        for idx, month in enumerate(self.month_names):
            self.setup_month_tab(idx, month)
            
        # Assign tabs to the main window
        self.main_window.content = self.tabs
        self.main_window.show()

    def setup_year_tab(self):
        """Replaces MainWindowView.setup_year_tab()"""
        # FIX: 'padding' is now 'margin'
        year_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        # FIX: 'padding_bottom' is now 'margin_bottom'
        stats_box = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        self.lbl_gross = toga.Label("Gross: $0.00", style=Pack(flex=1, font_weight='bold'))
        self.lbl_net = toga.Label("Net: $0.00", style=Pack(flex=1, font_weight='bold'))
        self.lbl_sav = toga.Label("Savings: $0.00", style=Pack(flex=1, font_weight='bold'))
        stats_box.add(self.lbl_gross, self.lbl_net, self.lbl_sav)
        
        # FIX: 'headings' is now 'columns'
        self.year_table = toga.Table(
            columns=["Date", "Hrs", "Rate", "Gross", "Net", "Remaining"],
            style=Pack(flex=1) 
        )
        
        year_box.add(stats_box)
        year_box.add(self.year_table)
        
        # FIX: Append directly to OptionContainer.content
        self.tabs.content.append("Year Overview", year_box)

    def setup_month_tab(self, m_idx, month_name):
        """Replaces MainWindowView.setup_month_tab()"""
        month_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        # Section Title
        ledger_label = toga.Label(f"{month_name} Ledger", style=Pack(margin_bottom=5, font_size=16))
        month_box.add(ledger_label)
        
        # Replaces QTableView (LedgerTableView)
        ledger_table = toga.Table(
            columns=["Date", "Payee", "Category", "Amount", "Notes"],
            style=Pack(flex=1)
        )
        self.month_tables.append(ledger_table)
        month_box.add(ledger_table)
        
        # Bottom Summary & Action Area
        bottom_box = toga.Box(style=Pack(direction=ROW, margin_top=10))
        
        # Buttons
        btn_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        btn_add_tx = toga.Button("Add Transaction", on_press=self.show_add_tx_form, style=Pack(margin_bottom=5))
        btn_box.add(btn_add_tx)
        
        # Summary
        summary_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        summary_box.add(toga.Label("Net Income: $0.00"))
        summary_box.add(toga.Label("Expenses: $0.00"))
        summary_box.add(toga.Label("Remaining: $0.00"))
        
        bottom_box.add(btn_box)
        bottom_box.add(summary_box)
        
        month_box.add(bottom_box)
        
        # FIX: Append directly to OptionContainer.content
        self.tabs.content.append(month_name, month_box)

    def show_add_tx_form(self, widget):
        """
        Temporary hook: In Toga, to mimic a QDialog without complex window management, 
        we can push a new view or open a secondary window.
        """
        self.main_window.info_dialog(
            "Transaction Entry", 
            "The Native Transaction form (from Issue #3) will overlay here."
        )

def main():
    return PandaLedger()
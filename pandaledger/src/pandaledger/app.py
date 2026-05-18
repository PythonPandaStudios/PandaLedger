import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import calendar

# Import our Brain (Pure Python Controller)
from pandaledger.logic.main_controller import MainController

class PandaLedger(toga.App):
    def startup(self):
        """Main application boot sequence. Relies on OS Native Theming."""
        # --- Initialize the Brain ---
        self.controller = MainController()
        
        self.main_window = toga.MainWindow(title=self.formal_name, size=(1200, 800))
        
        # --- 1. Global Header ---
        header_box = toga.Box(style=Pack(direction=ROW, margin=15, align_items=CENTER))
        
        title_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        title_label = toga.Label("PandaLedger", style=Pack(font_size=20, font_weight='bold'))
        self.subtitle_label = toga.Label("Semi-Monthly | Colorado Tax Rules", style=Pack(font_size=12, color="gray"))
        
        title_box.add(title_label, self.subtitle_label)
        
        # Payroll Settings Button
        payroll_btn = toga.Button("Payroll Settings", on_press=self.show_payroll_settings, style=Pack(width=150))
        
        header_box.add(title_box, payroll_btn)
        
        # --- 2. Main Navigation (Tabs) ---
        self.tabs = toga.OptionContainer(style=Pack(flex=1))
        
        self.setup_year_tab()
        
        self.month_names = list(calendar.month_name)[1:]
        self.month_tables = [] 
        
        for idx, month in enumerate(self.month_names):
            self.setup_month_tab(idx, month)
            
        # --- 3. Root Layout ---
        self.root_box = toga.Box(style=Pack(direction=COLUMN))
        self.root_box.add(header_box)
        self.root_box.add(self.tabs)
        
        self.main_window.content = self.root_box
        self.main_window.show()
        
        # Pull fresh data from SQLite DB / Controller to populate the UI
        self.refresh_ui()

    def create_stat_card(self, title, default_val, subtitle):
        """
        Creates a centered, transparent structural box for stats.
        Visual separation will be handled by external dividers.
        """
        card = toga.Box(style=Pack(direction=COLUMN, flex=1, align_items=CENTER, margin=5))
        
        lbl_title = toga.Label(title, style=Pack(font_size=10, font_weight='bold', margin_bottom=5, color="gray"))
        lbl_val = toga.Label(default_val, style=Pack(font_size=18, font_weight='bold'))
        lbl_sub = toga.Label(subtitle, style=Pack(font_size=10, margin_top=5, color="gray"))
        
        card.add(lbl_title, lbl_val, lbl_sub)
        return card, lbl_val

    def setup_year_tab(self):
        year_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        stats_box = toga.Box(style=Pack(direction=ROW, align_items=CENTER, margin_bottom=10, margin_top=10))
        
        card_gross, self.lbl_gross = self.create_stat_card("EST. ANNUAL GROSS", "$0.00", "Annual Total")
        card_net, self.lbl_net = self.create_stat_card("EST. ANNUAL NET", "$0.00", "Take Home")
        card_sav, self.lbl_sav = self.create_stat_card("EST. ANNUAL SAVINGS", "$0.00", "After Expenses")
        
        # A 1-pixel wide, 60-pixel high box that acts as a structural line. 
        div1 = toga.Box(style=Pack(width=1, height=60, background_color="gray", margin_left=15, margin_right=15))
        div2 = toga.Box(style=Pack(width=1, height=60, background_color="gray", margin_left=15, margin_right=15))
        
        stats_box.add(card_gross, div1, card_net, div2, card_sav)
        
        # Setup the Table
        self.year_table = toga.Table(columns=["Date", "Hrs", "Rate", "Gross", "Net", "Remaining"], style=Pack(flex=1))
        
        # Native Horizontal Dividers
        table_div = toga.Divider(direction=toga.Divider.HORIZONTAL, style=Pack(margin_bottom=10))
        
        year_box.add(stats_box, table_div, self.year_table)
        self.tabs.content.append("Year Overview", year_box)

    def setup_month_tab(self, m_idx, month_name):
        month_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        ledger_label = toga.Label(f"{month_name} Ledger", style=Pack(margin_bottom=5, font_size=16, font_weight='bold'))
        month_box.add(ledger_label)
        
        ledger_table = toga.Table(columns=["Date", "Payee", "Category", "Amount", "Notes"], style=Pack(flex=1))
        self.month_tables.append(ledger_table)
        month_box.add(ledger_table)
        
        bottom_box = toga.Box(style=Pack(direction=ROW, margin_top=10))
        btn_box = toga.Box(style=Pack(direction=ROW, flex=1))
        
        btn_manage_ded = toga.Button("Manage Deductions", style=Pack(margin_right=10))
        
        # Temporary test hook for the Add Transaction button
        def inject_test_tx(widget):
            from pandaledger.logic.transaction_service import TransactionService
            import datetime
            
            # Insert real data into SQLite
            TransactionService.create(
                tx_date=datetime.date.today(), 
                payee="Test Sync Groceries", 
                amount=-150.00
            )
            # Force the UI to pull the new data
            self.refresh_ui()

        btn_add_tx = toga.Button("Add Transaction", on_press=inject_test_tx)
        btn_box.add(btn_manage_ded, btn_add_tx)
        
        summary_box = toga.Box(style=Pack(direction=COLUMN))
        self.lbl_inc = toga.Label("Net Income: $0.00", style=Pack(text_align='right'))
        self.lbl_exp = toga.Label("Expenses: $0.00", style=Pack(text_align='right'))
        self.lbl_rem = toga.Label("Remaining: $0.00", style=Pack(text_align='right', font_weight='bold'))
        
        summary_box.add(self.lbl_inc, self.lbl_exp, self.lbl_rem)
        bottom_box.add(btn_box, summary_box)
        month_box.add(bottom_box)
        self.tabs.content.append(month_name, month_box)

    def show_payroll_settings(self, widget):
        self.settings_window = toga.Window(title="Payroll Settings", size=(400, 500))
        layout = toga.Box(style=Pack(direction=COLUMN, margin=20))
        
        lbl_header1 = toga.Label("Pay Schedule Settings", style=Pack(font_size=14, font_weight='bold', margin_bottom=10))
        layout.add(lbl_header1)
        
        row1 = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        lbl_sched = toga.Label("Schedule:", style=Pack(width=120))
        row1.add(lbl_sched, toga.Selection(items=["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly"], style=Pack(flex=1)))
        
        row2 = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        lbl_rate = toga.Label("Hourly Rate ($):", style=Pack(width=120))
        row2.add(lbl_rate, toga.NumberInput(step="0.01", value=45.78, style=Pack(flex=1)))
        
        layout.add(row1, row2)
        
        lbl_header2 = toga.Label("Tax Estimates (%)", style=Pack(font_size=14, font_weight='bold', margin_top=15, margin_bottom=10))
        layout.add(lbl_header2)
        
        row3 = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        lbl_fed = toga.Label("Federal Rate:", style=Pack(width=120))
        row3.add(lbl_fed, toga.NumberInput(step="0.1", value=12.0, style=Pack(flex=1)))

        row4 = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        lbl_state = toga.Label("State Rate:", style=Pack(width=120))
        row4.add(lbl_state, toga.NumberInput(step="0.1", value=4.4, style=Pack(flex=1)))
        
        layout.add(row3, row4)
        
        save_btn = toga.Button("Save Configuration", style=Pack(margin_top=20))
        save_btn.on_press = lambda x: self.settings_window.close() 
        layout.add(save_btn)
        
        self.settings_window.content = layout
        self.settings_window.show()

    def refresh_ui(self):
        """
        Pulls fresh data from the SQLite DB / Controller and repaints the UI tables.
        This replaces the old mock 'populate_default_data'.
        """
        # 1. Update Stat Cards
        stats = self.controller.get_annual_stats()
        self.lbl_gross.text = stats["gross"]
        self.lbl_net.text = stats["net"]
        self.lbl_sav.text = stats["savings"]
        
        # 2. Update Year Table
        self.year_table.data = self.controller.get_year_overview_table()
        
        # 3. Update Monthly Ledgers
        for idx, table in enumerate(self.month_tables):
            # Toga month tabs are 0-indexed (0=Feb, 11=Dec based on your calendar slice)
            # Real month number = idx + 2 (since index 0 is February)
            real_month_num = idx + 2 
            table.data = self.controller.get_month_transactions(real_month_num)

def main():
    return PandaLedger()
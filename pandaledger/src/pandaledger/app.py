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
        """Creates a centered, transparent structural box for stats."""
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
        
        div1 = toga.Box(style=Pack(width=1, height=60, background_color="gray", margin_left=15, margin_right=15))
        div2 = toga.Box(style=Pack(width=1, height=60, background_color="gray", margin_left=15, margin_right=15))
        
        stats_box.add(card_gross, div1, card_net, div2, card_sav)
        
        self.year_table = toga.Table(columns=["Date", "Hrs", "Rate", "Gross", "Net", "Remaining"], style=Pack(flex=1))
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
        
        def inject_test_tx(widget):
            from pandaledger.logic.transaction_service import TransactionService
            import datetime
            TransactionService.create(
                tx_date=datetime.date.today(), 
                payee="Test Sync Groceries", 
                amount=-150.00
            )
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
        current_settings = self.controller.get_payroll_settings()

        self.settings_window = toga.Window(title="Payroll Configuration", size=(450, 580))
        
        # --- Dynamic UI Inputs ---
        self.input_pay_type = toga.Selection(
            items=["Hourly", "Salary"], 
            on_change=self.on_settings_change,
            style=Pack(flex=1)
        )
        self.input_pay_type.value = current_settings["pay_type"]

        self.input_schedule = toga.Selection(
            items=["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly"], 
            on_change=self.on_settings_change,
            style=Pack(flex=1)
        )
        self.input_schedule.value = current_settings["schedule"]

        self.input_rate = toga.TextInput(value=str(current_settings["pay_rate"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_hours = toga.TextInput(value=str(current_settings["hours_per_period"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_tax = toga.TextInput(value=str(current_settings["tax_rate_percent"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_savings = toga.TextInput(value=str(current_settings["savings_rate_percent"]), on_change=self.on_settings_change, style=Pack(flex=1))

        # --- Output Labels for Real-Time UI ---
        self.lbl_yearly_gross = toga.Label("$0.00", style=Pack(font_weight='bold', text_align='right', flex=1))
        self.lbl_yearly_net = toga.Label("$0.00", style=Pack(font_weight='bold', color='green', text_align='right', flex=1))
        self.lbl_yearly_savings = toga.Label("$0.00", style=Pack(font_weight='bold', color='blue', text_align='right', flex=1))

        # --- View Assembly ---
        content = toga.Box(style=Pack(direction=COLUMN, margin=15))

        content.add(toga.Label("Pay Type:", style=Pack(margin_top=10)))
        content.add(self.input_pay_type)

        content.add(toga.Label("Pay Schedule:", style=Pack(margin_top=10)))
        content.add(self.input_schedule)

        row_rate = toga.Box(style=Pack(direction=ROW, margin_top=10))
        row_rate.add(toga.Label("Pay Rate / Salary ($):", style=Pack(width=180)))
        row_rate.add(self.input_rate)
        content.add(row_rate)

        # Critical: Defines the object BEFORE inputs can trigger layout updates
        self.hours_box = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.hours_box.add(toga.Label("Hours Per Period:", style=Pack(width=180)))
        self.hours_box.add(self.input_hours)
        content.add(self.hours_box)

        row_tax = toga.Box(style=Pack(direction=ROW, margin_top=10))
        row_tax.add(toga.Label("Estimated Net Tax %:", style=Pack(width=180)))
        row_tax.add(self.input_tax)
        content.add(row_tax)

        row_sav = toga.Box(style=Pack(direction=ROW, margin_top=10))
        row_sav.add(toga.Label("Target Savings %:", style=Pack(width=180)))
        row_sav.add(self.input_savings)
        content.add(row_sav)

        # Real-Time Estimates Panel
        estimates_box = toga.Box(style=Pack(direction=COLUMN, margin_top=25))
        estimates_box.add(toga.Label("--- Live Yearly Projections ---", style=Pack(margin_bottom=10, font_weight='bold')))

        row_gross = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        row_gross.add(toga.Label("Estimated Gross:", style=Pack(width=150)))
        row_gross.add(self.lbl_yearly_gross)
        estimates_box.add(row_gross)

        row_net = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        row_net.add(toga.Label("Estimated Net:", style=Pack(width=150)))
        row_net.add(self.lbl_yearly_net)
        estimates_box.add(row_net)

        row_save = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        row_save.add(toga.Label("Estimated Savings:", style=Pack(width=150)))
        row_save.add(self.lbl_yearly_savings)
        estimates_box.add(row_save)

        content.add(estimates_box)

        save_btn = toga.Button("Secure & Save Config", on_press=self.handle_save_settings, style=Pack(margin_top=25))
        content.add(save_btn)

        self.settings_window.content = toga.ScrollContainer(content=content)
        
        # Trigger initial mathematical map safely
        self.on_settings_change(None)
        self.settings_window.show()

    def on_settings_change(self, widget):
        """Background worker that recalculates the math on keystrokes/selection."""
        # Initial guard condition - prevents Toga 'on_change' initialization crashes
        if not hasattr(self, 'hours_box'):
            return

        try:
            # Dynamic Layout Toggle
            if self.input_pay_type.value == "Salary":
                self.hours_box.style.visibility = 'hidden'
            else:
                self.hours_box.style.visibility = 'visible'

            # Build a transient state map
            temp_settings = {
                'pay_type': self.input_pay_type.value,
                'schedule': self.input_schedule.value,
                'pay_rate': float(self.input_rate.value or 0),
                'hours_per_period': float(self.input_hours.value or 0),
                'tax_rate_percent': float(self.input_tax.value or 0),
                'savings_rate_percent': float(self.input_savings.value or 0)
            }

            estimates = self.controller.calculate_estimates(temp_settings)
            
            self.lbl_yearly_gross.text = f"${estimates['yearly_gross']:,.2f}"
            self.lbl_yearly_net.text = f"${estimates['yearly_net']:,.2f}"
            self.lbl_yearly_savings.text = f"${estimates['yearly_savings']:,.2f}"

        except ValueError:
            self.lbl_yearly_gross.text = "..."
            self.lbl_yearly_net.text = "..."
            self.lbl_yearly_savings.text = "..."

    def handle_save_settings(self, widget):
        """Commits the verified Toga data dict to the Controller."""
        try:
            data = {
                'pay_type': self.input_pay_type.value,
                'schedule': self.input_schedule.value,
                'pay_rate': float(self.input_rate.value),
                'hours_per_period': float(self.input_hours.value),
                'tax_rate_percent': float(self.input_tax.value),
                'savings_rate_percent': float(self.input_savings.value)
            }
            
            success = self.controller.save_payroll_settings(data)

            if success:
                self.subtitle_label.text = f"{data['schedule']} | Tax: {data['tax_rate_percent']}%"
                self.settings_window.close()
                self.refresh_ui()
                self.main_window.dialog(toga.InfoDialog("Success", "Settings secured to SQLite."))
            else:
                self.main_window.dialog(toga.ErrorDialog("Database Error", "Failed to secure settings to SQLite."))

        except ValueError:
            self.main_window.dialog(toga.ErrorDialog("Validation Error", "Check that numeric fields contain valid numbers."))

    def refresh_ui(self):
        """Pulls fresh database aggregations to paint the UI Tabs."""
        stats = self.controller.get_annual_stats()
        self.lbl_gross.text = stats["gross"]
        self.lbl_net.text = stats["net"]
        self.lbl_sav.text = stats["savings"]
        
        self.year_table.data = self.controller.get_year_overview_table()
        
        for idx, table in enumerate(self.month_tables):
            real_month_num = idx + 2 
            table.data = self.controller.get_month_transactions(real_month_num)

def main():
    return PandaLedger()
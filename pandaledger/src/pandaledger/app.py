import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import calendar

from pandaledger.logic.main_controller import MainController

class PandaLedger(toga.App):
    def startup(self):
        self.controller = MainController()
        self.main_window = toga.MainWindow(title=self.formal_name, size=(1200, 800))
        
        # --- 1. Global Header ---
        header_box = toga.Box(style=Pack(direction=ROW, margin=15, align_items=CENTER))
        title_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        title_label = toga.Label("Panda Ledger", style=Pack(font_size=20, font_weight='bold'))
        self.subtitle_label = toga.Label("Secure Local Ledger Engine", style=Pack(font_size=12, color="gray"))
        title_box.add(title_label, self.subtitle_label)
        header_box.add(title_box)

        # --- 2. Menu Bar Commands ---
        # Grouped under toga.Group.APP to force placement under the "Panda Ledger" OS Menu
        settings_cmd = toga.Command(
            self.show_payroll_settings,
            text="Payroll Settings",
            shortcut=toga.Key.MOD_1 + "S",
            group=toga.Group.SETTINGS
        )

        # File Menu (Standard OS Drop-down)
        export_cmd = toga.Command(
            self.mock_action,
            text="Export Ledger to CSV...",
            shortcut=toga.Key.MOD_1 + "E",
            group=toga.Group.FILE
        )
        import_cmd = toga.Command(
            self.mock_action, 
            text="Import Transactions...",
            group=toga.Group.FILE,
            section=2
        )

        # Custom Menu: "Reports"
        reports_group = toga.Group("Reports", order=30)
        tax_report_cmd = toga.Command(
            self.mock_action,
            text="Generate Tax Summary",
            shortcut=toga.Key.MOD_1 + "T",
            group=reports_group
        )
        
        # Help Menu (Standard OS Drop-down)
        help_cmd = toga.Command(
            self.show_help_dialog,
            text="Panda Ledger Documentation",
            shortcut=toga.Key.MOD_1 + "?",
            group=toga.Group.HELP
        )
        about_cmd = toga.Command(
            self.mock_action,
            text="About Panda Ledger",
            group=toga.Group.HELP,
            section=2
        )

        self.commands.add(
            settings_cmd, 
            export_cmd, import_cmd, 
            tax_report_cmd, 
            help_cmd, about_cmd
        )

        # --- 3. Main Navigation (Tabs) ---
        self.tabs = toga.OptionContainer(style=Pack(flex=1))
        self.setup_year_tab()
        
        self.month_names = list(calendar.month_name)[1:]
        self.month_tables = [] 
        for idx, month in enumerate(self.month_names):
            self.setup_month_tab(idx, month)
            
        self.root_box = toga.Box(style=Pack(direction=COLUMN))
        self.root_box.add(header_box)
        self.root_box.add(self.tabs)
        
        self.main_window.content = self.root_box
        self.main_window.show()
        self.refresh_ui()

    def create_stat_card(self, title, default_val, subtitle):
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
        year_box.add(stats_box, toga.Divider(direction=toga.Divider.HORIZONTAL), self.year_table)
        self.tabs.content.append("Year Overview", year_box)

    def setup_month_tab(self, m_idx, month_name):
        month_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        month_box.add(toga.Label(f"{month_name} Ledger", style=Pack(margin_bottom=5, font_size=16, font_weight='bold')))
        ledger_table = toga.Table(columns=["Date", "Payee", "Category", "Amount", "Notes"], style=Pack(flex=1))
        self.month_tables.append(ledger_table)
        month_box.add(ledger_table)
        self.tabs.content.append(month_name, month_box)

    async def mock_action(self, widget):
        """Temporary handler for new menu bar items."""
        await self.main_window.dialog(
            toga.InfoDialog("Coming Soon", f"The '{widget.text}' feature is currently under development.")
        )

    async def show_help_dialog(self, widget):
        await self.main_window.dialog(toga.InfoDialog("Panda Ledger Help", "Local-first payroll and transaction management. Use 'Settings' to adjust your income calendar."))

    def show_payroll_settings(self, widget):
        current_settings = self.controller.get_payroll_settings()
        self.settings_window = toga.Window(title="Payroll Configuration", size=(450, 550))
        self.content_box = toga.Box(style=Pack(direction=COLUMN, margin=15))
        
        # --- Instantiate Reusable Widget Blocks ---
        self.lbl_pay_type = toga.Label("Pay Type:", style=Pack(margin_top=10))
        self.input_pay_type = toga.Selection(items=["Hourly", "Salary"], on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_pay_type.value = current_settings["pay_type"]

        self.lbl_schedule = toga.Label("Pay Schedule:", style=Pack(margin_top=10))
        self.input_schedule = toga.Selection(items=["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly"], on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_schedule.value = current_settings["schedule"]

        self.row_rate = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.input_rate = toga.TextInput(value=str(current_settings["pay_rate"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.row_rate.add(toga.Label("Pay Rate / Salary ($):", style=Pack(width=180)), self.input_rate)

        self.hours_box = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.input_hours = toga.TextInput(value=str(current_settings["hours_per_period"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.hours_box.add(toga.Label("Hours (Weekly Fallback):", style=Pack(width=180)), self.input_hours)

        self.row_tax = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.input_tax = toga.TextInput(value=str(current_settings["tax_rate_percent"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.row_tax.add(toga.Label("Estimated Net Tax %:", style=Pack(width=180)), self.input_tax)

        self.row_sav = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.input_savings = toga.TextInput(value=str(current_settings["savings_rate_percent"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.row_sav.add(toga.Label("Target Savings %:", style=Pack(width=180)), self.input_savings)

        self.lbl_calendar_sync = toga.Label("--- Calendar Period Sync ---", style=Pack(margin_top=15, font_weight='bold'))
        
        self.row_ppe1 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.lbl_ppe1 = toga.Label("Period 1 End Date:", style=Pack(width=180))
        self.input_ppe1 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_ppe1.value = current_settings["pay_period_end_1"]
        self.row_ppe1.add(self.lbl_ppe1, self.input_ppe1)
        
        self.row_pd1 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.lbl_pd1 = toga.Label("Primary Pay Day:", style=Pack(width=180))
        self.input_pd1 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_pd1.value = current_settings["pay_day_1"]
        self.row_pd1.add(self.lbl_pd1, self.input_pd1)

        self.row_ppe2 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.input_ppe2 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_ppe2.value = current_settings["pay_period_end_2"]
        self.row_ppe2.add(toga.Label("Period 2 End Date:", style=Pack(width=180)), self.input_ppe2)

        self.row_pd2 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.input_pd2 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_pd2.value = current_settings["pay_day_2"]
        self.row_pd2.add(toga.Label("Secondary Pay Day:", style=Pack(width=180)), self.input_pd2)

        self.lbl_yearly_gross = toga.Label("$0.00", style=Pack(font_weight='bold', text_align='right', flex=1))
        self.lbl_yearly_net = toga.Label("$0.00", style=Pack(font_weight='bold', color='green', text_align='right', flex=1))
        self.lbl_yearly_savings = toga.Label("$0.00", style=Pack(font_weight='bold', color='blue', text_align='right', flex=1))

        self.estimates_box = toga.Box(style=Pack(direction=COLUMN, margin_top=25))
        self.estimates_box.add(toga.Label("--- Live Yearly Projections ---", style=Pack(margin_bottom=10, font_weight='bold')))
        row_gross = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        row_gross.add(toga.Label("Estimated Gross:", style=Pack(width=150)), self.lbl_yearly_gross)
        self.estimates_box.add(row_gross)
        row_net = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        row_net.add(toga.Label("Estimated Net:", style=Pack(width=150)), self.lbl_yearly_net)
        self.estimates_box.add(row_net)
        row_save = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        row_save.add(toga.Label("Estimated Savings:", style=Pack(width=150)), self.lbl_yearly_savings)
        self.estimates_box.add(row_save)

        self.save_btn = toga.Button("Secure & Save Config", on_press=self.handle_save_settings, style=Pack(margin_top=25))

        self.settings_window.content = toga.ScrollContainer(content=self.content_box)
        
        # Trigger initial DOM Layout map ONLY after the save_btn (the last component) exists
        self.on_settings_change(None)
        self.settings_window.show()

    def on_settings_change(self, widget):
        # Layout instantiation guard: wait until the entire form is built before rebuilding DOM layout
        if not hasattr(self, 'save_btn'): 
            return
        
        # --- DOM Rebuilder Strategy --- 
        # Safely remove all elements and re-insert to guarantee Toga Pack space collapses
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        components = [
            self.lbl_pay_type, self.input_pay_type,
            self.lbl_schedule, self.input_schedule,
            self.row_rate
        ]

        new_height = 490
        
        if self.input_pay_type.value != "Salary":
            components.append(self.hours_box)
            new_height += 40

        components.extend([self.row_tax, self.row_sav])

        schedule = self.input_schedule.value

        if schedule in ["Semi-Monthly", "Monthly"]:
            components.append(self.lbl_calendar_sync)
            components.append(self.row_ppe1)
            components.append(self.row_pd1)
            
            if schedule == "Semi-Monthly":
                self.lbl_ppe1.text = "Period 1 End Date:"
                self.lbl_pd1.text = "Primary Pay Day:"
                # Push the secondary elements ONLY if Semi-Monthly
                components.extend([self.row_ppe2, self.row_pd2])
                new_height += 190
            else:
                self.lbl_ppe1.text = "Period End Date:"
                self.lbl_pd1.text = "Pay Day:"
                new_height += 90

        components.extend([self.estimates_box, self.save_btn])

        for comp in components:
            self.content_box.add(comp)

        self.settings_window.size = (450, new_height)

        try:
            temp_settings = {
                'pay_type': self.input_pay_type.value, 
                'schedule': self.input_schedule.value,
                'pay_rate': float(self.input_rate.value or 0), 
                'hours_per_period': float(self.input_hours.value or 0),
                'tax_rate_percent': float(self.input_tax.value or 0), 
                'savings_rate_percent': float(self.input_savings.value or 0),
                'pay_day_1': int(self.input_pd1.value or 1), 
                'pay_day_2': int(self.input_pd2.value or 1),
                'pay_period_end_1': int(self.input_ppe1.value or 1), 
                'pay_period_end_2': int(self.input_ppe2.value or 1)
            }
            
            estimates = self.controller.calculate_estimates(temp_settings)
            
            self.lbl_yearly_gross.text = f"${estimates['yearly_gross']:,.2f}"
            self.lbl_yearly_net.text = f"${estimates['yearly_net']:,.2f}"
            self.lbl_yearly_savings.text = f"${estimates['yearly_savings']:,.2f}"
            
        except ValueError:
            self.lbl_yearly_gross.text = "..."
            self.lbl_yearly_net.text = "..."
            self.lbl_yearly_savings.text = "..."

    async def handle_save_settings(self, widget):
        try:
            data = {
                'pay_type': self.input_pay_type.value, 
                'schedule': self.input_schedule.value,
                'pay_rate': float(self.input_rate.value or 0), 
                'hours_per_period': float(self.input_hours.value or 0),
                'tax_rate_percent': float(self.input_tax.value or 0), 
                'savings_rate_percent': float(self.input_savings.value or 0),
                'pay_day_1': int(self.input_pd1.value or 1), 
                'pay_day_2': int(self.input_pd2.value or 1),
                'pay_period_end_1': int(self.input_ppe1.value or 1), 
                'pay_period_end_2': int(self.input_ppe2.value or 1)
            }
            
            success = self.controller.save_payroll_settings(data)
            
            if success:
                self.subtitle_label.text = f"{data['schedule']} | Tax: {data['tax_rate_percent']}%"
                
                # Await dialog BEFORE closing to ensure the Modal process finishes safely
                await self.settings_window.dialog(toga.InfoDialog("Success", "Settings secured."))
                
                # Window closes cleanly only upon successful commit and user acknowledgment
                self.settings_window.close()
                self.refresh_ui()
            else:
                await self.settings_window.dialog(toga.ErrorDialog("Error", "Save failed."))
        except Exception as e:
            await self.settings_window.dialog(toga.ErrorDialog("Error", f"Invalid inputs: {str(e)}"))

    def refresh_ui(self):
        stats = self.controller.get_annual_stats()
        self.lbl_gross.text = stats["gross"]
        self.lbl_net.text = stats["net"]
        self.lbl_sav.text = stats["savings"]
        
        self.year_table.data.clear()
        for row in self.controller.get_year_overview_table():
            self.year_table.data.append(row)
            
        for idx, table in enumerate(self.month_tables):
            real_month_num = idx + 2 
            table.data.clear()
            for row in self.controller.get_month_transactions(real_month_num):
                table.data.append(row)

# Explicitly declare App Name / Identifier to assert control over native OS Menus
def main():
    return PandaLedger(formal_name="Panda Ledger", app_id="com.pythonpanda.pandaledger")
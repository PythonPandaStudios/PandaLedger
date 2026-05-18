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
        title_label = toga.Label("PandaLedger", style=Pack(font_size=20, font_weight='bold'))
        self.subtitle_label = toga.Label("Secure Local Ledger Engine", style=Pack(font_size=12, color="gray"))
        title_box.add(title_label, self.subtitle_label)
        header_box.add(title_box)

        # --- 2. Menu Bar Commands ---
        settings_cmd = toga.Command(
            self.show_payroll_settings,
            text="Payroll Settings",
            shortcut=toga.Key.MOD_1 + "S",
            group=toga.Group.APP
        )
        
        help_cmd = toga.Command(
            self.show_help_dialog,
            text="Help & Documentation",
            group=toga.Group.APP,
            section=2
        )

        self.commands.add(settings_cmd, help_cmd)

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

    async def show_help_dialog(self, widget):
        await self.main_window.dialog(toga.InfoDialog("PandaLedger Help", "Local-first payroll and transaction management. Use 'Settings' to adjust your income calendar."))

    def show_payroll_settings(self, widget):
        current_settings = self.controller.get_payroll_settings()
        self.settings_window = toga.Window(title="Payroll Configuration", size=(450, 550))
        
        self.input_pay_type = toga.Selection(items=["Hourly", "Salary"], on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_pay_type.value = current_settings["pay_type"]

        self.input_schedule = toga.Selection(items=["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly"], on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_schedule.value = current_settings["schedule"]

        self.input_rate = toga.TextInput(value=str(current_settings["pay_rate"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_hours = toga.TextInput(value=str(current_settings["hours_per_period"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_tax = toga.TextInput(value=str(current_settings["tax_rate_percent"]), on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_savings = toga.TextInput(value=str(current_settings["savings_rate_percent"]), on_change=self.on_settings_change, style=Pack(flex=1))
        
        self.input_ppe1 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_ppe1.value = current_settings["pay_period_end_1"]
        self.input_ppe2 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_ppe2.value = current_settings["pay_period_end_2"]
        self.input_pd1 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_pd1.value = current_settings["pay_day_1"]
        self.input_pd2 = toga.NumberInput(step=1, min=1, max=31, on_change=self.on_settings_change, style=Pack(flex=1))
        self.input_pd2.value = current_settings["pay_day_2"]

        self.lbl_yearly_gross = toga.Label("$0.00", style=Pack(font_weight='bold', text_align='right', flex=1))
        self.lbl_yearly_net = toga.Label("$0.00", style=Pack(font_weight='bold', color='green', text_align='right', flex=1))
        self.lbl_yearly_savings = toga.Label("$0.00", style=Pack(font_weight='bold', color='blue', text_align='right', flex=1))

        content = toga.Box(style=Pack(direction=COLUMN, margin=15))
        content.add(toga.Label("Pay Type:", style=Pack(margin_top=10)))
        content.add(self.input_pay_type)
        content.add(toga.Label("Pay Schedule:", style=Pack(margin_top=10)))
        content.add(self.input_schedule)

        row_rate = toga.Box(style=Pack(direction=ROW, margin_top=10))
        row_rate.add(toga.Label("Pay Rate / Salary ($):", style=Pack(width=180)))
        row_rate.add(self.input_rate)
        content.add(row_rate)

        self.hours_box = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.hours_box.add(toga.Label("Hours (Weekly Fallback):", style=Pack(width=180)))
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

        # --- Base Payday Box (Used by both Monthly and Semi-Monthly) ---
        self.payday_box = toga.Box(style=Pack(direction=COLUMN))
        self.payday_box.add(toga.Label("--- Calendar Period Sync ---", style=Pack(margin_top=15, font_weight='bold')))
        
        row_ppe1 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.lbl_ppe1 = toga.Label("Period 1 End Date:", style=Pack(width=180))
        row_ppe1.add(self.lbl_ppe1, self.input_ppe1)
        self.payday_box.add(row_ppe1)
        
        row_pd1 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.lbl_pd1 = toga.Label("Primary Pay Day:", style=Pack(width=180))
        row_pd1.add(self.lbl_pd1, self.input_pd1)
        self.payday_box.add(row_pd1)
        
        # --- Secondary Payday Box (Used strictly by Semi-Monthly) ---
        self.secondary_payday_box = toga.Box(style=Pack(direction=COLUMN))
        
        row_ppe2 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        row_ppe2.add(toga.Label("Period 2 End Date:", style=Pack(width=180)), self.input_ppe2)
        self.secondary_payday_box.add(row_ppe2)
        
        row_pd2 = toga.Box(style=Pack(direction=ROW, margin_top=10))
        row_pd2.add(toga.Label("Secondary Pay Day:", style=Pack(width=180)), self.input_pd2)
        self.secondary_payday_box.add(row_pd2)
        
        self.payday_box.add(self.secondary_payday_box)
        content.add(self.payday_box)

        # Projections Box
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
        self.on_settings_change(None)
        self.settings_window.show()

    def on_settings_change(self, widget):
        # Layout instantiation guard
        if not hasattr(self, 'hours_box'): return
        
        try:
            # Baseline window height
            new_height = 490
            
            if self.input_pay_type.value == "Salary":
                self.hours_box.style.visibility = 'hidden'
            else:
                self.hours_box.style.visibility = 'visible'
                new_height += 40

            schedule = self.input_schedule.value

            if schedule == "Semi-Monthly":
                self.payday_box.style.visibility = 'visible'
                self.secondary_payday_box.style.visibility = 'visible'
                self.lbl_ppe1.text = "Period 1 End Date:"
                self.lbl_pd1.text = "Primary Pay Day:"
                new_height += 190
                
            elif schedule == "Monthly":
                self.payday_box.style.visibility = 'visible'
                self.secondary_payday_box.style.visibility = 'hidden'
                self.lbl_ppe1.text = "Period End Date:"
                self.lbl_pd1.text = "Pay Day:"
                new_height += 90
                
            else: # Weekly / Bi-Weekly
                self.payday_box.style.visibility = 'hidden'

            # Dynamically push boundaries mapping to Toga OS-window constraints
            self.settings_window.size = (450, new_height)

            # Map the transient dictionary securely
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
                'pay_rate': float(self.input_rate.value), 
                'hours_per_period': float(self.input_hours.value),
                'tax_rate_percent': float(self.input_tax.value), 
                'savings_rate_percent': float(self.input_savings.value),
                'pay_day_1': int(self.input_pd1.value), 
                'pay_day_2': int(self.input_pd2.value),
                'pay_period_end_1': int(self.input_ppe1.value), 
                'pay_period_end_2': int(self.input_ppe2.value)
            }
            success = self.controller.save_payroll_settings(data)
            if success:
                self.settings_window.close()
                self.refresh_ui()
                await self.main_window.dialog(toga.InfoDialog("Success", "Settings secured."))
            else:
                await self.main_window.dialog(toga.ErrorDialog("Error", "Save failed."))
        except ValueError:
            await self.main_window.dialog(toga.ErrorDialog("Error", "Invalid inputs."))

    def refresh_ui(self):
        stats = self.controller.get_annual_stats()
        self.lbl_gross.text = stats["gross"]
        self.lbl_net.text = stats["net"]
        self.lbl_sav.text = stats["savings"]
        self.year_table.data = self.controller.get_year_overview_table()

def main():
    return PandaLedger()
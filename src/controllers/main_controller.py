import datetime
from PySide6.QtWidgets import (QTableWidgetItem, QMessageBox, QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QScrollArea, QFrame, QTableWidget, QTableWidgetItem)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

from views.main_window import MainWindowView
from views.components import DeductionRow, ExpenseRow
from views.dialogs import PayrollSettingsDialog, ManageDeductionsDialog, ManageExpensesDialog
from views.theme_manager import THEMES

from models.payroll import PayrollCalculator
from models.database import init_db as init_sqlalchemy_db, SessionLocal
from models.schema import Account, Category, Transaction, AccountType, CategoryType, Config, Deduction, Expense
from models.qt_models import TransactionModel

class MainController:
    def __init__(self):
        self.current_year = datetime.date.today().year
        self.calculator = PayrollCalculator()
        self.current_config = {}
        
        self.init_db()
        self.seed_test_data()
        self.load_settings()

        self.view = MainWindowView()
        self.deductions_dialog = ManageDeductionsDialog(self.view)
        self.expenses_dialog = ManageExpensesDialog(self.view)
        
        self.connect_signals()
        
        self.change_theme(self.current_config.get("theme", "Light"))
        self.load_data()
        self.recalculate_budget()

    def init_db(self):
        init_sqlalchemy_db()

    def seed_test_data(self):
        with SessionLocal() as session:
            if session.query(Transaction).count() == 0:
                checking = Account(name="Main Checking", type=AccountType.CHECKING, current_balance=5000.0)
                housing = Category(name="Rent/Mortgage", type=CategoryType.FIXED, monthly_limit=2000.0)
                salary = Category(name="Income", type=CategoryType.SAVINGS, monthly_limit=0.0)
                session.add_all([checking, housing, salary])
                session.commit()

                t1 = Transaction(date=datetime.date(2026, 2, 1), payee="Landlord LLC", amount=-1500.00, notes="February Rent", account_id=checking.id, category_id=housing.id)
                t2 = Transaction(date=datetime.date(2026, 2, 15), payee="Employer Inc", amount=3000.00, notes="Mid-month pay", account_id=checking.id, category_id=salary.id)
                session.add_all([t1, t2])
                session.commit()

    def load_settings(self):
        defaults = {
            "schedule": "Semi-Monthly", "income_type": "Hourly", "rate": 45.78,
            "theme": "Light", "fed_rate": 12.0, "state_rate": 4.4, "add_tax_rate": 0.45,
            "state": "Colorado", "sm_p1_end": "15", "sm_pay1": "22", "sm_p2_end": "31", "sm_pay2": "7"
        }
        try:
            with SessionLocal() as session:
                db_settings = {c.key: c.value for c in session.query(Config).all()}
            self.current_config = defaults.copy()
            self.current_config.update(db_settings)
            
            numeric_keys = ['rate', 'state_rate', 'fed_rate', 'add_tax_rate']
            for k in numeric_keys:
                try: self.current_config[k] = float(self.current_config[k])
                except (ValueError, TypeError): self.current_config[k] = defaults[k]
        except Exception as e:
            print(f"Settings Load Error: {e}")
            self.current_config = defaults

    def save_setting(self, key, value):
        with SessionLocal() as session:
            conf = session.query(Config).filter_by(key=key).first()
            if conf:
                conf.value = str(value)
            else:
                conf = Config(key=key, value=str(value))
                session.add(conf)
            session.commit()

    def connect_signals(self):
        self.view.theme_changed_signal.connect(self.change_theme)
        self.view.open_payroll_settings_signal.connect(self.open_payroll_settings)
        self.view.export_clipboard_signal.connect(self.export_to_clipboard)
        
        self.view.manage_deductions_signal.connect(self.deductions_dialog.exec)
        self.view.manage_expenses_signal.connect(self.expenses_dialog.exec)
        
        self.deductions_dialog.add_btn.clicked.connect(lambda: self.add_deduction())
        self.expenses_dialog.add_btn.clicked.connect(lambda: self.add_expense())

    def change_theme(self, theme_name):
        self.current_config["theme"] = theme_name
        self.save_setting("theme", theme_name)
        QApplication.instance().setStyleSheet(THEMES[theme_name].stylesheet)
        self.recalculate_budget()

    def add_deduction(self, db_id=None, name="New", amount=0, is_pct=False, is_pre=True, category="Other Deduction"):
        if db_id is None:
            with SessionLocal() as session:
                new_ded = Deduction(name=name, amount=amount, is_percent=is_pct, is_pre_tax=is_pre, category=category)
                session.add(new_ded)
                session.commit()
                db_id = new_ded.id
        
        row = DeductionRow(db_id, name, amount, is_pct, is_pre, category)
        row.dataChanged.connect(self.sync_deduction)
        row.deleted.connect(self.delete_deduction)
        self.deductions_dialog.row_layout.addWidget(row)
        self.recalculate_budget()

    def add_expense(self, db_id=None, name="New", amount=0, is_global=True, month_idx=-1, category="Other Expense"):
        if db_id is None:
            with SessionLocal() as session:
                new_exp = Expense(name=name, amount=amount, is_global=is_global, month_idx=month_idx, category=category)
                session.add(new_exp)
                session.commit()
                db_id = new_exp.id
            
        row = ExpenseRow(db_id, name, amount, is_global, month_idx, category)
        row.dataChanged.connect(self.sync_expense)
        row.deleted.connect(self.delete_expense)
        self.expenses_dialog.row_layout.addWidget(row)
        self.recalculate_budget()

    def sync_deduction(self, data):
        with SessionLocal() as session:
            ded = session.query(Deduction).filter_by(id=data['id']).first()
            if ded:
                ded.name = data['name']
                ded.category = data['category']
                ded.amount = data['value']
                ded.is_percent = data['is_percent']
                ded.is_pre_tax = data['is_pre_tax']
                session.commit()
        self.recalculate_budget()

    def sync_expense(self, data):
        with SessionLocal() as session:
            exp = session.query(Expense).filter_by(id=data['id']).first()
            if exp:
                exp.name = data['name']
                exp.category = data['category']
                exp.amount = data['amount']
                exp.is_global = data['is_global']
                exp.month_idx = data['month_idx']
                session.commit()
        self.recalculate_budget()

    def delete_deduction(self, db_id):
        with SessionLocal() as session:
            ded = session.query(Deduction).filter_by(id=db_id).first()
            if ded:
                session.delete(ded)
                session.commit()
                
        layout = self.deductions_dialog.row_layout
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget and hasattr(widget, 'db_id') and widget.db_id == db_id:
                widget.setParent(None)
                widget.deleteLater()
                break
                
        self.recalculate_budget()

    def delete_expense(self, db_id):
        with SessionLocal() as session:
            exp = session.query(Expense).filter_by(id=db_id).first()
            if exp:
                session.delete(exp)
                session.commit()
                
        layout = self.expenses_dialog.row_layout
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget and hasattr(widget, 'db_id') and widget.db_id == db_id:
                widget.setParent(None)
                widget.deleteLater()
                break
                
        self.recalculate_budget()

    def load_data(self):
        with SessionLocal() as session:
            deductions = session.query(Deduction).all()
            for d in deductions: 
                # getattr used just in case schema migration isn't fully completed on first boot
                self.add_deduction(d.id, d.name, d.amount, d.is_percent, d.is_pre_tax, getattr(d, 'category', 'Other Deduction'))
                
            expenses = session.query(Expense).all()
            for e in expenses: 
                self.add_expense(e.id, e.name, e.amount, e.is_global, e.month_idx, getattr(e, 'category', 'Other Expense'))

    def recalculate_budget(self):
        try:
            self.view.subtitle.setText(f"{self.current_config.get('schedule')} | {self.current_config.get('state')} Tax Rules")
            
            expenses = [self.expenses_dialog.row_layout.itemAt(i).widget().get_values() for i in range(self.expenses_dialog.row_layout.count())]
            deductions = [self.deductions_dialog.row_layout.itemAt(i).widget().get_values() for i in range(self.deductions_dialog.row_layout.count())]
            
            pay_schedule = self.calculator.calculate_pay_dates(self.current_config, self.current_year)
            pay_schedule.sort(key=lambda x: x['date'])
            
            self.view.year_table.setRowCount(0)
            total_gross, total_net = 0, 0
            
            monthly_ledger_data = {i: [] for i in range(12)}
            
            for check in pay_schedule:
                m_idx = check['date'].month - 1
                if check['date'].year > self.current_year: m_idx = 0 
                
                gross = check['hours'] * check['rate']
                pre_tax_total, post_tax_total = 0, 0
                
                monthly_ledger_data[m_idx].append([check['date'], "Employer", "Gross Pay", gross, "Paycheck"])
                
                for d in deductions:
                    amt = d['value'] if not d['is_percent'] else gross * (d['value'] / 100)
                    if d['is_pre_tax']: pre_tax_total += amt
                    else: post_tax_total += amt
                    if amt > 0:
                        # Append with the selected custom category
                        monthly_ledger_data[m_idx].append([check['date'], d['name'], d['category'], -amt, "Payroll Deduction"])
                
                taxable = max(0, gross - pre_tax_total)
                taxes = self.calculator.calculate_taxes(gross, taxable, self.current_config)
                
                tax_map = [("Federal Tax", taxes.fed_tax), ("State Tax", taxes.state_tax), 
                           ("Social Security", taxes.ss_tax), ("Medicare", taxes.medicare_tax), 
                           ("Additional Tax", taxes.additional_tax)]
                for t_name, t_amt in tax_map:
                    if t_amt > 0:
                        monthly_ledger_data[m_idx].append([check['date'], t_name, "Tax", -t_amt, "Payroll Tax"])
                
                net = gross - pre_tax_total - taxes.total_tax - post_tax_total
                total_gross += gross
                total_net += net
                
                checks_per_month = sum(1 for c in pay_schedule if (c['date'].month - 1 == m_idx and c['date'].year == self.current_year) or (m_idx == 0 and c['date'].year > self.current_year))
                m_exp_total = sum(e['amount'] for e in expenses if e['is_global'] or e['month_idx'] == m_idx)
                rem = net - (m_exp_total / checks_per_month) if checks_per_month > 0 else net
                
                row = self.view.year_table.rowCount()
                self.view.year_table.insertRow(row)
                self.view.year_table.setItem(row, 0, QTableWidgetItem(check['date'].strftime("%b %d")))
                self.view.year_table.setItem(row, 1, QTableWidgetItem(str(check['hours'])))
                self.view.year_table.setItem(row, 2, QTableWidgetItem(f"${check['rate']}"))
                self.view.year_table.setItem(row, 3, QTableWidgetItem(f"${gross:,.2f}"))
                self.view.year_table.setItem(row, 4, QTableWidgetItem(f"${net:,.2f}"))
                self.view.year_table.setItem(row, 5, QTableWidgetItem(f"${rem:,.2f}"))

            for m_idx in range(12):
                exp_date = datetime.date(self.current_year, m_idx + 1, 1) 
                for e in expenses:
                    if e['is_global'] or e['month_idx'] == m_idx:
                        # Append with the selected custom category
                        monthly_ledger_data[m_idx].append([exp_date, e['name'], e['category'], -e['amount'], "Budgeted Expense"])

            with SessionLocal() as session:
                db_transactions = session.query(Transaction).all()
                for t in db_transactions:
                    t_m_idx = t.date.month - 1
                    if t.date.year == self.current_year and 0 <= t_m_idx <= 11:
                        category_name = t.category.name if t.category else "Uncategorized"
                        monthly_ledger_data[t_m_idx].append([t.date, t.payee, category_name, t.amount, t.notes])
            
            annual_exp_total = sum(e['amount'] * (12 if e['is_global'] else 1) for e in expenses)
            for child in self.view.card_gross.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_gross:,.2f}")
            for child in self.view.card_net.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_net:,.2f}")
            for child in self.view.card_savings.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_net - annual_exp_total:,.2f}")
                
            for m_idx, ref in enumerate(self.view.month_tabs_refs):
                month_data = monthly_ledger_data[m_idx]
                month_data.sort(key=lambda x: x[0])
                
                model = TransactionModel(month_data)
                ref['ledger'].setModel(model)
                
                net_income = 0.0
                total_expenses = 0.0
                
                for row_data in month_data:
                    amt = row_data[3]
                    # Check Notes (index 4) instead of Category (index 2) so math stays accurate!
                    notes = row_data[4]
                    
                    if notes in ["Paycheck", "Payroll Tax", "Payroll Deduction"]:
                        net_income += amt
                    elif amt < 0:
                        total_expenses += abs(amt)
                    elif amt > 0 and notes not in ["Paycheck", "Payroll Tax", "Payroll Deduction"]:
                        net_income += amt
                        
                ref['inc'].setText(f"${net_income:,.2f}")
                ref['exp'].setText(f"${total_expenses:,.2f}")
                ref['rem'].setText(f"${net_income - total_expenses:,.2f}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Recalculate Error: {e}")

    def export_to_clipboard(self):
        output = "Date\tHrs\tRate\tGross\tNet\tRemaining\n"
        for r in range(self.view.year_table.rowCount()):
            row_data = [self.view.year_table.item(r, c).text() for c in range(self.view.year_table.columnCount())]
            output += "\t".join(row_data) + "\n"
        QGuiApplication.clipboard().setText(output)
        QMessageBox.information(self.view, "Exported", "Data copied for Excel.")

    def show(self):
        self.view.show()
import os
import shutil
import datetime
from PySide6.QtWidgets import (QTableWidgetItem, QMessageBox, QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QScrollArea, QFrame, QTableWidget, QTableWidgetItem)
from PySide6.QtGui import QGuiApplication, QDesktopServices
from PySide6.QtCore import Qt, QStandardPaths, QUrl

from views.main_window import MainWindowView
from views.components import DeductionRow, ExpenseRow
from views.dialogs import PayrollSettingsDialog, ManageDeductionsDialog, AddTransactionDialog
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
        
        # New Add Transaction Dialog Instance
        self.add_tx_dialog = AddTransactionDialog(self.view)
        
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
        self.deductions_dialog.add_btn.clicked.connect(lambda: self.add_deduction())
        
        # Open the new Add Transaction popup
        self.view.add_transaction_signal.connect(self.open_add_transaction_dialog)
        
        # Dialog Internal Signals
        self.add_tx_dialog.payee_edited_signal.connect(self.handle_payee_edited)
        self.add_tx_dialog.save_transaction_signal.connect(self.save_transaction)
        
        self.view.receipt_dropped_signal.connect(self.handle_receipt_dropped)
        self.view.ledger_double_clicked_signal.connect(self.handle_ledger_double_click)

    def change_theme(self, theme_name):
        self.current_config["theme"] = theme_name
        self.save_setting("theme", theme_name)
        QApplication.instance().setStyleSheet(THEMES[theme_name].stylesheet)
        self.recalculate_budget()

    def open_payroll_settings(self):
        dialog = PayrollSettingsDialog(self.view, self.current_config)
        if dialog.exec():
            self.current_config = dialog.get_data()
            for k, v in self.current_config.items(): self.save_setting(k, v)
            self.recalculate_budget()

    def open_add_transaction_dialog(self):
        # Refresh the accounts combo list each time it opens
        with SessionLocal() as session:
            accounts = session.query(Account).all()
            self.add_tx_dialog.tx_account.clear()
            for a in accounts:
                self.add_tx_dialog.tx_account.addItem(a.name, a.id)
                
        # Clear previous inputs
        self.add_tx_dialog.tx_payee.clear()
        self.add_tx_dialog.tx_amount.clear()
        self.add_tx_dialog.tx_notes.clear()
        
        self.add_tx_dialog.exec()

    def handle_payee_edited(self, text):
        if not text or len(text) < 2: return
        with SessionLocal() as session:
            match = session.query(Transaction).filter(Transaction.payee.ilike(f"%{text}%")).order_by(Transaction.date.desc()).first()
            if match:
                if match.category:
                    self.add_tx_dialog.tx_category.setCurrentText(match.category.name)
                
                acc_idx = self.add_tx_dialog.tx_account.findData(match.account_id)
                if acc_idx >= 0: self.add_tx_dialog.tx_account.setCurrentIndex(acc_idx)

    def save_transaction(self, tx_data):
        try:
            amt = float(tx_data['amount'])
        except ValueError:
            amt = 0.0
            
        with SessionLocal() as session:
            # Smart logic: Find or create the Category if the string doesn't exist yet
            cat_name = tx_data['category']
            category = session.query(Category).filter_by(name=cat_name).first()
            if not category:
                category = Category(name=cat_name, type=CategoryType.VARIABLE, monthly_limit=0.0)
                session.add(category)
                session.commit()
                
            new_tx = Transaction(
                date=tx_data['date'],
                payee=tx_data['payee'],
                amount=amt,
                category_id=category.id,
                account_id=tx_data['account_id'],
                notes=tx_data['notes']
            )
            session.add(new_tx)
            session.commit()
        
        self.recalculate_budget()

    def handle_receipt_dropped(self, db_id, file_path):
        user_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        receipts_dir = os.path.join(user_data_path, "PythonPandaStudios", "PandaLedger", "receipts")
        os.makedirs(receipts_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        unique_filename = f"tx_{db_id}_{filename}"
        dest_path = os.path.join(receipts_dir, unique_filename)
        
        shutil.copy2(file_path, dest_path)
        
        with SessionLocal() as session:
            tx = session.query(Transaction).get(db_id)
            if tx:
                tx.receipt_path = dest_path
                session.commit()
                
        self.recalculate_budget()

    def handle_ledger_double_click(self, index):
        model = index.model()
        path = model.data(index, Qt.UserRole + 2) 
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

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

    def load_data(self):
        with SessionLocal() as session:
            deductions = session.query(Deduction).all()
            for d in deductions: 
                self.add_deduction(d.id, d.name, d.amount, d.is_percent, d.is_pre_tax, getattr(d, 'category', 'Other Deduction'))

    def recalculate_budget(self):
        try:
            self.view.subtitle.setText(f"{self.current_config.get('schedule')} | {self.current_config.get('state')} Tax Rules")
            
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
                
                monthly_ledger_data[m_idx].append([check['date'], "Employer", "Gross Pay", gross, "Paycheck", None, None])
                
                for d in deductions:
                    amt = d['value'] if not d['is_percent'] else gross * (d['value'] / 100)
                    if d['is_pre_tax']: pre_tax_total += amt
                    else: post_tax_total += amt
                    if amt > 0:
                        monthly_ledger_data[m_idx].append([check['date'], d['name'], d['category'], -amt, "Payroll Deduction", None, None])
                
                taxable = max(0, gross - pre_tax_total)
                taxes = self.calculator.calculate_taxes(gross, taxable, self.current_config)
                
                tax_map = [("Federal Tax", taxes.fed_tax), ("State Tax", taxes.state_tax), 
                           ("Social Security", taxes.ss_tax), ("Medicare", taxes.medicare_tax), 
                           ("Additional Tax", taxes.additional_tax)]
                for t_name, t_amt in tax_map:
                    if t_amt > 0:
                        monthly_ledger_data[m_idx].append([check['date'], t_name, "Tax", -t_amt, "Payroll Tax", None, None])
                
                net = gross - pre_tax_total - taxes.total_tax - post_tax_total
                total_gross += gross
                total_net += net
                
                # Removed budgeted expenses math from checks_per_month rem calculation
                rem = net
                
                row = self.view.year_table.rowCount()
                self.view.year_table.insertRow(row)
                self.view.year_table.setItem(row, 0, QTableWidgetItem(check['date'].strftime("%b %d")))
                self.view.year_table.setItem(row, 1, QTableWidgetItem(str(check['hours'])))
                self.view.year_table.setItem(row, 2, QTableWidgetItem(f"${check['rate']}"))
                self.view.year_table.setItem(row, 3, QTableWidgetItem(f"${gross:,.2f}"))
                self.view.year_table.setItem(row, 4, QTableWidgetItem(f"${net:,.2f}"))
                self.view.year_table.setItem(row, 5, QTableWidgetItem(f"${rem:,.2f}"))

            with SessionLocal() as session:
                db_transactions = session.query(Transaction).all()
                for t in db_transactions:
                    t_m_idx = t.date.month - 1
                    if t.date.year == self.current_year and 0 <= t_m_idx <= 11:
                        category_name = t.category.name if t.category else "Uncategorized"
                        monthly_ledger_data[t_m_idx].append([t.date, t.payee, category_name, t.amount, t.notes, t.id, t.receipt_path])
            
            for child in self.view.card_gross.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_gross:,.2f}")
            for child in self.view.card_net.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_net:,.2f}")
            for child in self.view.card_savings.findChildren(QLabel):
                # Using total_net as placeholder now that budgeted expenses were removed
                if child.objectName() == "StatValue": child.setText(f"${total_net:,.2f}")
                
            for m_idx, ref in enumerate(self.view.month_tabs_refs):
                month_data = monthly_ledger_data[m_idx]
                month_data.sort(key=lambda x: x[0])
                
                model = TransactionModel(month_data)
                ref['ledger'].setModel(model)
                
                net_income = 0.0
                total_expenses = 0.0
                
                for row_data in month_data:
                    amt = row_data[3]
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
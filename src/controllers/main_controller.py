import datetime
import sqlite3
from PySide6.QtWidgets import (QTableWidgetItem, QMessageBox, QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QScrollArea, QFrame, QTableWidget, QTableWidgetItem, QMessageBox)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

# Import our Views
from views.main_window import MainWindowView
from views.components import DeductionRow, ExpenseRow
from views.dialogs import PayrollSettingsDialog
from views.theme_manager import THEMES

# Import our Models
from models.payroll import PayrollCalculator
from models.database import init_db as init_sqlalchemy_db, DB_FILE, SessionLocal
from models.schema import Account, Category, Transaction, AccountType, CategoryType
from models.qt_models import TransactionModel

class MainController:
    """The Controller connects the View (GUI) to the Models (Data/Logic)."""
    def __init__(self):
        # 1. Initialize Models
        self.current_year = datetime.date.today().year
        self.calculator = PayrollCalculator()
        self.current_config = {}
        
        self.init_db()
        self.seed_test_data() # Add dummy data if the DB is empty
        self.load_settings()

        # 2. Initialize View
        self.view = MainWindowView()
        self.connect_signals()
        
        # 3. Apply Initial State
        self.change_theme(self.current_config.get("theme", "Light"))
        self.load_data()
        self.load_transactions() # Fetch and display SQLAlchemy data

    def init_db(self):
        init_sqlalchemy_db()
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)')
                cursor.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, amount REAL)')
                cursor.execute('CREATE TABLE IF NOT EXISTS deductions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, amount REAL, is_percent INTEGER, is_pre_tax INTEGER)')
        except sqlite3.Error as e:
            print(f"Database Error: {e}")

    def seed_test_data(self):
        """Seeds the database with initial test data if it is empty."""
        with SessionLocal() as session:
            # Check if we already have transactions so we don't duplicate them
            if session.query(Transaction).count() == 0:
                # 1. Create a default account and some categories
                checking = Account(name="Main Checking", type=AccountType.CHECKING, current_balance=5000.0)
                housing = Category(name="Rent/Mortgage", type=CategoryType.FIXED, monthly_limit=2000.0)
                salary = Category(name="Income", type=CategoryType.SAVINGS, monthly_limit=0.0)

                session.add_all([checking, housing, salary])
                session.commit()

                # 2. Add dummy transactions tied to those accounts/categories
                t1 = Transaction(date=datetime.date(2026, 2, 1), payee="Landlord LLC", amount=-1500.00, notes="February Rent", account_id=checking.id, category_id=housing.id)
                t2 = Transaction(date=datetime.date(2026, 2, 15), payee="Employer Inc", amount=3000.00, notes="Mid-month pay", account_id=checking.id, category_id=salary.id)

                session.add_all([t1, t2])
                session.commit()

    def load_transactions(self):
        """Fetches transactions from SQLAlchemy and binds them to the View's table."""
        with SessionLocal() as session:
            # Fetch all transactions from the database
            db_transactions = session.query(Transaction).all()
            
            # Format them into the List of Lists expected by our TransactionModel
            table_data = []
            for t in db_transactions:
                # Safely get the category name via the SQLAlchemy relationship
                category_name = t.category.name if t.category else "Uncategorized"
                
                # Order matters here: [Date, Payee, Category, Amount, Notes]
                table_data.append([t.date, t.payee, category_name, t.amount, t.notes])
            
            # Create the model and apply it to the view
            self.transaction_model = TransactionModel(table_data)
            self.view.ledger_view.setModel(self.transaction_model)

    def load_settings(self):
        defaults = {
            "schedule": "Semi-Monthly", "income_type": "Hourly", "rate": 45.78,
            "theme": "Light", "fed_rate": 12.0, "state_rate": 4.4, "add_tax_rate": 0.45,
            "state": "Colorado", "sm_p1_end": "15", "sm_pay1": "22", "sm_p2_end": "31", "sm_pay2": "7"
        }
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM config")
                db_settings = {r[0]: r[1] for r in cursor.fetchall()}
            self.current_config = defaults.copy()
            self.current_config.update(db_settings)
            numeric_keys = ['rate', 'state_rate', 'fed_rate', 'add_tax_rate']
            for k in numeric_keys:
                try: self.current_config[k] = float(self.current_config[k])
                except (ValueError, TypeError): self.current_config[k] = defaults[k]
        except sqlite3.Error:
            self.current_config = defaults

    def save_setting(self, key, value):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
        except sqlite3.Error: pass

    # --- SIGNAL ROUTING ---
    def connect_signals(self):
        """Listen to the View's signals and route them to Controller methods."""
        self.view.theme_changed_signal.connect(self.change_theme)
        self.view.open_payroll_settings_signal.connect(self.open_payroll_settings)
        self.view.add_deduction_signal.connect(lambda: self.add_deduction())
        self.view.add_expense_signal.connect(lambda: self.add_expense())
        self.view.export_clipboard_signal.connect(self.export_to_clipboard)

    # --- CONTROLLER LOGIC ---
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

    def add_deduction(self, db_id=None, name="New", amount=0, is_pct=False, is_pre=True):
        if db_id is None:
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO deductions (name, amount, is_percent, is_pre_tax) VALUES (?,?,?,?)", (name, amount, int(is_pct), int(is_pre)))
                    db_id = cursor.lastrowid
            except sqlite3.Error: return
        
        row = DeductionRow(db_id, name, amount, is_pct, is_pre)
        row.dataChanged.connect(self.sync_deduction)
        row.deleted.connect(self.delete_deduction)
        
        self.view.ded_layout.addWidget(row)
        self.recalculate_budget()

    def add_expense(self, db_id=None, name="New", amount=0):
        if db_id is None:
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO expenses (name, amount) VALUES (?,?)", (name, amount))
                    db_id = cursor.lastrowid
            except sqlite3.Error: return
            
        row = ExpenseRow(db_id, name, amount)
        row.dataChanged.connect(self.sync_expense)
        row.deleted.connect(self.delete_expense)
        
        self.view.exp_layout.addWidget(row)
        self.recalculate_budget()

    def sync_deduction(self, data):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE deductions SET name=?, amount=?, is_percent=?, is_pre_tax=? WHERE id=?", 
                             (data['name'], data['value'], int(data['is_percent']), int(data['is_pre_tax']), data['id']))
            self.recalculate_budget()
        except sqlite3.Error: pass

    def sync_expense(self, data):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE expenses SET name=?, amount=? WHERE id=?", (data['name'], data['amount'], data['id']))
            self.recalculate_budget()
        except sqlite3.Error: pass

    def delete_deduction(self, db_id):
        try:
            with sqlite3.connect(DB_FILE) as conn: conn.execute("DELETE FROM deductions WHERE id=?", (db_id,))
            self.view.sender().setParent(None)
            self.recalculate_budget()
        except sqlite3.Error: pass

    def delete_expense(self, db_id):
        try:
            with sqlite3.connect(DB_FILE) as conn: conn.execute("DELETE FROM expenses WHERE id=?", (db_id,))
            self.view.sender().setParent(None)
            self.recalculate_budget()
        except sqlite3.Error: pass

    def load_data(self):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, amount, is_percent, is_pre_tax FROM deductions")
                for r in cursor.fetchall(): self.add_deduction(r[0], r[1], r[2], bool(r[3]), bool(r[4]))
                cursor.execute("SELECT id, name, amount FROM expenses")
                for r in cursor.fetchall(): self.add_expense(r[0], r[1], r[2])
        except sqlite3.Error: pass

    def recalculate_budget(self):
        try:
            self.view.subtitle.setText(f"{self.current_config.get('schedule')} | {self.current_config.get('state')} Tax Rules")
            
            expenses = [self.view.exp_layout.itemAt(i).widget().get_values() for i in range(self.view.exp_layout.count())]
            total_exp = sum(e['amount'] for e in expenses)
            self.view.lbl_total_exp.setText(f"Total Monthly: ${total_exp:,.2f}")
            
            deductions = [self.view.ded_layout.itemAt(i).widget().get_values() for i in range(self.view.ded_layout.count())]
            
            pay_schedule = self.calculator.calculate_pay_dates(self.current_config, self.current_year)
            pay_schedule.sort(key=lambda x: x['date'])
            
            self.view.year_table.setRowCount(0)
            total_gross, total_net = 0, 0
            monthly_data = {i: [] for i in range(12)}
            
            for check in pay_schedule:
                gross = check['hours'] * check['rate']
                check_ded_details = []
                pre_tax_total, post_tax_total = 0, 0
                for d in deductions:
                    amt = d['value'] if not d['is_percent'] else gross * (d['value'] / 100)
                    check_ded_details.append({'name': d['name'], 'amount': amt})
                    if d['is_pre_tax']: pre_tax_total += amt
                    else: post_tax_total += amt
                
                taxable = max(0, gross - pre_tax_total)
                taxes = self.calculator.calculate_taxes(gross, taxable, self.current_config)
                net = gross - pre_tax_total - taxes.total_tax - post_tax_total
                rem = net - (total_exp / 2)
                
                total_gross += gross
                total_net += net
                
                row = self.view.year_table.rowCount()
                self.view.year_table.insertRow(row)
                self.view.year_table.setItem(row, 0, QTableWidgetItem(check['date'].strftime("%b %d")))
                self.view.year_table.setItem(row, 1, QTableWidgetItem(str(check['hours'])))
                self.view.year_table.setItem(row, 2, QTableWidgetItem(f"${check['rate']}"))
                self.view.year_table.setItem(row, 3, QTableWidgetItem(f"${gross:,.2f}"))
                self.view.year_table.setItem(row, 4, QTableWidgetItem(f"${net:,.2f}"))
                self.view.year_table.setItem(row, 5, QTableWidgetItem(f"${rem:,.2f}"))
                
                m_idx = check['date'].month - 1
                if check['date'].year > self.current_year: m_idx = 0 
                monthly_data[m_idx].append({'date': check['date'], 'gross': gross, 'net': net, 'taxes': taxes, 'deductions_list': check_ded_details})
                
            for child in self.view.card_gross.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_gross:,.2f}")
            for child in self.view.card_net.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_net:,.2f}")
            for child in self.view.card_savings.findChildren(QLabel):
                if child.objectName() == "StatValue": child.setText(f"${total_net - (total_exp * 12):,.2f}")
                
            for m_idx, ref in enumerate(self.view.month_tabs_refs):
                checks = monthly_data[m_idx]
                ref['table'].setRowCount(0)
                m_net = sum(c['net'] for c in checks)
                for c in checks:
                    r = ref['table'].rowCount()
                    ref['table'].insertRow(r)
                    ref['table'].setItem(r, 0, QTableWidgetItem(c['date'].strftime("%b %d")))
                    ref['table'].setItem(r, 1, QTableWidgetItem(f"${c['gross']:,.2f}"))
                    ref['table'].setItem(r, 2, QTableWidgetItem(f"${c['net']:,.2f}"))
                ref['inc'].setText(f"${m_net:,.2f}")
                ref['exp'].setText(f"${total_exp:,.2f}")
                ref['rem'].setText(f"${m_net - total_exp:,.2f}")
                
                grid = ref['grid']
                while grid.count():
                    item = grid.takeAt(0)
                    if item.widget(): item.widget().deleteLater()
                
                row_idx = 0
                for check_data in checks:
                    title = QLabel(f"Paycheck: {check_data['date'].strftime('%b %d, %Y')}")
                    title.setStyleSheet("font-weight: bold; color: #3B82F6; font-size: 15px;")
                    grid.addWidget(title, row_idx, 0, 1, 2); row_idx += 1
                    
                    grid.addWidget(QLabel("Gross Pay"), row_idx, 0)
                    v_gross = QLabel(f"${check_data['gross']:,.2f}")
                    v_gross.setAlignment(Qt.AlignRight)
                    grid.addWidget(v_gross, row_idx, 1); row_idx += 1
                    
                    t = check_data['taxes']
                    tax_map = [("Federal", t.fed_tax), ("State", t.state_tax), ("SS", t.ss_tax), ("Med", t.medicare_tax), ("Addtl", t.additional_tax)]
                    for label, val in tax_map:
                        if val > 0:
                            l = QLabel(f"  {label}"); l.setStyleSheet("color: #6B7280; font-size: 12px;"); grid.addWidget(l, row_idx, 0)
                            v = QLabel(f"-${val:,.2f}"); v.setStyleSheet("color: #EF4444; font-size: 12px;"); v.setAlignment(Qt.AlignRight); grid.addWidget(v, row_idx, 1)
                            row_idx += 1
                            
                    for ded in check_data['deductions_list']:
                        l = QLabel(f"  {ded['name']}"); l.setStyleSheet("color: #6B7280; font-size: 12px;"); grid.addWidget(l, row_idx, 0)
                        v = QLabel(f"-${ded['amount']:,.2f}"); v.setStyleSheet("color: #EF4444; font-size: 12px;"); v.setAlignment(Qt.AlignRight); grid.addWidget(v, row_idx, 1)
                        row_idx += 1
                        
                    net_l, net_v = QLabel("Net Total"), QLabel(f"${check_data['net']:,.2f}")
                    net_l.setStyleSheet("font-weight: bold; border-top: 1px solid #E5E7EB;")
                    net_v.setStyleSheet("font-weight: bold; border-top: 1px solid #E5E7EB;"); net_v.setAlignment(Qt.AlignRight)
                    grid.addWidget(net_l, row_idx, 0); grid.addWidget(net_v, row_idx, 1); row_idx += 1
                    grid.addWidget(QLabel(""), row_idx, 0); row_idx += 1 
        except Exception as e:
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
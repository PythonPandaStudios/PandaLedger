import os
import calendar
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QTableView
from PySide6.QtCore import Signal, Qt

DEDUCTION_CATEGORIES = [
    "401k", "ROTH IRA", "Traditional IRA", "Health Insurance", 
    "Dental Insurance", "Vision Insurance", "HSA", "FSA", 
    "Life Insurance", "Union Dues", "Other Deduction"
]

EXPENSE_CATEGORIES = [
    "Rent/Mortgage", "Utilities", "Internet/Cable", "Groceries", 
    "Dining Out", "Transportation/Gas", "Car Payment", "Auto Insurance", 
    "Student Loan", "Debt Payment", "Entertainment", "Personal Care", 
    "Savings", "Subscriptions", "Other Expense"
]

class LedgerTableView(QTableView):
    receipt_dropped = Signal(int, str) # db_id, file_path

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSortingEnabled(True)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    ext = os.path.splitext(url.toLocalFile())[1].lower()
                    if ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                    index = self.indexAt(event.pos())
                    if index.isValid():
                        model = self.model()
                        # Retrieve the db_id from our custom UserRole 
                        db_id = model.data(index, Qt.UserRole + 1)
                        if db_id is not None:
                            self.receipt_dropped.emit(db_id, file_path)
                            event.acceptProposedAction()
                            break

class DeductionRow(QWidget):
    dataChanged = Signal(dict)
    deleted = Signal(int)

    def __init__(self, db_id, name, amount, is_percent, is_pre_tax, category="Other Deduction"):
        super().__init__()
        self.db_id = db_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        
        self.name_input = QLineEdit(name)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(DEDUCTION_CATEGORIES)
        self.category_combo.setCurrentText(category if category in DEDUCTION_CATEGORIES else "Other Deduction")
        
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setFixedWidth(80)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["$", "%"])
        self.type_combo.setCurrentIndex(1 if is_percent else 0)
        
        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["Pre-Tax", "Post-Tax"])
        self.tax_combo.setCurrentIndex(0 if is_pre_tax else 1)
        
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)

        layout.addWidget(self.name_input, 2)
        layout.addWidget(self.category_combo, 2)
        layout.addWidget(self.amount_input, 1)
        layout.addWidget(self.type_combo, 0)
        layout.addWidget(self.tax_combo, 0)
        layout.addWidget(self.del_btn, 0)

        self.name_input.textChanged.connect(self.emit_changed)
        self.category_combo.currentTextChanged.connect(self.emit_changed)
        self.amount_input.textChanged.connect(self.emit_changed)
        self.type_combo.currentIndexChanged.connect(self.emit_changed)
        self.tax_combo.currentIndexChanged.connect(self.emit_changed)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.db_id))

    def emit_changed(self):
        self.dataChanged.emit(self.get_values())

    def get_values(self):
        try:
            val = float(self.amount_input.text())
        except ValueError:
            val = 0.0
        return {
            'id': self.db_id, 
            'name': self.name_input.text(), 
            'category': self.category_combo.currentText(),
            'value': val, 
            'is_percent': self.type_combo.currentIndex() == 1, 
            'is_pre_tax': self.tax_combo.currentIndex() == 0
        }

class ExpenseRow(QWidget):
    dataChanged = Signal(dict)
    deleted = Signal(int)

    def __init__(self, db_id, name, amount, is_global=True, month_idx=-1, category="Other Expense"):
        super().__init__()
        self.db_id = db_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        
        self.name_input = QLineEdit(name)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(EXPENSE_CATEGORIES)
        self.category_combo.setCurrentText(category if category in EXPENSE_CATEGORIES else "Other Expense")
        
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setFixedWidth(80)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("Global (All)")
        self.scope_combo.addItems(list(calendar.month_name)[1:])
        
        if is_global:
            self.scope_combo.setCurrentIndex(0)
        else:
            self.scope_combo.setCurrentIndex(month_idx + 1)
            
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)

        layout.addWidget(self.name_input, 2)
        layout.addWidget(self.category_combo, 2)
        layout.addWidget(self.amount_input, 1)
        layout.addWidget(self.scope_combo, 1)
        layout.addWidget(self.del_btn, 0)

        self.name_input.textChanged.connect(self.emit_changed)
        self.category_combo.currentTextChanged.connect(self.emit_changed)
        self.amount_input.textChanged.connect(self.emit_changed)
        self.scope_combo.currentIndexChanged.connect(self.emit_changed)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.db_id))

    def emit_changed(self):
        self.dataChanged.emit(self.get_values())

    def get_values(self):
        try:
            val = float(self.amount_input.text())
        except ValueError:
            val = 0.0
            
        idx = self.scope_combo.currentIndex()
        is_global = (idx == 0)
        month_idx = idx - 1 if not is_global else -1

        return {
            'id': self.db_id, 
            'name': self.name_input.text(), 
            'category': self.category_combo.currentText(),
            'amount': val,
            'is_global': is_global,
            'month_idx': month_idx
        }
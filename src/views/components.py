import calendar
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton
from PySide6.QtCore import Signal

class DeductionRow(QWidget):
    # MVC Signals: Emits the dictionary of values when changed, or the ID when deleted
    dataChanged = Signal(dict)
    deleted = Signal(int)

    def __init__(self, db_id, name, amount, is_percent, is_pre_tax):
        super().__init__()
        self.db_id = db_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        
        self.name_input = QLineEdit(name)
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

        layout.addWidget(self.name_input, 3)
        layout.addWidget(self.amount_input, 1)
        layout.addWidget(self.type_combo, 0)
        layout.addWidget(self.tax_combo, 0)
        layout.addWidget(self.del_btn, 0)

        # Connect internal UI interactions to our custom emitters
        self.name_input.textChanged.connect(self.emit_changed)
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
            'value': val, 
            'is_percent': self.type_combo.currentIndex() == 1, 
            'is_pre_tax': self.tax_combo.currentIndex() == 0
        }

class ExpenseRow(QWidget):
    # MVC Signals: Emits the dictionary of values when changed, or the ID when deleted
    dataChanged = Signal(dict)
    deleted = Signal(int)

    def __init__(self, db_id, name, amount, is_global=True, month_idx=-1):
        super().__init__()
        self.db_id = db_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        
        self.name_input = QLineEdit(name)
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setFixedWidth(80)
        
        # New: Dropdown to select Global or a specific month
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("Global (All)")
        self.scope_combo.addItems(list(calendar.month_name)[1:]) # Adds Jan through Dec
        
        # Set the initial selection based on the database data
        if is_global:
            self.scope_combo.setCurrentIndex(0)
        else:
            self.scope_combo.setCurrentIndex(month_idx + 1) # +1 because Index 0 is "Global"
            
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)

        layout.addWidget(self.name_input, 2)
        layout.addWidget(self.amount_input, 1)
        layout.addWidget(self.scope_combo, 1) # Add combo box to layout
        layout.addWidget(self.del_btn, 0)

        self.name_input.textChanged.connect(self.emit_changed)
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
            
        # Determine global status and month index based on dropdown choice
        idx = self.scope_combo.currentIndex()
        is_global = (idx == 0)
        month_idx = idx - 1 if not is_global else -1

        return {
            'id': self.db_id, 
            'name': self.name_input.text(), 
            'amount': val,
            'is_global': is_global,
            'month_idx': month_idx
        }
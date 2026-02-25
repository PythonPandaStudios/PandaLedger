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

    def __init__(self, db_id, name, amount):
        super().__init__()
        self.db_id = db_id
        layout = QHBoxLayout(self)
        self.name_input = QLineEdit(name)
        self.amount_input = QLineEdit(str(amount) if amount != 0 else "")
        self.amount_input.setFixedWidth(80)
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.setFixedSize(24, 24)

        layout.addWidget(self.name_input, 1)
        layout.addWidget(self.amount_input, 0)
        layout.addWidget(self.del_btn, 0)

        self.name_input.textChanged.connect(self.emit_changed)
        self.amount_input.textChanged.connect(self.emit_changed)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.db_id))

    def emit_changed(self):
        self.dataChanged.emit(self.get_values())

    def get_values(self):
        try:
            val = float(self.amount_input.text())
        except ValueError:
            val = 0.0
        return {'id': self.db_id, 'name': self.name_input.text(), 'amount': val}
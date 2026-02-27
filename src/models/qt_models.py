import datetime
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor

class TransactionModel(QAbstractTableModel):
    # Custom Roles to store hidden background data
    DB_ID_ROLE = Qt.UserRole + 1
    RECEIPT_PATH_ROLE = Qt.UserRole + 2

    def __init__(self, data=None):
        super().__init__()
        # Data structure: [Date, Payee, Category, Amount, Notes, db_id, receipt_path]
        self._data = data or []
        self._headers = ["Date", "Payee", "Category", "Amount", "Notes"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        # Even though we hold 7 items, we only want to display the first 5 columns
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        value = self._data[row][col]
        
        if role == Qt.DisplayRole:
            if col == 0 and isinstance(value, datetime.date):
                return value.strftime("%Y-%m-%d")
            elif col == 3: 
                return f"${value:,.2f}"
            elif col == 4: # Notes Column
                # Prepend a paperclip icon if a receipt exists
                receipt = self._data[row][6] if len(self._data[row]) > 6 else None
                if receipt: return f"📎 {value}"
            return str(value)
            
        elif role == Qt.ForegroundRole:
            if col == 3: 
                if isinstance(value, (int, float)):
                    if value > 0: return QColor("green")
                    elif value < 0: return QColor("red")
        
        elif role == Qt.TextAlignmentRole:
            if col == 3: 
                return Qt.AlignRight | Qt.AlignVCenter
                
        # Return hidden data when queried by the Table View Event Handlers
        elif role == self.DB_ID_ROLE:
            return self._data[row][5] if len(self._data[row]) > 5 else None
        elif role == self.RECEIPT_PATH_ROLE:
            return self._data[row][6] if len(self._data[row]) > 6 else None
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None
        
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self._data.sort(key=lambda x: x[column], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()
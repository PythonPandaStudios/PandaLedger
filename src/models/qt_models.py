import datetime
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor

class TransactionModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        # Data structure: List of lists: [Date, Payee, Category, Amount, Notes]
        self._data = data or []
        self._headers = ["Date", "Payee", "Category", "Amount", "Notes"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        value = self._data[row][col]
        
        # Format how data is displayed as text
        if role == Qt.DisplayRole:
            if col == 0 and isinstance(value, datetime.date):
                return value.strftime("%Y-%m-%d")
            elif col == 3: # Amount Column
                return f"${value:,.2f}"
            return str(value)
            
        # Color coding: Green for positive, Red for negative
        elif role == Qt.ForegroundRole:
            if col == 3: # Amount Column
                if isinstance(value, (int, float)):
                    if value > 0:
                        return QColor("green")
                    elif value < 0:
                        return QColor("red")
        
        # Align currency to the right for better readability
        elif role == Qt.TextAlignmentRole:
            if col == 3: 
                return Qt.AlignRight | Qt.AlignVCenter
                
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None
        
    def sort(self, column, order):
        """Allows the QTableView to sort data when a header is clicked."""
        self.layoutAboutToBeChanged.emit()
        self._data.sort(key=lambda x: x[column], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()
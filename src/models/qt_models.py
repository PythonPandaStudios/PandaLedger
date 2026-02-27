import datetime
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor

class TransactionModel(QAbstractTableModel):
    DB_ID_ROLE = Qt.UserRole + 1
    RECEIPT_PATH_ROLE = Qt.UserRole + 2

    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        # Added a 6th empty header column for the delete button
        self._headers = ["Date", "Payee", "Category", "Amount", "Notes", ""]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:
                val = self._data[row][0]
                return val.strftime("%Y-%m-%d") if isinstance(val, datetime.date) else str(val)
            elif col == 1:
                return str(self._data[row][1])
            elif col == 2:
                return str(self._data[row][2])
            elif col == 3: 
                return f"${self._data[row][3]:,.2f}"
            elif col == 4: 
                val = self._data[row][4]
                receipt = self._data[row][6] if len(self._data[row]) > 6 else None
                if receipt: return f"📎 {val}"
                return str(val)
            elif col == 5:
                # Add the trashcan emoji
                return "🗑️"
            
        elif role == Qt.ForegroundRole:
            if col == 3: 
                v = self._data[row][col]
                if isinstance(v, (int, float)):
                    if v > 0: return QColor("green")
                    elif v < 0: return QColor("red")
            elif col == 5:
                # Make the trashcan red
                return QColor("red")
        
        elif role == Qt.TextAlignmentRole:
            if col == 3: 
                return Qt.AlignRight | Qt.AlignVCenter
            elif col == 5:
                return Qt.AlignCenter
                
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
        self._data.sort(key=lambda x: x[column] if column < 5 else x[0], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()
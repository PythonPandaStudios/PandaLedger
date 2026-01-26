class Theme:
    def __init__(self, name, stylesheet, palette):
        self.name = name
        self.stylesheet = stylesheet
        self.palette = palette

# --- LIGHT THEME ---
LIGHT_PALETTE = {
    "text_primary": "#374151",
    "text_secondary": "#6B7280",
    "bg_primary": "#F9FAFB",
    "bg_secondary": "#FFFFFF",
}

LIGHT_STYLESHEET = """
/* FORCE DEFAULTS: Override system dark theme settings globally */
QMainWindow, QDialog { background-color: #F9FAFB; color: #374151; }
QWidget { font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 14px; color: #374151; }

/* TABS */
QTabWidget::pane { border: 1px solid #E5E7EB; background: white; border-radius: 4px; }
QTabBar::tab { background: #F3F4F6; border: 1px solid #E5E7EB; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #6B7280; font-weight: bold; }
QTabBar::tab:selected { background: #FFFFFF; border-bottom-color: #FFFFFF; color: #1F2937; }

/* TABS SCROLL BUTTONS */
QTabBar::scroller { width: 24px; }
QTabBar QToolButton { 
    background-color: #F3F4F6; 
    border: 1px solid #E5E7EB; 
    color: #374151; 
    border-radius: 0px;
}
QTabBar QToolButton:hover { background-color: #E5E7EB; }

/* SCROLL AREAS - Global Transparency for Viewports */
QScrollArea { background-color: transparent; border: none; }
QScrollArea > QWidget { background-color: transparent; }
QScrollArea > QWidget > QWidget { background-color: transparent; }

/* FIX: Restore Grey Backgrounds for Sidebar Boxes */
QFrame#Sidebar QScrollArea { 
    background-color: #F8FAFC; 
    border: 1px solid #E5E7EB; 
    border-radius: 6px; 
}

/* FIX: Specific Styling for Breakdown Box */
QScrollArea#ExpenseBreakdownBox { 
    border: 1px solid #E5E7EB; 
    border-radius: 6px; 
    background-color: #F8FAFC; 
}

/* SCROLL BARS */
QScrollBar { background: #F1F5F9; border: none; }
QScrollBar:vertical { width: 12px; margin: 0px; }
QScrollBar::handle:vertical { background: #CBD5E1; min-height: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #94A3B8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal { height: 12px; margin: 0px; }
QScrollBar::handle:horizontal { background: #CBD5E1; min-width: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:horizontal:hover { background: #94A3B8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QAbstractScrollArea::corner { background: transparent; }

/* HEADER & SIDEBAR */
QFrame#Header { background-color: #FFFFFF; border-bottom: 1px solid #E5E7EB; }
QFrame#Sidebar { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
QLabel#HeaderTitle { color: #1F2937; font-size: 20px; font-weight: bold; }
QLabel#HeaderSubtitle { color: #6B7280; font-size: 13px; }
QLabel#SectionTitle { color: #111827; font-weight: bold; font-size: 14px; padding-top: 10px; padding-bottom: 5px; }

/* INPUTS */
QLineEdit, QComboBox, QAbstractSpinBox, QSpinBox, QDoubleSpinBox { 
    border: 1px solid #D1D5DB; 
    border-radius: 4px; 
    padding: 6px; 
    background-color: #FFFFFF; 
    color: #374151; 
    selection-background-color: #10B981;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QComboBox:focus, QAbstractSpinBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { 
    border: 2px solid #3B82F6; 
}
QComboBox::drop-down { border: 0px; }
QComboBox QAbstractItemView { background-color: #FFFFFF; color: #374151; selection-background-color: #EFF6FF; selection-color: #374151; }

/* DIALOGS */
QDialog QLabel { color: #374151; }

/* BUTTONS */
QPushButton { background-color: #F3F4F6; border: 1px solid #D1D5DB; border-radius: 4px; color: #374151; padding: 6px; font-weight: bold; }
QPushButton:hover { background-color: #E5E7EB; }
QPushButton#CopyButton { background-color: #059669; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
QPushButton#CopyButton:hover { background-color: #047857; }
QPushButton#DeleteButton { background-color: #EF4444; color: white; border: none; }

/* TABLES & HEADERS */
QTableWidget { background-color: #FFFFFF; border: 1px solid #E5E7EB; gridline-color: #E5E7EB; color: #374151; alternate-background-color: #F9FAFB; }
/* Fix for dark vertical headers */
QHeaderView { background-color: #F3F4F6; }
QHeaderView::section { background-color: #F3F4F6; color: #1F2937; border: 1px solid #E5E7EB; padding: 4px; }
QTableCornerButton::section { background-color: #F3F4F6; border: 1px solid #E5E7EB; }

/* CARDS */
QFrame#StatCard { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; }
QLabel#StatTitle { color: #6B7280; font-size: 11px; font-weight: bold; text-transform: uppercase; }
QLabel#StatValue { font-size: 24px; font-weight: bold; color: #1F2937; }
QLabel#StatSub { color: #9CA3AF; font-size: 11px; }
"""

# --- DARK THEME ---
DARK_PALETTE = {
    "text_primary": "#E5E7EB",
    "text_secondary": "#9CA3AF",
    "bg_primary": "#111827",
    "bg_secondary": "#1F2937",
}

DARK_STYLESHEET = """
QMainWindow, QDialog { background-color: #111827; color: #E5E7EB; }
QWidget { font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 14px; color: #E5E7EB; }

/* TABS */
QTabWidget::pane { border: 1px solid #374151; background: #1F2937; border-radius: 4px; }
QTabBar::tab { background: #111827; border: 1px solid #374151; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #9CA3AF; font-weight: bold; }
QTabBar::tab:selected { background: #1F2937; border-bottom-color: #1F2937; color: #F3F4F6; }

/* TABS SCROLL BUTTONS */
QTabBar::scroller { width: 24px; }
QTabBar QToolButton { 
    background-color: #1F2937; 
    border: 1px solid #4B5563; 
    color: #E5E7EB; 
    border-radius: 0px;
}
QTabBar QToolButton:hover { background-color: #374151; }

/* SCROLL AREAS */
QScrollArea { background-color: transparent; border: none; }
QScrollArea > QWidget { background-color: transparent; }
QScrollArea > QWidget > QWidget { background-color: transparent; }

/* FIX: Restore Dark Backgrounds for Sidebar Boxes */
QFrame#Sidebar QScrollArea { 
    background-color: #111827; 
    border: 1px solid #4B5563; 
    border-radius: 6px;
}

QScrollArea#ExpenseBreakdownBox { 
    border: 1px solid #4B5563; 
    border-radius: 6px; 
    background-color: #111827; 
}

/* SCROLL BARS */
QScrollBar { background: #111827; border: none; }
QScrollBar:vertical { width: 12px; margin: 0px; }
QScrollBar::handle:vertical { background: #4B5563; min-height: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #6B7280; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal { height: 12px; margin: 0px; }
QScrollBar::handle:horizontal { background: #4B5563; min-width: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:horizontal:hover { background: #6B7280; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QAbstractScrollArea::corner { background: transparent; }

/* HEADER & SIDEBAR */
QFrame#Header { background-color: #000000; border-bottom: 1px solid #374151; }
QFrame#Sidebar { background-color: #1F2937; border-right: 1px solid #374151; }
QLabel#HeaderTitle { color: #FFFFFF; font-size: 20px; font-weight: bold; }
QLabel#HeaderSubtitle { color: #9CA3AF; font-size: 13px; }
QLabel#SectionTitle { color: #E5E7EB; font-weight: bold; font-size: 14px; padding-top: 10px; padding-bottom: 5px; }

/* INPUTS */
QLineEdit, QComboBox, QAbstractSpinBox, QSpinBox, QDoubleSpinBox { 
    border: 1px solid #4B5563; 
    border-radius: 4px; 
    padding: 6px; 
    background-color: #374151; 
    color: #F3F4F6; 
    selection-background-color: #10B981;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QComboBox:focus, QAbstractSpinBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { 
    border: 2px solid #3B82F6; 
}
QComboBox::drop-down { border: 0px; }
QComboBox QAbstractItemView { background-color: #374151; color: #F3F4F6; selection-background-color: #4B5563; selection-color: #FFFFFF; }

/* DIALOGS */
QDialog QLabel { color: #E5E7EB; }

/* BUTTONS */
QPushButton { background-color: #374151; border: 1px solid #4B5563; border-radius: 4px; color: #E5E7EB; padding: 6px; font-weight: bold; }
QPushButton:hover { background-color: #4B5563; }
QPushButton#CopyButton { background-color: #059669; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
QPushButton#CopyButton:hover { background-color: #047857; }
QPushButton#DeleteButton { background-color: #EF4444; color: white; border: none; }

/* TABLES & HEADERS */
QTableWidget { background-color: #1F2937; border: 1px solid #4B5563; gridline-color: #4B5563; color: #E5E7EB; alternate-background-color: #111827; }
/* Fix for vertical headers */
QHeaderView { background-color: #111827; }
QHeaderView::section { background-color: #111827; color: #E5E7EB; border: 1px solid #4B5563; padding: 4px; }
QTableCornerButton::section { background-color: #111827; border: 1px solid #4B5563; }

/* CARDS */
QFrame#StatCard { background-color: #1F2937; border: 1px solid #374151; border-radius: 8px; }
QLabel#StatTitle { color: #9CA3AF; font-size: 11px; font-weight: bold; text-transform: uppercase; }
QLabel#StatValue { font-size: 24px; font-weight: bold; color: #F3F4F6; }
QLabel#StatSub { color: #6B7280; font-size: 11px; }
"""

THEMES = {
    "Light": Theme("Light", LIGHT_STYLESHEET, LIGHT_PALETTE),
    "Dark": Theme("Dark", DARK_STYLESHEET, DARK_PALETTE)
}
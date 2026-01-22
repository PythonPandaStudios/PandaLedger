class Theme:
    def __init__(self, name, stylesheet, palette):
        self.name = name
        self.stylesheet = stylesheet
        self.palette = palette

# --- LIGHT THEME ---
LIGHT_PALETTE = {
    "text_primary": "#374151",
    "text_secondary": "#6B7280",
    "text_alt_row": "#374151",
    "bg_alt_row": "#F8FAFC",
    "success": "#059669",
    "success_light": "#10B981",
    "danger": "#DC2626",
    "danger_light": "#EF4444",
    "info": "#2563EB",
    "info_light": "#3B82F6",
    "chart_gross": "#1F2937",
    "table_grid": "#E5E7EB"
}

LIGHT_STYLESHEET = """
QMainWindow { background-color: #F9FAFB; }
QWidget { font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 14px; color: #374151; }

/* TABS */
QTabWidget::pane { border: 1px solid #E5E7EB; background: white; border-radius: 4px; }
QTabBar::tab { background: #F3F4F6; border: 1px solid #E5E7EB; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #6B7280; font-weight: bold; }
QTabBar::tab:selected { background: #FFFFFF; border-bottom-color: #FFFFFF; color: #1F2937; }
QTabBar QToolButton { background-color: #F3F4F6; border: 1px solid #E5E7EB; color: #374151; }
QTabBar QToolButton:hover { background-color: #E5E7EB; }

/* FIX: Tab Internal Scroll Area */
QTabWidget QScrollArea { background-color: transparent; border: none; }
QTabWidget QScrollArea > QWidget > QWidget { background-color: transparent; }

/* RIGHT PANEL BOX (The new border for Expense Breakdown) */
QScrollArea#ExpenseBreakdownBox { 
    border: 1px solid #E5E7EB; 
    border-radius: 6px; 
    background-color: #F8FAFC; 
}

/* SCROLL BARS */
QScrollBar:vertical { border: none; background: #F1F5F9; width: 12px; margin: 0px; }
QScrollBar::handle:vertical { background: #CBD5E1; min-height: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #94A3B8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { border: none; background: #F1F5F9; height: 12px; margin: 0px; }
QScrollBar::handle:horizontal { background: #CBD5E1; min-width: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:horizontal:hover { background: #94A3B8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

/* HEADER */
QFrame#Header { background-color: #FFFFFF; border-bottom: 1px solid #E5E7EB; }
QFrame#Header QLabel { color: #1F2937; }
QLabel#HeaderTitle { color: #1F2937; font-size: 20px; font-weight: bold; }
QLabel#HeaderSubtitle { color: #6B7280; font-size: 13px; }

/* SIDEBAR */
QFrame#Sidebar { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
QLabel#SectionTitle { color: #111827; font-weight: bold; font-size: 14px; padding-top: 10px; padding-bottom: 5px; }
QFrame#Sidebar QScrollArea { background-color: #F8FAFC; border: 1px solid #E5E7EB; border-radius: 6px; }
QFrame#Sidebar QScrollArea > QWidget > QWidget { background-color: transparent; }

/* INPUTS */
QLineEdit { border: 1px solid #D1D5DB; border-radius: 4px; padding: 6px; background-color: #FFFFFF; color: #374151; selection-background-color: #10B981; }
QLineEdit:focus { border: 2px solid #3B82F6; }
QComboBox { background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 4px; padding: 5px; color: #374151; }
QComboBox::drop-down { border: 0px; background-color: transparent; }
QComboBox QAbstractItemView { background-color: #FFFFFF; color: #374151; selection-background-color: #EFF6FF; selection-color: #1F2937; }

/* BUTTONS */
QPushButton#AddButton { background-color: #F3F4F6; border: 1px solid #D1D5DB; border-radius: 4px; color: #374151; padding: 6px; font-weight: bold; }
QPushButton#AddButton:hover { background-color: #E5E7EB; }
QPushButton#CopyButton { background-color: #059669; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton#CopyButton:hover { background-color: #047857; }
QPushButton#DeleteButton { background-color: #EF4444; color: white; border: none; border-radius: 4px; font-weight: bold; }

/* TABLE */
QTableWidget { background-color: #FFFFFF; border: 1px solid #E5E7EB; gridline-color: #E5E7EB; color: #374151; selection-background-color: #EFF6FF; selection-color: #1F2937; alternate-background-color: #F9FAFB; }
QHeaderView::section { background-color: #F3F4F6; padding: 8px; border: 1px solid #E5E7EB; font-weight: bold; color: #1F2937; }
QTableWidget::item { border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB; }

/* CARDS */
QFrame#StatCard { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; }
QLabel#StatTitle { color: #6B7280; font-size: 11px; font-weight: bold; text-transform: uppercase; }
QLabel#StatValue { font-size: 24px; font-weight: bold; color: #1F2937; }
QLabel#StatSub { color: #9CA3AF; font-size: 11px; }

/* MONTHLY SUMMARY */
QFrame#MonthSummaryBox { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; }
QLabel#MonthBigLabel { font-size: 16px; font-weight: bold; color: #1F2937; }
"""

# --- DARK THEME ---
DARK_PALETTE = {
    "text_primary": "#E5E7EB",
    "text_secondary": "#9CA3AF",
    "text_alt_row": "#E5E7EB",
    "bg_alt_row": "#374151",
    "success": "#34D399",
    "success_light": "#6EE7B7",
    "danger": "#F87171",
    "danger_light": "#FCA5A5",
    "info": "#60A5FA",
    "info_light": "#93C5FD",
    "chart_gross": "#F3F4F6",
    "table_grid": "#4B5563"
}

DARK_STYLESHEET = """
QMainWindow { background-color: #111827; }
QWidget { font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 14px; color: #E5E7EB; }

/* TABS */
QTabWidget::pane { border: 1px solid #374151; background: #1F2937; border-radius: 4px; }
QTabBar::tab { background: #111827; border: 1px solid #374151; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #9CA3AF; font-weight: bold; }
QTabBar::tab:selected { background: #1F2937; border-bottom-color: #1F2937; color: #F3F4F6; }
QTabBar QToolButton { background-color: #1F2937; border: 1px solid #374151; color: #E5E7EB; }
QTabBar QToolButton:hover { background-color: #374151; }

/* FIX: Tab Internal Scroll Area */
QTabWidget QScrollArea { background-color: transparent; border: none; }
QTabWidget QScrollArea > QWidget > QWidget { background-color: transparent; }

/* RIGHT PANEL BOX (The new border for Expense Breakdown) */
QScrollArea#ExpenseBreakdownBox { 
    border: 1px solid #4B5563; 
    border-radius: 6px; 
    background-color: #111827; 
}

/* SCROLL BARS */
QScrollBar:vertical { border: none; background: #111827; width: 12px; margin: 0px; }
QScrollBar::handle:vertical { background: #4B5563; min-height: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #6B7280; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { border: none; background: #111827; height: 12px; margin: 0px; }
QScrollBar::handle:horizontal { background: #4B5563; min-width: 20px; border-radius: 6px; margin: 2px; }
QScrollBar::handle:horizontal:hover { background: #6B7280; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

/* HEADER */
QFrame#Header { background-color: #000000; border-bottom: 1px solid #374151; }
QFrame#Header QLabel { color: #FFFFFF; }
QLabel#HeaderTitle { color: #FFFFFF; font-size: 20px; font-weight: bold; }
QLabel#HeaderSubtitle { color: #9CA3AF; font-size: 13px; }

/* SIDEBAR */
QFrame#Sidebar { background-color: #1F2937; border-right: 1px solid #374151; }
QLabel#SectionTitle { color: #E5E7EB; font-weight: bold; font-size: 14px; padding-top: 10px; padding-bottom: 5px; }
QFrame#Sidebar QScrollArea { background-color: #111827; border: 1px solid #4B5563; border-radius: 6px; }
QFrame#Sidebar QScrollArea > QWidget > QWidget { background-color: transparent; }

/* INPUTS */
QLineEdit { border: 1px solid #4B5563; border-radius: 4px; padding: 6px; background-color: #374151; color: #F3F4F6; selection-background-color: #10B981; }
QLineEdit:focus { border: 2px solid #3B82F6; }
QComboBox { background-color: #374151; border: 1px solid #4B5563; border-radius: 4px; padding: 5px; color: #F3F4F6; }
QComboBox::drop-down { border: 0px; background-color: transparent; }
QComboBox QAbstractItemView { background-color: #374151; color: #F3F4F6; selection-background-color: #4B5563; selection-color: #FFFFFF; }

/* BUTTONS */
QPushButton#AddButton { background-color: #374151; border: 1px solid #4B5563; border-radius: 4px; color: #E5E7EB; padding: 6px; font-weight: bold; }
QPushButton#AddButton:hover { background-color: #4B5563; }
QPushButton#CopyButton { background-color: #059669; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton#CopyButton:hover { background-color: #047857; }
QPushButton#DeleteButton { background-color: #EF4444; color: white; border: none; border-radius: 4px; font-weight: bold; }

/* TABLE */
QTableWidget { background-color: #1F2937; border: 1px solid #4B5563; gridline-color: #4B5563; color: #E5E7EB; selection-background-color: #374151; selection-color: #FFFFFF; alternate-background-color: #111827; }
QHeaderView::section { background-color: #111827; padding: 8px; border: 1px solid #4B5563; font-weight: bold; color: #E5E7EB; }
QTableWidget::item { border-right: 1px solid #4B5563; border-bottom: 1px solid #4B5563; }

/* CARDS */
QFrame#StatCard { background-color: #1F2937; border: 1px solid #374151; border-radius: 8px; }
QLabel#StatTitle { color: #9CA3AF; font-size: 11px; font-weight: bold; text-transform: uppercase; }
QLabel#StatValue { font-size: 24px; font-weight: bold; color: #F3F4F6; }
QLabel#StatSub { color: #6B7280; font-size: 11px; }

/* MONTHLY SUMMARY */
QFrame#MonthSummaryBox { background-color: #111827; border: 1px solid #374151; border-radius: 6px; }
QLabel#MonthBigLabel { font-size: 16px; font-weight: bold; color: #F3F4F6; }
"""

THEMES = {
    "Light": Theme("Light", LIGHT_STYLESHEET, LIGHT_PALETTE),
    "Dark": Theme("Dark", DARK_STYLESHEET, DARK_PALETTE)
}
import os
import sys
import time
import sqlite3
import ctypes
from PySide6.QtWidgets import QApplication, QSplashScreen, QProgressBar
from PySide6.QtGui import QColor, QFont, QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt, QRect

# Import our new MVC Controller and necessary constants
from controllers.main_controller import MainController
from models.database import DB_FILE
from views.theme_manager import THEMES

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    BASE_PATH = sys._MEIPASS
    ASSET_DIR = os.path.join(BASE_PATH, "assets")
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_PATH = os.path.dirname(APP_DIR)
    ASSET_DIR = os.path.join(BASE_PATH, "assets")

ICON_PATH = os.path.join(ASSET_DIR, "PandaLedger_256.png")

def show_splash(theme_palette):
    bg_color, text_color = QColor(theme_palette["bg_primary"]), QColor(theme_palette["text_primary"])
    pixmap = QPixmap(500, 300); pixmap.fill(bg_color)
    painter = QPainter(pixmap); painter.setPen(text_color); painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
    painter.drawText(QRect(0, 50, 500, 50), Qt.AlignCenter, "PandaLedger")
    painter.setFont(QFont("Segoe UI", 12)); painter.drawText(QRect(0, 100, 500, 30), Qt.AlignCenter, "PythonPandaStudios")
    painter.end()
    
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    progress_bar = QProgressBar(splash); progress_bar.setGeometry(50, 220, 400, 20); progress_bar.setValue(0)
    is_dark = bg_color.lightness() < 128
    border_color = "#374151" if is_dark else "#D1D5DB"
    progress_bar.setStyleSheet(f"QProgressBar {{ border: 1px solid {border_color}; border-radius: 5px; text-align: center; color: {'white' if is_dark else 'black'}; }} QProgressBar::chunk {{ background-color: #3B82F6; }}")
    
    splash.show()
    QApplication.processEvents()
    time.sleep(0.3)
    
    steps = ["Database Check", "Config Load", "Theme Selection", "Ready"]
    for i, step in enumerate(steps):
        progress_bar.setValue((i + 1) * 25)
        splash.showMessage(f"  {step}", Qt.AlignBottom | Qt.AlignLeft, text_color)
        QApplication.processEvents()
        time.sleep(0.3)
    return splash

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Panda Ledger")
    app.setOrganizationName("Python Panda Studios")

    print(f"DATABASE LOCATION: {DB_FILE}")
    
    if os.path.exists(ICON_PATH): 
        app.setWindowIcon(QIcon(ICON_PATH))
        
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('pythonpandastudios.pandaledger.1.0')
    
    # Check current theme for splash screen colors
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
        cursor.execute("SELECT value FROM config WHERE key='theme'")
        row = cursor.fetchone()
        saved_theme = row[0] if row else "Light"
        
    splash = show_splash(THEMES[saved_theme].palette)
    
    # Initialize the entire MVC application via the Controller
    controller = MainController()
    
    splash.finish(controller.view)
    controller.show()
    
    sys.exit(app.exec())
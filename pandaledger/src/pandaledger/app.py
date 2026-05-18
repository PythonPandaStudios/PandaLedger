import toga
from toga.style import Pack
from toga.style.pack import COLUMN

# Import the database module to trigger the initialization and path resolution
from pandaledger.models import database 

class PandaLedger(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        main_box = toga.Box(style=Pack(direction=COLUMN))
        
        self.main_window.content = main_box
        self.main_window.show()

def main():
    return PandaLedger()
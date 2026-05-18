import toga
from toga.style import Pack
from toga.style.pack import COLUMN

class PandaLedger(toga.App):
    def startup(self):
        """
        Construct and show the Toga application.
        This serves as the foundational skeleton for the PandaLedger UI.
        """
        # Define the main window using the formal name from pyproject.toml
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Create a basic Box layout to hold future components
        main_box = toga.Box(style=Pack(direction=COLUMN))
        
        # Assign the layout to the main window and display it
        self.main_window.content = main_box
        self.main_window.show()

def main():
    return PandaLedger()
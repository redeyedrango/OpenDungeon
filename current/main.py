import sys
import os
from dotenv import load_dotenv
from PyQt5.QtGui import QIcon

# Load environment variables before anything else
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from game_manager import GameManager

def main():
    # Verify API key is loaded
    if not os.getenv('OPENROUTER_API_KEY'):
        print("Warning: OPENROUTER_API_KEY not found in environment variables!")
    
    app = QApplication(sys.argv)
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    game_manager = GameManager()
    window = MainWindow(game_manager)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QLabel, QScrollArea, QFrame, QApplication,
                           QSizePolicy, QMessageBox, QAbstractScrollArea, QInputDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QPixmap
from enum import Enum
import traceback
from PyQt5 import uic
import random
import os
from scene_image_handler import SceneImageHandler

class GameState(Enum):
    WAITING_FOR_INPUT = 1
    PROCESSING = 2
    WAITING_FOR_ROLL = 3
    ERROR = 4

class GameLogEntry(QFrame):
    def __init__(self, text, entry_type="normal", parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setText(text)
        self.text_area.setMinimumHeight(100)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.text_area)
        
        # Add image generation button for DM messages
        if entry_type == "dm":
            self.image_layout = QVBoxLayout()
            self.generate_image_btn = QPushButton("🎨 Generate Scene Image")
            self.generate_image_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2980B9;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px;
                    max-width: 200px;
                }
                QPushButton:hover {
                    background-color: #3498DB;
                }
            """)
            self.image_layout.addWidget(self.generate_image_btn)
            
            # Add image display label (hidden initially)
            self.image_label = QLabel()
            self.image_label.setVisible(False)
            self.image_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    border: 2px solid #203D72;
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
            self.image_layout.addWidget(self.image_label)
            self.main_layout.addLayout(self.image_layout)
        
        # Apply styles based on entry type
        if entry_type == "dm":
            self.setStyleSheet("""
                QFrame {
                    background-color: #203D72;
                    border: 2px solid #334970;
                    margin: 5px;
                }
                QTextEdit {
                    color: #ECF0F1;
                    background-color: transparent;
                    border: none;
                    font-family: 'MedievalSharp';
                    font-size: 18px;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #334970;
                    border: 2px solid #203D72;
                    margin: 5px;
                }
                QTextEdit {
                    color: #ECF0F1;
                    background-color: transparent;
                    border: none;
                    font-family: 'Poppins', sans-serif;
                    font-size: 14px;
                    padding: 10px;
                }
            """)

class PlayGameTab(QWidget):
    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.last_dm_message = ""
        
        # Load UI
        uic.loadUi('current/ui/designer/play_game_tab.ui', self)
        
        # Connect signals
        self.submitBtn.clicked.connect(self.submit_action)
        self.speakBtn.clicked.connect(self.speak_last_message)
        self.stopBtn.clicked.connect(self.toggle_volume)  # Changed to toggle_volume
        self.rollDiceBtn.clicked.connect(self.roll_dice)
        self.saveGameBtn.clicked.connect(self.save_game)
        self.loadGameBtn.clicked.connect(self.load_game)
        
        # Update button text to match settings tab
        self.stopBtn.setText("🔊 Volume")
        
        # Apply styles
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ECF0F1;
            }
            QTextEdit {
                background-color: #334970;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: #ECF0F1;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2980B9;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3498DB;
            }
        """)
        
        # Initialize scene image handler
        self.scene_image_handler = SceneImageHandler(game_manager)

    def add_message(self, text: str, is_dm: bool = False):
        entry = GameLogEntry(text, "dm" if is_dm else "normal")
        if is_dm:
            self.last_dm_message = text
            # Connect image generation button if it's a DM message
            entry.generate_image_btn.clicked.connect(
                lambda: self.generate_scene_image(entry, text)
            )
        self.gameLogLayout.addWidget(entry)

    def generate_scene_image(self, entry: GameLogEntry, scene_text: str):
        """Generate and display an image for the given scene"""
        try:
            entry.generate_image_btn.setEnabled(False)
            entry.generate_image_btn.setText("Generating image...")
            
            # Generate the image
            image_path = self.scene_image_handler.generate_scene_image(scene_text)
            
            if image_path and os.path.exists(image_path):
                # Load and display the image
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                entry.image_label.setPixmap(scaled_pixmap)
                entry.image_label.setVisible(True)
            else:
                QMessageBox.warning(self, "Error", "Failed to generate scene image")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error generating scene image: {str(e)}")
            
        finally:
            entry.generate_image_btn.setEnabled(True)
            entry.generate_image_btn.setText("🎨 Generate Scene Image")

    def submit_action(self):
        action = self.inputArea.toPlainText().strip()
        if action:
            self.add_message(f"Player: {action}")
            response = self.game_manager.process_player_action(action)
            if response:
                self.add_message(response, is_dm=True)
            self.inputArea.clear()

    def speak_last_message(self):
        """Speak the last DM message using TTS"""
        if hasattr(self.game_manager, 'tts_manager') and self.last_dm_message:
            try:
                self.game_manager.tts_manager.speak(self.last_dm_message)
                self.update_button_states()
            except Exception as e:
                print(f"Error with TTS: {e}")
                QMessageBox.warning(self, "TTS Error", "There was an error with text-to-speech. Please check your settings.")

    def toggle_volume(self):
        """Toggle TTS volume between full and muted"""
        try:
            is_muted = self.game_manager.tts_manager.toggle_mute()
            self.stopBtn.setText("🔈 Unmute" if is_muted else "🔊 Volume")
            self.update_button_states()
        except Exception as e:
            print(f"Error toggling volume: {e}")
            self.update_button_states()

    def update_button_states(self):
        """Update button states based on TTS status"""
        is_speaking = self.game_manager.tts_manager.speaking
        is_muted = self.game_manager.tts_manager.muted
        
        self.speakBtn.setEnabled(not is_speaking)
        self.stopBtn.setEnabled(True)
        self.stopBtn.setText("🔈 Unmute" if is_muted else "🔊 Volume")

    def roll_dice(self):
        """Roll a d20 and send the result as an action to the DM"""
        dice_roll = random.randint(1, 20)
        self.add_message(f"🎲 You rolled a {dice_roll}!", is_dm=False)
        
        # Send the roll as an action to the DM
        action = f"I rolled a {dice_roll} on my d20."
        response = self.game_manager.process_player_action(action)
        if response:
            self.add_message(response, is_dm=True)

    def save_game(self):
        """Save current game state"""
        try:
            save_name, ok = QInputDialog.getText(
                self, 
                "Save Game", 
                "Enter a name for this save:",
                text="SaveGame"
            )
            
            if ok and save_name:
                filepath = self.game_manager.save_game_state(save_name)
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Game saved successfully as {save_name}!"
                )
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Failed to save game: {str(e)}"
            )

    def load_game(self):
        """Load a saved game state"""
        try:
            saved_games = self.game_manager.list_saved_games()
            if not saved_games:
                QMessageBox.information(
                    self, 
                    "Info", 
                    "No saved games found!"
                )
                return
                
            # Create list of save files with timestamps
            save_options = [
                f"{save['name']} ({save['timestamp']})" 
                for save in saved_games
            ]
            
            selection, ok = QInputDialog.getItem(
                self,
                "Load Game",
                "Select a save to load:",
                save_options,
                0,
                False
            )
            
            if ok and selection:
                # Find selected save file
                selected_save = next(
                    save for save in saved_games 
                    if f"{save['name']} ({save['timestamp']})" == selection
                )
                
                # Clear existing messages before loading
                self.clear_messages()
                
                # Load the save file
                if self.game_manager.load_game_state(selected_save['filename']):
                    # Add loading message
                    self.add_message("Loading your saved game...", is_dm=True)
                    
                    # The recap will be the last response in game_state['responses']
                    if self.game_manager.game_state and self.game_manager.game_state.get('responses'):
                        for response in self.game_manager.game_state['responses']:
                            self.add_message(response, is_dm=True)
                    
                    QMessageBox.information(
                        self, 
                        "Success", 
                        "Game loaded successfully!"
                    )
                    
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Failed to load game: {str(e)}"
            )

    def clear_messages(self):
        """Clear all messages from the game log"""
        while self.gameLogLayout.count():
            item = self.gameLogLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

import sys
import os
import requests
import re
import html
from dotenv import load_dotenv
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPalette, QColor, QFont

load_dotenv()

KAGI_API_TOKEN = os.environ.get("KAGI_API_TOKEN")
KAGI_API_URL = "https://kagi.com/api/v0/fastgpt"
WINDOW_TITLE = "Kagi FastGPT"
APP_CLASS_NAME = "KagiChatPopup"

DARK_BACKGROUND = "#2e3440"
LIGHT_BACKGROUND = "#4c566a"
TEXT_COLOR = "#eceff4"
ACCENT_COLOR = "#88c0d0"
INPUT_BACKGROUND = "#3b4252"
BORDER_COLOR = "#434c5e"

def simple_markdown_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = text.replace('\n', '<br>')
    return text

def format_references_html(references):
    if not references:
        return ""
    ref_html = "<br><br><b>References:</b>"
    for i, ref in enumerate(references):
        raw_title = ref.get('title', 'N/A')
        unescaped_title = html.unescape(raw_title)
        safe_title = html.escape(unescaped_title)
        safe_url = html.escape(ref.get('url', '#'))
        ref_html += f"<br>{i+1}. <a href=\"{safe_url}\">{safe_title}</a>"
    return ref_html

STYLESHEET = f"""
QWidget {{
    background-color: {DARK_BACKGROUND};
    color: {TEXT_COLOR};
    font-family: 'Cantarell', sans-serif; /* Example font */
    font-size: 11pt;
}}
QTextEdit#chat_display {{
    background-color: {DARK_BACKGROUND};
    border: none;
}}
QLineEdit#input_field {{
    background-color: {INPUT_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    padding: 8px;
    border-radius: 4px;
    font-size: 11pt;
}}
QLineEdit#input_field:focus {{
    border: 1px solid {ACCENT_COLOR};
}}
QPushButton#send_button {{
    background-color: {ACCENT_COLOR};
    color: {DARK_BACKGROUND};
    padding: 8px 15px;
    border: none;
    border-radius: 8px;
    font-weight: bold;
}}
QPushButton#send_button:hover {{
    background-color: #a0d9e8; /* Lighter accent */
}}
QPushButton#send_button:pressed {{
    background-color: #7aa6b3; /* Darker accent */
}}
QScrollArea {{
    border: none;
}}
QScrollBar:vertical {{
    border: none;
    background: {LIGHT_BACKGROUND};
    width: 10px;
    margin: 0px 0px 0px 0px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT_COLOR};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QLabel#error_label {{
    color: #bf616a; /* Nord Aurora Red */
    padding: 5px;
}}
/* Style for links within messages */
QLabel a {{
    color: {ACCENT_COLOR};
    text-decoration: underline;
}}
"""

class KagiChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setObjectName(APP_CLASS_NAME)

        if not KAGI_API_TOKEN:
            print("Error: KAGI_API_TOKEN environment variable not set.")
            self.setup_error_ui("KAGI_API_TOKEN not set!")
            return

        self.setup_ui()
        self.apply_styles()

    def setup_error_ui(self, error_message):
        self.layout = QVBoxLayout(self)
        error_label = QLabel(f"Error: {error_message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet(f"color: #bf616a; font-size: 14pt; padding: 20px;")
        self.layout.addWidget(error_label)
        self.setMinimumSize(400, 100)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("chat_scroll_area") # For potential specific styling

        self.chat_display_container = QWidget() # Container for the layout
        self.chat_layout = QVBoxLayout(self.chat_display_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)
        self.chat_layout.setSpacing(12)

        self.scroll_area.setWidget(self.chat_display_container)

        self.input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setObjectName("input_field")
        self.input_field.setPlaceholderText("Ask Kagi...")
        self.input_field.returnPressed.connect(self.send_query) # Send on Enter

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("send_button")
        self.send_button.clicked.connect(self.send_query)

        self.input_layout.addWidget(self.input_field)
        self.input_layout.addWidget(self.send_button)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.layout.addWidget(self.scroll_area, stretch=1)
        self.layout.addWidget(self.error_label)
        self.layout.addLayout(self.input_layout)

        self.setMinimumSize(500, 400)

    def apply_styles(self):
        self.setStyleSheet(STYLESHEET)
        self.chat_display_container.setStyleSheet(f"background-color: {DARK_BACKGROUND};")


    def add_message(self, text, is_user=True):
        display_text = text
        if is_user:
            display_text = html.escape(text)
            display_text = display_text.replace('\n', '<br>')
        else:
            display_text = text

        message_label = QLabel(display_text)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_label.setOpenExternalLinks(True)

        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 8, 10, 8)
        frame_layout.addWidget(message_label)
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.MinimumExpanding)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)

        if is_user:
            frame.setStyleSheet(f"background-color: {INPUT_BACKGROUND}; border-radius: 12px;")
            hbox.addStretch(1)
            hbox.addWidget(frame, stretch=0)
            self.chat_layout.addLayout(hbox)
        else:
            frame.setStyleSheet(f"background-color: {LIGHT_BACKGROUND}; border-radius: 12px;")
            hbox.addWidget(frame, stretch=0)
            hbox.addStretch(1)
            self.chat_layout.addLayout(hbox)


        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def show_error(self, message):
        self.error_label.setText(f"Error: {message}")
        self.error_label.show()

    def clear_error(self):
        self.error_label.hide()
        self.error_label.setText("")

    @Slot()
    def send_query(self):
        query_text = self.input_field.text().strip()
        if not query_text:
            return

        self.clear_error()
        self.add_message(f"You: {query_text}", is_user=True)
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        QApplication.processEvents()

        thinking_label = QLabel("Kagi is thinking...")
        thinking_label.setObjectName("thinking_label")
        thinking_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        thinking_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-style: italic; margin-right: 50px; padding: 8px;")
        self.chat_layout.addWidget(thinking_label, alignment=Qt.AlignmentFlag.AlignLeft)
        QApplication.processEvents()


        try:
            headers = {'Authorization': f'Bot {KAGI_API_TOKEN}'}
            data = {
                "query": query_text,
                "web_search": True
            }
            response = requests.post(KAGI_API_URL, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            response_data = response.json()

            think_widget = self.chat_display_container.findChild(QLabel, "thinking_label")
            if think_widget:
                think_widget.deleteLater()


            if response_data.get("error"):
                error_info = response_data["error"]
                self.show_error(f"API Error {error_info.get('code')}: {error_info.get('msg')}")
            elif "data" in response_data and "output" in response_data["data"]:
                output = response_data["data"]["output"]
                references = response_data["data"].get("references", [])

                kagi_prefix = "<b>Kagi:</b><br>"
                unescaped_output = html.unescape(output)
                safe_output = html.escape(unescaped_output)
                formatted_output = simple_markdown_to_html(safe_output)
                formatted_references = format_references_html(references)

                response_html = kagi_prefix + formatted_output + formatted_references

                self.add_message(response_html, is_user=False)
            else:
                self.show_error("Unexpected response format from Kagi API.")

        except requests.exceptions.RequestException as e:
            think_widget = self.chat_display_container.findChild(QLabel, "thinking_label")
            if think_widget:
                think_widget.deleteLater()
            self.show_error(f"Network or API request error: {e}")
        except Exception as e:
            think_widget = self.chat_display_container.findChild(QLabel, "thinking_label")
            if think_widget:
                think_widget.deleteLater()
            self.show_error(f"An unexpected error occurred: {e}")
        finally:
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
            self.input_field.setFocus()
            QApplication.processEvents()
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )

if __name__ == "__main__":
    load_dotenv()
    KAGI_API_TOKEN = os.environ.get("KAGI_API_TOKEN")

    if not KAGI_API_TOKEN:
        print("Fatal Error: KAGI_API_TOKEN environment variable is not set and not found in .env file.")
        print("Please set it either as an environment variable or in a .env file in the same directory as main.py:")
        print(".env file content: KAGI_API_TOKEN=your_token_here")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setApplicationDisplayName(WINDOW_TITLE)

    window = KagiChatWindow()

    if KAGI_API_TOKEN:
       window.show()
    else:
       error_window = window
       error_window.show()


    sys.exit(app.exec()) 
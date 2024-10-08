from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QApplication, QScrollArea, QProgressBar
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QUrl, QTimer
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from dotenv import load_dotenv
import os
import sys
import uuid
sys.path.append('.')
from openai import OpenAI
import io

class ImageGenerationThread(QThread):
    image_generated = Signal(str)

    def __init__(self, client, prompt):
        super().__init__()
        self.client = client
        self.prompt = prompt

    def run(self):
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=self.prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            self.image_generated.emit(image_url)
        except Exception as e:
            print(f"Error generating image: {str(e)}")

class VisualDesignTab(QWidget):
    visual_design_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_api_key()
        self.current_stream = None
        self.stream_buffer = ""
        self.load_system_prompt()
        self.client = None
        self.load_initial_visual_design()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_image_downloaded)

    def load_initial_visual_design(self):
        try:
            with open('visual_design.md', 'r', encoding='utf-8') as f:
                initial_visual_design = f.read()
            self.result_area.setText(initial_visual_design)
        except FileNotFoundError:
            self.chat_area.append("Warning: visual_design.md file not found. Starting with empty visual design.")

    def initUI(self):
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # Chat area
        chat_layout = QVBoxLayout()
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.textChanged.connect(lambda: self.chat_area.ensureCursorVisible())
        self.chat_area.append("Hey there! I'm Pixel, your visual design virtuoso. Welcome to the Visual Design Tab! Here you can work on the visual aspects of your project. Start by describing your ideas for visuals or ask for suggestions in the input field below.")
        chat_layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        chat_layout.addLayout(input_layout)
        self.layout.addLayout(chat_layout)

        # Visual design display area
        self.result_area = QTextEdit()
        self.result_area.textChanged.connect(self.save_visual_design)
        self.result_area.textChanged.connect(lambda: self.result_area.ensureCursorVisible())
        self.layout.addWidget(self.result_area)

        # Image display area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.image_container = QWidget()
        self.image_layout = QVBoxLayout(self.image_container)
        scroll_area.setWidget(self.image_container)

        self.layout.addWidget(scroll_area)

        # Add spinner
        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner_movie = QMovie("spinner.gif")  # Make sure to have a spinner.gif file in your project directory
        self.spinner.setMovie(self.spinner_movie)
        self.spinner.hide()
        self.image_layout.addWidget(self.spinner)

    def save_visual_design(self):
        with open('visual_design.md', 'w', encoding='utf-8') as f:
            f.write(self.result_area.toPlainText())

    def load_api_key(self):
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("Error: OpenAI API key not found in .env file. Please add OPENAI_API_KEY to your .env file.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.client.models.list()  # Test the client to ensure it's working
            except Exception as e:
                print(f"Error initializing OpenAI client: {str(e)}")
                print("Please check your API key in the .env file")
                self.client = None

    def load_system_prompt(self):
        try:
            with open('prompts/visual_design.md', 'r', encoding='utf-8') as f:
                visual_design_prompt = f.read()
            
            with open('concept.md', 'r', encoding='utf-8') as f:
                concept_content = f.read()
            
            self.system_prompt = f"{visual_design_prompt}\n\nContext from concept.md:\n{concept_content}"
        except FileNotFoundError as e:
            self.system_prompt = "You are a creative assistant to help develop visual designs for songs."
            self.chat_area.append(f"Warning: File not found: {str(e)}. Using a default prompt.")

    def send_message(self):
        # Update the system prompt with the latest content
        self.load_system_prompt()
        
        user_message = self.input_field.text()

    def send_message(self):
        user_message = self.input_field.text()
        self.chat_area.append(f"You: {user_message}")
        self.input_field.clear()

        if not self.api_key:
            self.chat_area.append("Error: OpenAI API key not found. Please check your .env file.")
            return

        if self.client is None:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.chat_area.append("OpenAI client reinitialized successfully.")
            except Exception as e:
                self.chat_area.append(f"Error reinitializing OpenAI client: {str(e)}")
                return

        try:
            # Refresh the concept content
            with open('concept.md', 'r', encoding='utf-8') as f:
                concept_content = f.read()
            
            # Update the system prompt with the latest concept content
            updated_system_prompt = f"{self.system_prompt}\n\nUpdated context from concept.md:\n{concept_content}"

            self.stream_buffer = ""
            self.chat_area.append("Assistant: ")
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": updated_system_prompt},
                    {"role": "user", "content": user_message}
                ],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    self.stream_buffer += chunk.choices[0].delta.content
                    self.chat_area.insertPlainText(chunk.choices[0].delta.content)
                    QApplication.processEvents()
            self.update_visual_design(self.stream_buffer)
            
            # Generate image based on the response
            self.generate_image(self.stream_buffer)
        except Exception as e:
            self.chat_area.append(f"Error sending message: {str(e)}")
            self.chat_area.append("Please check your internet connection and the validity of your API key.")

    def update_visual_design(self, new_content):
        try:
            with open('visual_design.md', 'r', encoding='utf-8') as f:
                current_visual_design = f.read()
        except FileNotFoundError:
            current_visual_design = ""
        
        updated_visual_design = current_visual_design + "\n\n" + new_content
        self.visual_design_updated.emit(updated_visual_design)
        
        # Save the visual design to visual_design.md
        with open('visual_design.md', 'w', encoding='utf-8') as f:
            f.write(updated_visual_design)

    def generate_image(self, prompt):
        self.chat_area.append("Generating image...")
        self.spinner.show()
        self.spinner_movie.start()
        self.image_thread = ImageGenerationThread(self.client, prompt)
        self.image_thread.image_generated.connect(self.on_image_generated)
        self.image_thread.start()

    def on_image_generated(self, image_url):
        self.chat_area.append(f"Image generated: {image_url}")
        self.download_image(image_url)
        self.spinner_movie.stop()
        self.spinner.hide()

    def download_image(self, url):
        request = QNetworkRequest(QUrl(url))
        self.network_manager.get(request)

    def on_image_downloaded(self, reply):
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            
            # Créer un nouveau QLabel pour l'image
            image_label = QLabel()
            image_label.setPixmap(pixmap.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            image_label.setAlignment(Qt.AlignCenter)
            
            # Ajouter le nouveau QLabel au layout des images
            self.image_layout.addWidget(image_label)
            
            # Sauvegarder l'image
            self.save_image(data)
        else:
            self.chat_area.append(f"Error downloading image: {reply.errorString()}")

    def save_image(self, image_data):
        if not os.path.exists('images'):
            os.makedirs('images')
        
        image_name = f"visual_design_{uuid.uuid4()}.png"
        image_path = os.path.join('images', image_name)
        
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        self.chat_area.append(f"Image saved: {image_path}")

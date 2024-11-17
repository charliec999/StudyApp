import sys, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
import json, openai
from datetime import datetime
import sqlite3
from functools import partial
class ModernStudyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Study Assistant")
        self.setup_openai()
        self.setup_database()
        self.setup_styles()
        self.setup_ui()
        self.load_playlists()
    def setup_openai(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                openai.api_key = config.get('openai_api_key')
        except FileNotFoundError:
            self.show_api_key_dialog()
    def show_api_key_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("OpenAI API Key Setup")
        layout = QVBoxLayout()
        label = QLabel("Please enter your OpenAI API key:")
        api_key_input = QLineEdit()
        api_key_input.setEchoMode(QLineEdit.Password)
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_api_key(api_key_input.text(), dialog))
        layout.addWidget(label)
        layout.addWidget(api_key_input)
        layout.addWidget(save_button)
        dialog.setLayout(layout)
        dialog.exec_()
    def setup_database(self):
        self.conn = sqlite3.connect('study_app.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL, transcript TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS generated_tests (id INTEGER PRIMARY KEY, playlist_id INTEGER, questions TEXT NOT NULL, answers TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (playlist_id) REFERENCES playlists (id))''')
        self.conn.commit()
    def setup_styles(self):
        self.setStyleSheet("""QMainWindow {background-color: #0a0a0a;} QWidget {background-color: #0a0a0a; color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif;} QPushButton {background: rgba(98, 0, 238, 0.8); border: none; border-radius: 8px; color: white; padding: 12px 24px; margin: 4px; font-weight: bold; font-size: 13px;} QPushButton:hover {background: rgba(119, 34, 255, 0.9);} QTextEdit, QListWidget {background-color: rgba(30, 30, 30, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 12px; color: white; font-size: 14px;} QSplitter::handle {background-color: #2d2d2d; height: 2px; width: 2px;} QSplitter::handle:hover {background-color: #6200EE;} QGroupBox {background-color: rgba(30, 30, 30, 0.5); border: 1px solid rgba(98, 0, 238, 0.3); border-radius: 12px; margin-top: 16px; padding: 20px; font-weight: bold;} QGroupBox::title {subcontrol-origin: margin; left: 12px; padding: 0 8px; color: #6200EE;} QLineEdit {background-color: rgba(30, 30, 30, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px; color: white; font-size: 13px;} QTabWidget::pane {border: 1px solid rgba(98, 0, 238, 0.3); border-radius: 8px; background-color: rgba(30, 30, 30, 0.5);} QTabBar::tab {background-color: rgba(30, 30, 30, 0.7); border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 8px 16px; margin-right: 2px;} QTabBar::tab:selected {background-color: rgba(98, 0, 238, 0.8);}""")
    def setup_ui(self):
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.main_splitter)
        left_panel = self.setup_left_panel()
        self.main_splitter.addWidget(left_panel)
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.setup_right_top_panel())
        right_splitter.addWidget(self.setup_right_bottom_panel())
        self.main_splitter.addWidget(right_splitter)
        self.main_splitter.setSizes([600, 800])
        right_splitter.setSizes([400, 500])
        self.setMinimumSize(1400, 900)
    def setup_left_panel(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        youtube_container = QGroupBox("Video Player")
        youtube_layout = QVBoxLayout(youtube_container)
        self.web_view = QWebEngineView()
        self.web_view.setMinimumSize(640, 360)
        youtube_layout.addWidget(self.web_view)
        playlist_group = QGroupBox("Study Playlists")
        playlist_layout = QVBoxLayout(playlist_group)
        add_playlist_widget = QWidget()
        add_layout = QGridLayout(add_playlist_widget)
        self.playlist_name = QLineEdit()
        self.playlist_name.setPlaceholderText("Playlist name")
        add_layout.addWidget(self.playlist_name, 0, 0)
        self.playlist_url = QLineEdit()
        self.playlist_url.setPlaceholderText("YouTube URL")
        add_layout.addWidget(self.playlist_url, 1, 0)
        add_btn = QPushButton("Add Playlist")
        add_btn.clicked.connect(self.add_playlist)
        add_layout.addWidget(add_btn, 1, 1)
        playlist_layout.addWidget(add_playlist_widget)
        self.playlist_list = QListWidget()
        self.playlist_list.setItemDelegate(PlaylistItemDelegate())
        self.playlist_list.itemClicked.connect(self.play_playlist)
        playlist_layout.addWidget(self.playlist_list)
        ai_controls = QGroupBox("AI Tools")
        ai_controls_layout = QVBoxLayout(ai_controls)
        generate_test_btn = QPushButton("Generate Practice Test")
        generate_test_btn.clicked.connect(self.generate_test)
        ai_controls_layout.addWidget(generate_test_btn)
        summarize_btn = QPushButton("Summarize Content")
        summarize_btn.clicked.connect(self.summarize_content)
        ai_controls_layout.addWidget(summarize_btn)
        create_flashcards_btn = QPushButton("Create Flashcards")
        create_flashcards_btn.clicked.connect(self.create_flashcards)
        ai_controls_layout.addWidget(create_flashcards_btn)
        left_layout.addWidget(youtube_container)
        left_layout.addWidget(playlist_group)
        left_layout.addWidget(ai_controls)
        return left_widget
    def setup_right_top_panel(self):
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        note_controls = QHBoxLayout()
        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Note title")
        note_controls.addWidget(self.note_title)
        save_btn = QPushButton("Save Note")
        save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        save_btn.clicked.connect(self.save_note)
        note_controls.addWidget(save_btn)
        analyze_btn = QPushButton("Analyze Notes")
        analyze_btn.clicked.connect(self.ai_analyze)
        note_controls.addWidget(analyze_btn)
        top_layout.addLayout(note_controls)
        self.note_editor = QTextEdit()
        self.note_editor.setPlaceholderText("Start taking notes...")
        top_layout.addWidget(self.note_editor)
        return top_widget
    def setup_right_bottom_panel(self):
        bottom_widget = QTabWidget()
        ai_analysis_widget = QWidget()
        ai_layout = QVBoxLayout(ai_analysis_widget)
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setPlaceholderText("AI analysis and suggestions will appear here...")
        ai_layout.addWidget(self.ai_output)
        qa_widget = QWidget()
        qa_layout = QVBoxLayout(qa_widget)
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Ask a question about the content...")
        qa_layout.addWidget(self.question_input)
        ask_btn = QPushButton("Ask Question")
        ask_btn.clicked.connect(self.ask_question)
        qa_layout.addWidget(ask_btn)
        self.qa_output = QTextEdit()
        self.qa_output.setReadOnly(True)
        self.qa_output.setPlaceholderText("AI answers will appear here...")
        qa_layout.addWidget(self.qa_output)
        test_widget = QWidget()
        test_layout = QVBoxLayout(test_widget)
        self.test_display = QTextEdit()
        self.test_display.setReadOnly(True)
        test_layout.addWidget(self.test_display)
        bottom_widget.addTab(ai_analysis_widget, "AI Analysis")
        bottom_widget.addTab(qa_widget, "Q&A Assistant")
        bottom_widget.addTab(test_widget, "Practice Tests")
        return bottom_widget
    def ask_question(self):
        if not self.playlist_list.currentItem():
            QMessageBox.warning(self, "Error", "Please select a playlist first")
            return
        question = self.question_input.text()
        if not question:
            QMessageBox.warning(self, "Error", "Please enter a question")
            return
        try:
            context = self.note_editor.toPlainText()
            playlist_name = self.playlist_list.currentItem().text()
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable study assistant. Answer questions based on the provided context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ]
            )
            answer = response.choices[0].message.content
            self.qa_output.setText(f"Q: {question}\n\nA: {answer}")
            self.question_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get answer: {str(e)}")
    def generate_test(self):
        if not self.playlist_list.currentItem():
            QMessageBox.warning(self, "Error", "Please select a playlist first")
            return
        try:
            context = self.note_editor.toPlainText()
            playlist_name = self.playlist_list.currentItem().text()
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Create a practice test with 5 questions based on the provided content. Include both questions and answers."},
                    {"role": "user", "content": f"Content for {playlist_name}:\n{context}"}
                ]
            )
            test_content = response.choices[0].message.content
            self.test_display.setText(test_content)
            self.save_generated_test(playlist_name, test_content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate test: {str(e)}")
    def summarize_content(self):
        if not self.playlist_list.currentItem():
            QMessageBox.warning(self, "Error", "Please select a playlist first")
            return
        try:
            content = self.note_editor.toPlainText()
            playlist_name = self.playlist_list.currentItem().text()
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Create a concise summary of the provided content, highlighting key points and concepts."},
                    {"role": "user", "content": f"Content for {playlist_name}:\n{content}"}
                ]
            )
            summary = response.choices[0].message.content
            self.ai_output.setText(f"Summary of {playlist_name}\n\n{summary}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to summarize content: {str(e)}")
    def create_flashcards(self):
        if not self.playlist_list.currentItem():
            QMessageBox.warning(self, "Error", "Please select a playlist first")
            return
        try:
            content = self.note_editor.toPlainText()
            playlist_name = self.playlist_list.currentItem().text()
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Create a set of 10 flashcards based on the content. Format as 'Front: [question/term] | Back: [answer/definition]'"},
                    {"role": "user", "content": f"Content for {playlist_name}:\n{content}"}
                ]
            )
            flashcards = response.choices[0].message.content
            self.show_flashcards_dialog(flashcards)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create flashcards: {str(e)}")
    def show_flashcards_dialog(self, flashcards):
        dialog = FlashcardsDialog(flashcards, self)
        dialog.exec_()
    def save_generated_test(self, playlist_name, test_content):
        self.cursor.execute("SELECT id FROM playlists WHERE name = ?", (playlist_name,))
        playlist_id = self.cursor.fetchone()[0]
        parts = test_content.split("\nAnswers:\n")
        questions = parts[0]
        answers = parts[1] if len(parts) > 1 else ""
        self.cursor.execute("INSERT INTO generated_tests (playlist_id, questions, answers) VALUES (?, ?, ?)", (playlist_id, questions, answers))
        self.conn.commit()
    def save_api_key(self, api_key, dialog):
        config = {'openai_api_key': api_key}
        with open('config.json', 'w') as f:
            json.dump(config, f)
        openai.api_key = api_key
        dialog.accept()
    def add_playlist(self):
        name = self.playlist_name.text()
        url = self.playlist_url.text()
        if not name or not url:
            QMessageBox.warning(self, "Error", "Please enter both name and URL")
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            QMessageBox.warning(self, "Error", "Please enter a valid YouTube URL")
            return
        self.cursor.execute("INSERT INTO playlists (name, url) VALUES (?, ?)", (name, url))
        self.conn.commit()
        self.add_playlist_item(name, url)
        self.playlist_name.clear()
        self.playlist_url.clear()
        video_id = self.extract_video_id(url)
        if video_id:
            self.load_youtube_video(video_id)
    def extract_video_id(self, url):
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        return None
    def add_playlist_item(self, name, url):
        item = QListWidgetItem()
        item.setText(name)
        item.setData(Qt.UserRole, url)
        self.playlist_list.addItem(item)
    def load_playlists(self):
        self.cursor.execute("SELECT name, url FROM playlists")
        for name, url in self.cursor.fetchall():
            self.add_playlist_item(name, url)
    def load_youtube_video(self, video_id):
        html = f"""<html><body style="margin:0;background:#000;"><iframe width="100%" height="100%" src="https://www.youtube.com/embed/{video_id}?rel=0&autoplay=1" frameborder="0" allowfullscreen allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe></body></html>"""
        self.web_view.setHtml(html)
    def play_playlist(self, item):
        url = item.data(Qt.UserRole)
        video_id = self.extract_video_id(url)
        if video_id:
            self.load_youtube_video(video_id)
    def save_note(self):
        title = self.note_title.text()
        if not title:
            title = f"Note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not os.path.exists("notes"):
            os.makedirs("notes")
        content = self.note_editor.toPlainText()
        with open(f"notes/{title}.txt", "w", encoding="utf-8") as f:
            f.write(content)
        QMessageBox.information(self, "Success", "Note saved successfully!")
    def ai_analyze(self):
        if not openai.api_key:
            QMessageBox.warning(self, "Error", "Please set up your OpenAI API key first")
            self.show_api_key_dialog()
            return
        content = self.note_editor.toPlainText()
        if not content:
            QMessageBox.warning(self, "Error", "Please enter some notes first")
            return
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful study assistant. Analyze the student's notes and provide:\n1. Key concepts identified\n2. Areas that need clarification\n3. Suggestions for further study\n4. Learning objectives achieved"},
                    {"role": "user", "content": f"Please analyze these study notes:\n\n{content}"}
                ]
            )
            analysis = response.choices[0].message.content
            self.ai_output.setText(analysis)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"AI analysis failed: {str(e)}")
    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
    def setup_splitter_controls(self):
        self.locked = False
        lock_btn = QPushButton()
        lock_btn.setIcon(self.style().standardIcon(QStyle.SP_Lock))
        lock_btn.setFixedSize(32, 32)
        lock_btn.setToolTip("Lock/Unlock panel sizes")
        lock_btn.clicked.connect(self.toggle_splitter_lock)
        self.statusBar().addPermanentWidget(lock_btn)

    def toggle_splitter_lock(self):
        self.locked = not self.locked
        self.main_splitter.setHandleWidth(1 if self.locked else 2)
        for i in range(self.main_splitter.count()):
            handle = self.main_splitter.handle(i)
            if handle:
                handle.setEnabled(not self.locked)
        right_splitter = self.main_splitter.widget(1)
        if isinstance(right_splitter, QSplitter):
            right_splitter.setHandleWidth(1 if self.locked else 2)
            for i in range(right_splitter.count()):
                handle = right_splitter.handle(i)
                if handle:
                    handle.setEnabled(not self.locked)
class FlashcardsDialog(QDialog):
    def __init__(self, flashcards_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Study Flashcards")
        self.setMinimumSize(600, 400)
        self.flashcards = []
        for line in flashcards_content.split('\n'):
            if '|' in line:
                front, back = line.split('|')
                self.flashcards.append({'front': front.replace('Front:', '').strip(), 'back': back.replace('Back:', '').strip()})
        self.current_index = 0
        self.showing_front = True
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        self.card_display.setAlignment(Qt.AlignCenter)
        self.card_display.setMinimumHeight(200)
        layout.addWidget(self.card_display)
        controls = QHBoxLayout()
        prev_btn = QPushButton("Previous")
        prev_btn.clicked.connect(self.previous_card)
        controls.addWidget(prev_btn)
        self.flip_btn = QPushButton("Flip")
        self.flip_btn.clicked.connect(self.flip_card)
        controls.addWidget(self.flip_btn)
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(self.next_card)
        controls.addWidget(next_btn)
        layout.addLayout(controls)
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        self.update_display()
        self.setup_splitter_controls()
        self.setWindowIcon(QIcon('study_icon.png'))
    def update_display(self):
        if self.flashcards:
            card = self.flashcards[self.current_index]
            content = card['front'] if self.showing_front else card['back']
            self.card_display.setText(content)
            self.progress_label.setText(f"Card {self.current_index + 1} of {len(self.flashcards)}")
    def flip_card(self):
        self.showing_front = not self.showing_front
        self.update_display()
    def next_card(self):
        if self.current_index < len(self.flashcards) - 1:
            self.current_index += 1
            self.showing_front = True
            self.update_display()
    def previous_card(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.showing_front = True
            self.update_display()
class PlaylistItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#6200EE"))
        else:
            painter.fillRect(option.rect, QColor("#2d2d2d"))
        text = index.data()
        painter.setPen(QColor("white"))
        painter.drawText(option.rect.adjusted(10, 0, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setStyle("Fusion")
    window = ModernStudyApp()
    window.show()
    sys.exit(app.exec_())
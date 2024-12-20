from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QDoubleSpinBox, QListWidget
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt

from env import SERVER_PORT
from http_manage import HTTPClientManager


class ScoreTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.subject_suggestions = []

    def load_subject_suggestions(self):
        try:
            client = HTTPClientManager.get_client()
            response = client.get(f"{SERVER_PORT}/user-subjects/")
            response.raise_for_status()

            self.subject_suggestions = response.json()
            print("Đã tải dữ liệu môn học:", self.subject_suggestions)
        except Exception as e:
            print(f"Lỗi khi tải dữ liệu môn học: {e}")

    def init_ui(self):
        self.subject_input = QLineEdit(self)
        self.subject_input.setPlaceholderText("Nhập mã môn học hoặc tìm kiếm...")
        self.subject_input.textChanged.connect(self.on_subject_input_changed)

        self.subject_suggestions_list = QListWidget(self)
        self.subject_suggestions_list.hide()
        self.subject_suggestions_list.itemClicked.connect(self.on_subject_suggestion_clicked)

        self.score_input = QDoubleSpinBox()
        self.score_input.setRange(0.0, 10.0)
        self.score_input.setValue(0.0)
        self.score_input.setDecimals(1)
        self.score_input.setFixedWidth(50)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Nhập ghi chú")
        self.note_input.setAlignment(Qt.AlignTop)

        self.save_button = QPushButton("Lưu điểm")
        self.save_button.clicked.connect(self.save_score)

        self.delete_button = QPushButton("Xóa điểm")
        self.delete_button.clicked.connect(self.delete_score)

        self.credits_completed_label = QLabel("Tín chỉ đã học: 0")
        self.total_credits_label = QLabel("Tổng số tín: 0")
        self.avg_score_label = QLabel("Điểm trung bình (thang 10): 0.0")
        self.avg_score_4_label = QLabel("Điểm trung bình (thang 4): 0.0")

        self.subject_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.score_input.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.note_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()

        summary_layout = QHBoxLayout()
        summary_layout.addWidget(self.credits_completed_label)
        summary_layout.addWidget(self.total_credits_label)
        summary_layout.addWidget(self.avg_score_label)
        summary_layout.addWidget(self.avg_score_4_label)

        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Chọn môn:"))
        subject_layout.addWidget(self.subject_input)
        subject_layout.addWidget(self.score_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.save_button)

        layout.addLayout(summary_layout)
        layout.addLayout(subject_layout)
        layout.addWidget(self.subject_suggestions_list)
        layout.addWidget(self.note_input)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_subject_input_changed(self, text):
        if not self.subject_suggestions:
            self.load_subject_suggestions()

        if text:
            self.subject_suggestions_list.show()
            self.subject_suggestions_list.clear()

            filtered_suggestions = [
                f"{subject['id']} - {subject['name']}"
                for subject in self.subject_suggestions
                if text.lower() in subject['id'].lower() or text.lower() in subject['name'].lower()
            ]

            if filtered_suggestions:
                self.subject_suggestions_list.addItems(filtered_suggestions)
            else:
                self.subject_suggestions_list.addItem("Không tìm thấy kết quả.")
        else:
            self.subject_suggestions_list.hide()

    def on_subject_suggestion_clicked(self, item):
        selected_subject = item.text()
        self.subject_input.setText(selected_subject.split(" - ")[0])
        self.subject_suggestions_list.hide()

    def save_score(self):
        subject = self.subject_input.text()
        score = self.score_input.value()
        note = self.note_input.text()

        success = self.save_score_to_api(subject, score, note)

        if success:
            self.update_summary()
            print(f"Đã lưu điểm cho {subject}: {score} - {note}")
        else:
            print("Lưu điểm thất bại.")

    def delete_score(self):
        subject = self.subject_input.text()

        if not subject:
            self.show_notification("Error", "Vui lòng chọn một môn học để xóa.")
            return

        success = self.delete_score_from_api(subject)

        if success:
            self.update_summary()
            print(f"Đã xóa điểm cho {subject}.")
        else:
            print("Xóa điểm thất bại.")

    def save_score_to_api(self, subject, score, note):
        try:
            client = HTTPClientManager.get_client()

            payload = {
                "subject_id": subject,
                "score": score,
                "note": note
            }

            response = client.post(SERVER_PORT + "/add-score/", json=payload)

            if response.status_code == 200:
                self.show_notification("Success", "Score saved successfully.")
                return True
            else:
                self.show_notification("Error", f"Failed to save score: {response.status_code}")
                return False
        except Exception as e:
            self.show_notification("Error", f"An error occurred while saving the score: {e}")
            return False

    def delete_score_from_api(self, subject):
        try:
            client = HTTPClientManager.get_client()

            payload = {"subject_id": subject}

            response = client.post(SERVER_PORT + "/remove-score/", json=payload)

            if response.status_code == 200:
                self.show_notification("Success", "Score deleted successfully.")
                return True
            else:
                self.show_notification("Error", f"Failed to delete score: {response.status_code}")
                return False
        except Exception as e:
            self.show_notification("Error", f"An error occurred while deleting the score: {e}")
            return False

    def show_notification(self, title, message):
        from PyQt5.QtWidgets import QMessageBox
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    def update_summary(self):
        completed_credits = 10
        total_credits = 20
        avg_score_10 = 7.5
        avg_score_4 = 3.0

        self.credits_completed_label.setText(f"Tín chỉ đã học: {completed_credits}")
        self.total_credits_label.setText(f"Tổng số tín: {total_credits}")
        self.avg_score_label.setText(f"Điểm trung bình (thang 10): {avg_score_10:.1f}")
        self.avg_score_4_label.setText(f"Điểm trung bình (thang 4): {avg_score_4:.1f}")

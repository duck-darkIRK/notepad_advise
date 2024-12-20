import sys
import httpx
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QComboBox
)

from env import SERVER_PORT
from http_manage import HTTPClientManager


class TabGenPath(QWidget):
    def __init__(self):
        super().__init__()
        self.client = None
        self.details = {}
        self.data = []
        self.init_ui()
        self.fetch_user_subjects()

    def init_ui(self):
        main_layout = QVBoxLayout()

        input_layout = QHBoxLayout()

        self.min_weight_label = QLabel("Tín chỉ tối thiểu:")
        self.min_weight_input = QLineEdit()
        self.min_weight_input.setText("12")
        input_layout.addWidget(self.min_weight_label)
        input_layout.addWidget(self.min_weight_input)

        self.max_weight_label = QLabel("Tín chỉ tối đa:")
        self.max_weight_input = QLineEdit()
        self.max_weight_input.setText("16")
        input_layout.addWidget(self.max_weight_label)
        input_layout.addWidget(self.max_weight_input)

        self.option_label = QLabel("Gồm option:")
        self.option_combo = QComboBox()
        self.option_combo.addItem("Có")
        self.option_combo.addItem("Không")
        input_layout.addWidget(self.option_label)
        input_layout.addWidget(self.option_combo)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.fetch_data)
        input_layout.addWidget(self.submit_button)

        main_layout.addLayout(input_layout)

        lists_layout = QHBoxLayout()

        self.left_list = QListWidget()
        self.left_list.itemClicked.connect(self.show_details)
        lists_layout.addWidget(self.left_list)

        self.right_list = QListWidget()
        lists_layout.addWidget(self.right_list)

        main_layout.addLayout(lists_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Giao diện Tab")
        self.setGeometry(200, 200, 600, 400)

    def fetch_user_subjects(self):
        """Fetch dữ liệu chỉ một lần khi mở tab."""
        if not self.client:
            self.client = HTTPClientManager.get_client()

        try:
            response = self.client.get(SERVER_PORT + "/user-subjects/")
            response.raise_for_status()
            user_subjects = response.json()

            self.details = {item["id"]: item for item in user_subjects}
        except Exception as e:
            print(f"Error fetching user subjects: {e}")

    def fetch_data(self):
        """Fetch data khi nhấn nút Submit."""
        try:
            min_weight = self.min_weight_input.text()
            max_weight = self.max_weight_input.text()

            include_option = self.option_combo.currentText() == "Có"

            payload = {
                "min_weight": min_weight,
                "max_weight": max_weight,
                "force": include_option
            }

            response = self.client.post(SERVER_PORT + "/generate_path/", json=payload)
            response.raise_for_status()
            generated_data = response.json()

            self.data = generated_data

            self.populate_left_list()
        except Exception as e:
            print(f"Error fetching generated path data: {e}")

    def populate_left_list(self):
        self.left_list.clear()
        for idx, subject_group in enumerate(self.data):
            group_item = QListWidgetItem(f"{', '.join(subject_group)}")
            group_item.setData(1, subject_group)
            self.left_list.addItem(group_item)

    def show_details(self, item):
        """Hiển thị chi tiết các môn học trong nhóm được chọn"""
        self.right_list.clear()
        subject_group = item.data(1)
        if subject_group:
            for subject_id in subject_group:
                subject = self.details.get(subject_id)
                if subject:
                    detail_text = f"{subject['id']} - {subject['name']} - {subject['weight']}"
                    self.right_list.addItem(detail_text)

    def arrange(self):
        min_weight = self.min_weight_input.text()
        max_weight = self.max_weight_input.text()
        print(f"Tín chỉ tối thiểu: {min_weight}, Tín chỉ tối đa: {max_weight}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TabGenPath()
    window.show()
    sys.exit(app.exec_())

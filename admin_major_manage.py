import json

import httpx
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLineEdit, QCompleter, QPushButton, QTableWidget, \
    QHBoxLayout, QTableWidgetItem, QLabel, QFileDialog, QListWidget, QComboBox, QMessageBox

from env import SERVER_PORT
from http_manage import HTTPClientManager


class MajorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        self.tab_widget.addTab(SearchTab(), "Tìm kiếm")
        self.tab_widget.addTab(ImportTab(), "Nhập")
        self.tab_widget.addTab(AssignSubjectTab(), "Gán môn")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)


class SearchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.major_input = QLineEdit(self)
        self.major_input.setPlaceholderText("Nhập mã ngành")
        self.major_completer = QCompleter(self)
        self.major_input.setCompleter(self.major_completer)

        submit_button = QPushButton("Tìm kiếm", self)
        submit_button.clicked.connect(self.on_submit)

        self.results_table = QTableWidget(self)
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Mã ngành", "Tên ngành", "Mã môn học", "Tên môn học", "Tín chỉ"])

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.major_input)
        input_layout.addWidget(submit_button)

        layout.addLayout(input_layout)
        layout.addWidget(self.results_table)

        self.setLayout(layout)

    def on_submit(self):
        major_code = self.major_input.text()
        data = self.search_major(major_code)
        self.results_table.setRowCount(0)
        for row_data in data:
            row_position = self.results_table.rowCount()
            self.results_table.insertRow(row_position)
            for col, value in enumerate(row_data):
                self.results_table.setItem(row_position, col, QTableWidgetItem(value))

    def search_major(self, major_code):
        """Tìm kiếm thông tin ngành dựa trên mã ngành bằng cách gọi API"""
        url = f"{SERVER_PORT}/majors/{major_code}"
        try:
            client = HTTPClientManager.get_client()
            response = client.get(url)
            response.raise_for_status()

            majors_data = response.json()
            print(majors_data)
            result = []

            major = majors_data

            major_id = major.get("id", "")
            major_name = major.get("name", "")
            subjects = major.get("subjects", [])

            for subject in subjects:
                subject_id = subject.get("id", "")
                subject_name = subject.get("name", "")
                subject_weight = subject.get("weight", "")
                result.append([major_id, major_name, subject_id, subject_name, str(subject_weight)])

            return result

        except httpx.RequestError as e:
            print(f"Lỗi kết nối API: {e}")
        except httpx.HTTPStatusError as e:
            print(f"Lỗi HTTP: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Lỗi khác: {e}")

        return []


class ImportTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.path_label = QLabel("Chọn file JSON đầu vào:")
        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)

        self.browse_button = QPushButton("Chọn file")
        self.browse_button.clicked.connect(self.browse_file)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_data)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Mã Ngành", "Tên Ngành", "Môn Học", "Liên Kết"])

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.path_label)
        top_layout.addWidget(self.path_display)
        top_layout.addWidget(self.browse_button)

        layout.addLayout(top_layout)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def browse_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file JSON", "", "JSON Files (*.json)", options=options)
        if file_path:
            self.path_display.setText(file_path)
            self.load_data(file_path)

    def load_data(self, file_path):
        """Đọc và hiển thị dữ liệu từ file JSON vào bảng"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.table.setRowCount(0)
            for major in data:
                major_id = major["major"]["id"]
                major_name = major["major"]["name"]
                for subject in major["subjects"]:
                    subject_id = subject["id"]
                    subject_type = subject["type"]
                    row_position = self.table.rowCount()
                    self.table.insertRow(row_position)
                    self.table.setItem(row_position, 0, QTableWidgetItem(major_id))
                    self.table.setItem(row_position, 1, QTableWidgetItem(major_name))
                    self.table.setItem(row_position, 2, QTableWidgetItem(subject_id))
                    self.table.setItem(row_position, 3, QTableWidgetItem(subject_type))

        except Exception as e:
            self.table.setRowCount(0)
            print(f"Error reading file: {e}")

    def submit_data(self):
        """Gửi file JSON lên server"""
        file_path = self.path_display.text()
        try:
            with open(file_path, 'rb') as file:
                url = f"{SERVER_PORT}/upload-majors/"
                client = HTTPClientManager.get_client()

                files = {'file': (file_path, file, 'application/json')}
                response = client.post(url, files=files)
                response.raise_for_status()

                if response.status_code == 200:
                    self.show_message("Thành công", "Tệp đã được upload thành công!", QMessageBox.Information)
                else:
                    self.show_message("Lỗi", f"Lỗi khi upload: {response.status_code}", QMessageBox.Critical)

        except httpx.RequestError as e:
            print(f"Lỗi kết nối API: {e}")
            self.show_message("Lỗi kết nối", f"Lỗi kết nối API: {e}", QMessageBox.Critical)
        except httpx.HTTPStatusError as e:
            print(f"Lỗi HTTP: {e.response.status_code} - {e.response.text}")
            self.show_message("Lỗi HTTP", f"Lỗi HTTP: {e.response.status_code}", QMessageBox.Critical)
        except Exception as e:
            print(f"Lỗi khác: {e}")
            self.show_message("Lỗi khác", f"Lỗi khác: {e}", QMessageBox.Critical)

    def show_message(self, title, text, icon):
        """Hiển thị hộp thoại thông báo"""
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec_()


class AssignSubjectTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_suggestions()

    def init_ui(self):
        layout = QVBoxLayout()

        self.major_input = QLineEdit(self)
        self.major_input.setPlaceholderText("Nhập mã ngành")
        self.major_input.textChanged.connect(self.on_major_input_changed)

        self.major_suggestions_list = QListWidget(self)
        self.major_suggestions_list.hide()
        self.major_suggestions_list.itemClicked.connect(self.on_major_suggestion_clicked)

        self.subject_input = QLineEdit(self)
        self.subject_input.setPlaceholderText("Nhập mã môn")
        self.subject_input.textChanged.connect(self.on_subject_input_changed)

        self.subject_suggestions_list = QListWidget(self)
        self.subject_suggestions_list.hide()
        self.subject_suggestions_list.itemClicked.connect(self.on_subject_suggestion_clicked)

        self.subject_type_combo = QComboBox(self)
        self.subject_type_combo.addItems(["required", "optional", "language_optional"])

        self.assign_button = QPushButton("Gán môn", self)
        self.assign_button.clicked.connect(self.on_assign)

        layout.addWidget(QLabel("Nhập thông tin gán môn"))
        layout.addWidget(self.major_input)
        layout.addWidget(self.major_suggestions_list)
        layout.addWidget(self.subject_input)
        layout.addWidget(self.subject_suggestions_list)
        layout.addWidget(self.subject_type_combo)
        layout.addWidget(self.assign_button)

        self.setLayout(layout)

        self.suggested_majors = []
        self.suggested_subjects = []

    def load_suggestions(self):
        """Gọi API để lấy danh sách gợi ý ngành và môn học"""
        try:
            client = HTTPClientManager.get_client()
            majors_response = client.get(f"{SERVER_PORT}/majors/")
            majors_response.raise_for_status()
            self.suggested_majors = majors_response.json()

            subjects_response = client.get(f"{SERVER_PORT}/subjects/")
            subjects_response.raise_for_status()
            self.suggested_subjects = subjects_response.json()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi tải danh sách gợi ý: {str(e)}")

    def on_major_input_changed(self):
        major_input = self.major_input.text().lower()

        filtered_majors = [
            f"{major['id']} - {major['name']}" for major in self.suggested_majors
            if major_input in major["id"].lower()
        ]

        self.major_suggestions_list.clear()
        if filtered_majors:
            self.major_suggestions_list.addItems(filtered_majors)
            self.major_suggestions_list.show()
        else:
            self.major_suggestions_list.hide()

    def on_major_suggestion_clicked(self, item):
        selected_text = item.text()
        selected_id = selected_text.split(" - ")[0]
        self.major_input.setText(selected_id)
        self.major_suggestions_list.hide()

    def on_subject_input_changed(self):
        subject_input = self.subject_input.text().lower()

        filtered_subjects = [
            f"{subject['id']} - {subject['name']}" for subject in self.suggested_subjects
            if subject_input in subject["id"].lower()
        ]

        self.subject_suggestions_list.clear()
        if filtered_subjects:
            self.subject_suggestions_list.addItems(filtered_subjects)
            self.subject_suggestions_list.show()
        else:
            self.subject_suggestions_list.hide()

    def on_subject_suggestion_clicked(self, item):
        selected_text = item.text()
        selected_id = selected_text.split(" - ")[0]
        self.subject_input.setText(selected_id)
        self.subject_suggestions_list.hide()

    def on_assign(self):
        major_code = self.major_input.text()
        subject_code = self.subject_input.text()
        subject_type = self.subject_type_combo.currentText()

        if not major_code or not subject_code:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        payload = {
            "major_id": major_code,
            "subject_id": subject_code,
            "subject_type": subject_type
        }

        try:
            client = httpx.Client(follow_redirects=True)
            response = client.post(f"{SERVER_PORT}/assign-subject/", json=payload)
            response.raise_for_status()

            QMessageBox.information(self, "Thành công", "Môn học đã được gán thành công!")
            self.major_input.clear()
            self.subject_input.clear()

        except httpx.HTTPStatusError as e:
            error_message = f"Lỗi từ server: {e.response.json().get('detail', str(e))}"
            QMessageBox.critical(self, "Lỗi", error_message)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi: {str(e)}")
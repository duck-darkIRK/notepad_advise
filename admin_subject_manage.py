import asyncio
import json

import httpx
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QTableWidget, \
    QTableWidgetItem, QListWidget, QFileDialog, QTabWidget, QMessageBox

from env import SERVER_PORT
from http_manage import HTTPClientManager


class SearchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.all_data = []
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()

        search_name_layout = QHBoxLayout()
        self.search_name_input = QLineEdit()
        self.search_name_input.setPlaceholderText("Nhập tên môn học để tìm kiếm...")
        search_name_btn = QPushButton("Tìm kiếm theo tên")
        search_name_btn.clicked.connect(self.update_table)

        search_name_layout.addWidget(self.search_name_input)
        search_name_layout.addWidget(search_name_btn)

        search_id_layout = QHBoxLayout()
        self.search_id_input = QLineEdit()
        self.search_id_input.setPlaceholderText("Nhập ID để tìm kiếm...")
        search_id_btn = QPushButton("Tìm kiếm theo ID")
        search_id_btn.clicked.connect(self.update_table)

        search_id_layout.addWidget(self.search_id_input)
        search_id_layout.addWidget(search_id_btn)

        filter_layout = QHBoxLayout()
        filter_label = QLabel("Lọc theo trọng số:")
        self.weight_filter = QComboBox()
        self.weight_filter.addItems(["Tất cả", "1", "2", "3", "4", "5", "6"])
        self.weight_filter.currentIndexChanged.connect(self.update_table)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.weight_filter)

        sort_layout = QHBoxLayout()
        sort_label = QLabel("Sắp xếp theo:")
        self.sort_by = QComboBox()
        self.sort_by.addItems(["Tên", "Trọng số", "Ngày tạo"])
        self.sort_by.currentIndexChanged.connect(self.update_table)
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_by)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Tên môn", "Trọng số", "Đã xóa", "Tiên quyết"])

        layout.addLayout(search_name_layout)
        layout.addLayout(search_id_layout)
        layout.addLayout(filter_layout)
        layout.addLayout(sort_layout)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_data(self):
        """Tải dữ liệu từ API và sử dụng cookie từ client"""
        url = f"{SERVER_PORT}/subjects/"
        try:
            client = HTTPClientManager.get_client()

            response = client.get(url)
            response.raise_for_status()
            print("Load Data Response:", response.status_code)
            all_data = response.json()
            print("Data:", all_data)

            self.all_data = all_data

            self.update_table()

        except httpx.RequestError as e:
            print(f"Lỗi kết nối API: {e}")
        except Exception as e:
            print(f"Lỗi xử lý dữ liệu: {e}")

    def update_table(self):
        """Lọc, sắp xếp và cập nhật bảng dựa trên dữ liệu đã tải."""
        search_name_term = self.search_name_input.text().lower()
        search_id_term = self.search_id_input.text().strip()
        weight_filter = self.weight_filter.currentText()
        sort_order = self.sort_by.currentText()

        filtered_data = self.all_data

        if search_id_term:
            filtered_data = [
                item for item in filtered_data
                if str(item["id"]) == search_id_term
            ]

        if search_name_term and not search_id_term:
            filtered_data = [
                item for item in filtered_data
                if search_name_term in item["name"].lower()
            ]

        if weight_filter != "Tất cả":
            filtered_data = [
                item for item in filtered_data
                if str(item["weight"]) == weight_filter
            ]

        if sort_order == "Tên":
            filtered_data.sort(key=lambda x: x["name"].lower())
        elif sort_order == "Trọng số":
            filtered_data.sort(key=lambda x: x["weight"])
        elif sort_order == "Ngày tạo":
            filtered_data.sort(key=lambda x: x.get("created_at", ""))

        self.table.setRowCount(0)

        for row_data in filtered_data:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(str(row_data["id"])))
            self.table.setItem(row_position, 1, QTableWidgetItem(row_data["name"]))
            self.table.setItem(row_position, 2, QTableWidgetItem(str(row_data["weight"])))
            self.table.setItem(row_position, 3, QTableWidgetItem("Có" if row_data["is_deleted"] else "Không"))
            self.table.setItem(row_position, 4, QTableWidgetItem(row_data["required"]))


class AddTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Nhập mã môn học")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên môn học")
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Nhập trọng số")
        self.require_input = QLineEdit()
        self.require_input.setPlaceholderText("Nhập môn học tiên quyết")

        submit_btn = QPushButton("Thêm môn học")
        submit_btn.clicked.connect(self.submit_search_form)

        layout.addWidget(QLabel("Mã môn học"))
        layout.addWidget(self.code_input)

        layout.addWidget(QLabel("Tên môn học"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Trọng số"))
        layout.addWidget(self.weight_input)

        layout.addWidget(QLabel("Môn học tiên quyết"))
        layout.addWidget(self.require_input)

        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def submit_search_form(self):
        code = self.code_input.text()
        name = self.name_input.text()
        weight = self.weight_input.text()
        require = self.require_input.text()

        if not code or not name or not weight or not require:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        data = {
            "id": code,
            "name": name,
            "weight": int(weight),
            "required": require
        }

        try:
            client = HTTPClientManager.get_client()
            response = client.post("http://127.0.0.1:8000/subjects/", json=data)

            if response.status_code == 200:
                QMessageBox.information(self, "Thành công", f"Đã thêm môn học: {name}")
                self.code_input.clear()
                self.name_input.clear()
                self.weight_input.clear()
                self.require_input.clear()
            else:
                QMessageBox.critical(self, "Lỗi",
                                     f"Không thể thêm môn học: {response.json().get('detail', 'Lỗi không xác định')}")

        except httpx.RequestError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể kết nối đến API: {e}")


class EditTab(QWidget):

    def __init__(self):
        super().__init__()
        self.suggestions = []
        self.init_ui()
        self.load_suggestions()

    def init_ui(self):
        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Nhập ID môn học")
        self.id_input.textChanged.connect(self.on_id_input_changed)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Tên môn học")
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Trọng số")
        self.require_input = QLineEdit()
        self.require_input.setPlaceholderText("Môn học tiên quyết")

        self.suggestions_list = QListWidget()
        self.suggestions_list.hide()
        self.suggestions_list.itemClicked.connect(self.on_suggestion_clicked)

        submit_btn = QPushButton("Sửa môn học")
        submit_btn.clicked.connect(self.submit_edit_form)

        delete_btn = QPushButton("Xóa môn học")
        delete_btn.clicked.connect(self.delete_subject)

        layout.addWidget(QLabel("ID môn học"))
        layout.addWidget(self.id_input)

        layout.addWidget(QLabel("Tên môn học"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Trọng số"))
        layout.addWidget(self.weight_input)

        layout.addWidget(QLabel("Môn học tiên quyết"))
        layout.addWidget(self.require_input)

        layout.addWidget(self.suggestions_list)
        layout.addWidget(submit_btn)
        layout.addWidget(delete_btn)

        self.setLayout(layout)

    def load_suggestions(self):
        """Tải dữ liệu gợi ý từ API và lưu cục bộ."""
        try:
            client = HTTPClientManager.get_client()
            response = client.get(f"{SERVER_PORT}/subjects/", timeout=10)
            response.raise_for_status()
            data = response.json()
            self.suggestions = [f"{s['id']} - {s['name']}" for s in data]
        except httpx.RequestError as e:
            QMessageBox.critical(None, "Lỗi", f"Lỗi khi tải dữ liệu gợi ý: {e}")

    def load_subject_details(self, subject_code):
        """Tải chi tiết môn học từ API."""
        try:
            response = httpx.get(f"{SERVER_PORT}/subjects/{subject_code}", timeout=10)
            response.raise_for_status()
            data = response.json()

            self.name_input.setText(data.get("name", ""))
            self.weight_input.setText(str(data.get("weight", "")))
            self.require_input.setText(str(data.get("required", "")))
        except httpx.RequestError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi tải dữ liệu môn học: {e}")

    def on_id_input_changed(self):
        search_term = self.id_input.text()
        if not self.suggestions:
            return

        filtered_suggestions = [s for s in self.suggestions if search_term.lower() in s.lower()]
        self.suggestions_list.clear()

        if filtered_suggestions:
            self.suggestions_list.addItems(filtered_suggestions)
            self.suggestions_list.show()
        else:
            self.suggestions_list.hide()

    def on_suggestion_clicked(self, item):
        selected_text = item.text()
        selected_id = selected_text.split(" - ")[0]
        self.id_input.setText(selected_id)
        self.suggestions_list.hide()
        self.load_subject_details(selected_id)

    def submit_edit_form(self):
        """Cập nhật thông tin môn học."""
        subject_code = self.id_input.text()
        name = self.name_input.text()
        weight = self.weight_input.text()
        require = self.require_input.text()

        if not subject_code or not name or not weight:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        try:
            payload = {
                "name": name,
                "weight": int(weight),
                "required": require,
            }
            response = httpx.put(f"{SERVER_PORT}/subjects/{subject_code}", json=payload, timeout=10)
            response.raise_for_status()
            QMessageBox.information(self, "Thành công", "Cập nhật môn học thành công!")
            self.clear_form()
        except httpx.RequestError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi cập nhật môn học: {e}")

    def delete_subject(self):
        """Xóa môn học."""
        subject_code = self.id_input.text()

        if not subject_code:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập ID môn học để xóa!")
            return

        try:
            response = httpx.delete(f"{SERVER_PORT}/subjects/{subject_code}", timeout=10)
            response.raise_for_status()
            QMessageBox.information(self, "Thành công", "Xóa môn học thành công!")
            self.clear_form()
        except httpx.RequestError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi xóa môn học: {e}")

    def clear_form(self):
        """Xóa toàn bộ dữ liệu trên form."""
        self.id_input.clear()
        self.name_input.clear()
        self.weight_input.clear()
        self.require_input.clear()


class ImportTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Chọn file nhập vào")
        self.file_input.setReadOnly(True)

        self.select_file_btn = QPushButton("Chọn File")
        self.select_file_btn.clicked.connect(self.select_file)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["ID", "Tên môn học", "Trọng số", "Tiên quyết"])

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.submit_data)

        layout.addWidget(self.file_input)
        layout.addWidget(self.select_file_btn)
        layout.addWidget(self.data_table)
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn File", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            self.file_input.setText(file_path)
            self.load_data(file_path)

    def load_data(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.display_data(data)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi đọc file: {e}")

    def display_data(self, data):
        self.data_table.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            self.data_table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.data_table.setItem(row_idx, 1, QTableWidgetItem(row["name"]))
            self.data_table.setItem(row_idx, 2, QTableWidgetItem(str(row["weight"])))
            self.data_table.setItem(row_idx, 3, QTableWidgetItem(row["required"]))

    def submit_data(self):
        file_path = self.file_input.text()
        if not file_path:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn file trước khi submit.")
            return

        try:
            with open(file_path, "rb") as file:
                files = {"file": (file_path, file, "application/json")}
                client = HTTPClientManager.get_client()
                response = client.post("http://127.0.0.1:8000/upload-subjects/", files=files, timeout=10)
                response.raise_for_status()
                QMessageBox.information(self, "Thành công", "Upload thành công!")
        except httpx.RequestError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi kết nối: {e}")
        except httpx.HTTPStatusError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi từ server: {e.response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {e}")


class SubjectPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        self.tab_widget.addTab(SearchTab(), "Tìm kiếm")
        self.tab_widget.addTab(AddTab(), "Thêm")
        self.tab_widget.addTab(EditTab(), "Sửa")
        self.tab_widget.addTab(ImportTab(), "Nhập")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)


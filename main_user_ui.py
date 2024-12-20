import sys

import qdarkstyle
from PyQt5.QtWidgets import QVBoxLayout, QTabWidget, QWidget, QApplication, QMainWindow, QMenuBar, QAction, QDialog, \
    QLineEdit, QPushButton, QHBoxLayout, QListWidget, QMessageBox
from PyQt5.QtCore import Qt

from env import SERVER_PORT
from genpath_tab import TabGenPath
from grades_tab import GradesTab
from http_manage import HTTPClientManager
from register_tab import RegisterTab
from save_note_module import ScoreTab



class AddMajorDialog(QDialog):
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url
        self.suggested_majors = []
        self.selected_major_id = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Thêm chuyên ngành")
        self.setFixedSize(500, 200)

        self.major_input = QLineEdit(self)
        self.major_input.setPlaceholderText("Nhập tên chuyên ngành hoặc tìm kiếm...")
        self.major_input.textChanged.connect(self.on_major_input_changed)

        self.major_suggestions_list = QListWidget(self)
        self.major_suggestions_list.hide()
        self.major_suggestions_list.itemClicked.connect(self.on_major_suggestion_clicked)

        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.submit_major)

        self.remove_button = QPushButton("Remove", self)
        self.remove_button.clicked.connect(self.remove_major)
        self.remove_button.setEnabled(False)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.major_input)
        input_layout.addWidget(self.submit_button)
        input_layout.addWidget(self.remove_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.major_suggestions_list)

        self.setLayout(main_layout)

        self.load_suggestions()

    def load_suggestions(self):
        try:
            client = HTTPClientManager.get_client()
            response = client.get(f"{SERVER_PORT}/majors/")
            response.raise_for_status()
            self.suggested_majors = response.json()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi tải danh sách gợi ý: {str(e)}")

    def on_major_input_changed(self, text):
        if text:
            self.major_suggestions_list.show()
            self.major_suggestions_list.clear()

            filtered_suggestions = [
                f"{major['id']} - {major['name']}" for major in self.suggested_majors
                if text.lower() in major["name"].lower()
            ]

            if filtered_suggestions:
                self.major_suggestions_list.addItems(filtered_suggestions)
            else:
                self.major_suggestions_list.addItem("Không tìm thấy kết quả.")
        else:
            self.major_suggestions_list.hide()

    def on_major_suggestion_clicked(self, item):
        selected_text = item.text()
        print(f"Đã chọn: {selected_text}")
        parts = selected_text.split(" - ")
        if len(parts) >= 2:
            self.selected_major_id = parts[0]
            self.major_input.setText(parts[1])
        else:
            self.selected_major_id = None
        print(f"selected_major_id: {self.selected_major_id}")
        self.major_suggestions_list.hide()
        self.remove_button.setEnabled(True)

    def submit_major(self):
        selected_major = self.major_input.text()
        if selected_major:
            try:
                major_id = self.selected_major_id
                print(f"Đang thêm chuyên ngành với major_id: {major_id}")
                if not major_id:
                    QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một chuyên ngành hợp lệ.")
                    return

                client = HTTPClientManager.get_client()
                response = client.post(f"{SERVER_PORT}/add-major/", json={"major_id": major_id})
                response.raise_for_status()

                QMessageBox.information(self, "Thông báo", "Chuyên ngành đã được thêm thành công.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi thêm chuyên ngành: {str(e)}")
        else:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập hoặc chọn một chuyên ngành.")

    def remove_major(self):
        if not self.selected_major_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn chuyên ngành để xóa.")
            return

        try:
            print(f"Đang loại bỏ chuyên ngành với major_id: {self.selected_major_id}")
            client = HTTPClientManager.get_client()
            response = client.post(f"{SERVER_PORT}/remove-major/", json={"major_id": self.selected_major_id})

            if response.status_code == 404:
                QMessageBox.warning(self, "Cảnh báo", "Bạn không có học chuyên ngành này.")
                return

            response.raise_for_status()

            QMessageBox.information(self, "Thông báo", "Chuyên ngành đã được loại bỏ.")
            self.major_input.clear()
            self.selected_major_id = None
            self.remove_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi loại bỏ chuyên ngành: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Trang chủ")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()

        # self.tab_schedule = ScheduleTab()
        # self.tab_register = RegisterTab()
        self.tab_grades = GradesTab()
        self.tab_save = ScoreTab()
        self.tab_gen_path = TabGenPath()

        # self.tabs.addTab(self.tab_schedule, "Lịch học")
        self.tabs.addTab(self.tab_gen_path, "Xếp lịch trình")
        # self.tabs.addTab(self.tab_register, "Đăng kí học")
        self.tabs.addTab(self.tab_grades, "Bảng điểm")
        self.tabs.addTab(self.tab_save, "Lưu điểm")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()

        settings_menu = menubar.addMenu("Settings")

        self.toggle_dark_action = QAction("Switch to Dark Mode", self)
        self.toggle_dark_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(self.toggle_dark_action)

        add_major_action = QAction("Thêm chuyên ngành", self)
        add_major_action.triggered.connect(self.open_add_major_dialog)
        settings_menu.addAction(add_major_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menubar.addAction(quit_action)

    def open_add_major_dialog(self):
        major_suggestions = ["Khoa học máy tính", "Kỹ thuật phần mềm", "Hệ thống thông tin", "Mạng máy tính", "Trí tuệ nhân tạo"]

        dialog = AddMajorDialog(major_suggestions)
        dialog.exec_()

    def toggle_theme(self):
        if self.toggle_dark_action.text() == "Switch to Dark Mode":
            self.set_dark_mode()
            self.toggle_dark_action.setText("Switch to Light Mode")
        else:
            self.set_light_mode()
            self.toggle_dark_action.setText("Switch to Dark Mode")

    def set_dark_mode(self):
        self.setStyleSheet(qdarkstyle.load_stylesheet())

    def set_light_mode(self):
        self.setStyleSheet("")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QTabWidget
)
import httpx
from env import SERVER_PORT
from http_manage import HTTPClientManager

from main_user_ui import MainWindow
from main_admin_ui import AdminWindow

class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Đăng nhập/Đăng ký")
        self.setGeometry(100, 100, 400, 300)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.login_tab = LoginTab()
        self.signup_tab = SignupTab()

        self.tab_widget.addTab(self.login_tab, "Đăng nhập")
        self.tab_widget.addTab(self.signup_tab, "Đăng ký")


class LoginTab(QWidget):
    def __init__(self):
        super().__init__()
        self.client = httpx.Client(follow_redirects=True)
        self.init_ui()

    def init_ui(self):
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        self.password_label = QLabel("Mật khẩu:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Đăng nhập")
        self.login_button.clicked.connect(self.on_login)

        layout = QVBoxLayout()

        username_layout = QHBoxLayout()
        username_layout.addWidget(self.username_label)
        username_layout.addWidget(self.username_input)
        self.username_input.setFixedWidth(200)

        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_label)
        password_layout.addWidget(self.password_input)
        self.password_input.setFixedWidth(200)

        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def on_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            self.show_message("Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu.")
            return

        response = self.api_login(username, password)

        if response and response.status_code == 200:
            user_data = response.json()
            role = user_data.get("user", {}).get("role", "user")
            self.show_message("Thành công", f"Đăng nhập thành công với Username: {username}")
            self.open_main_window(role)
        else:
            self.show_message("Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng.")

    def api_login(self, username, password):
        """Đăng nhập và lưu cookie vào client"""
        url = f"{SERVER_PORT}/login/"
        payload = {
            'code': username,
            'password': password
        }
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            client = HTTPClientManager.get_client()
            response = client.post(url, json=payload, headers=headers)
            print("Login Response Headers:", response.headers)

            cookies = client.cookies
            print("Login Cookies:", cookies)

            session_id = cookies.get("session_id")
            if session_id:
                print(f"Session ID: {session_id}")
            else:
                print("Không tìm thấy session_id trong cookie.")

            return response
        except httpx.RequestError as e:
            print(f"Lỗi: Không thể kết nối đến API: {e}")
            return None

    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information if title == "Thành công" else QMessageBox.Critical)
        msg_box.exec_()

    def open_main_window(self, role):
        if role == "admin":
            self.main_window = AdminWindow()
        else:
            self.main_window = MainWindow()
        self.main_window.show()
        self.window().close()


class SignupTab(QWidget):
    def __init__(self):
        super().__init__()
        self.client = httpx.Client(follow_redirects=True)
        self.init_ui()

    def init_ui(self):
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        self.password_label = QLabel("Mật khẩu:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.confirm_password_label = QLabel("Nhập lại mật khẩu:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()

        self.signup_button = QPushButton("Đăng ký")
        self.signup_button.clicked.connect(self.on_signup)

        layout = QVBoxLayout()

        username_layout = QHBoxLayout()
        username_layout.addWidget(self.username_label)
        username_layout.addWidget(self.username_input)
        self.username_input.setFixedWidth(200)

        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_label)
        password_layout.addWidget(self.password_input)
        self.password_input.setFixedWidth(200)

        confirm_password_layout = QHBoxLayout()
        confirm_password_layout.addWidget(self.confirm_password_label)
        confirm_password_layout.addWidget(self.confirm_password_input)
        self.confirm_password_input.setFixedWidth(200)

        email_layout = QHBoxLayout()
        email_layout.addWidget(self.email_label)
        email_layout.addWidget(self.email_input)
        self.email_input.setFixedWidth(200)

        layout.addLayout(username_layout)
        layout.addLayout(email_layout)
        layout.addLayout(password_layout)
        layout.addLayout(confirm_password_layout)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

    def on_signup(self):
        username = self.username_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        email = self.email_input.text()

        if len(username) < 3:
            self.show_message("Lỗi", "Username phải có ít nhất 3 ký tự.")
            return

        if len(password) < 4:
            self.show_message("Lỗi", "Mật khẩu phải có ít nhất 4 ký tự.")
            return

        if password != confirm_password:
            self.show_message("Lỗi", "Mật khẩu và nhập lại mật khẩu không khớp.")
            return

        if email is not None and email != "" and not self.validate_email(email):
            self.show_message("Lỗi", "Email không hợp lệ.")
            return

        response = self.api_register(username, password, email)

        if response and response.status_code == 200:
            self.show_message("Thành công", f"Đăng ký thành công với Username: {username}")
        else:
            self.show_message("Lỗi", "Đăng ký không thành công. Vui lòng thử lại.")

    def api_register(self, username, password, email):
        url = f"{SERVER_PORT}/register"
        payload = {
            'code': username,
            'password': password,
            'email': email
        }
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = self.client.post(url, json=payload, headers=headers)
            return response
        except httpx.RequestError as e:
            self.show_message("Lỗi", f"Không thể kết nối đến API: {e}")
            return None

    def validate_email(self, email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None

    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information if title == "Thành công" else QMessageBox.Critical)
        msg_box.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    auth_window = AuthWindow()
    auth_window.show()
    sys.exit(app.exec_())

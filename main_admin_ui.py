import json

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QVBoxLayout, QWidget, QLabel, QTabWidget, QPushButton, \
    QTableWidgetItem, QTableWidget, QComboBox, QHBoxLayout, QLineEdit, QListWidget, QFileDialog, QCompleter
import sys

from admin_subject_manage import SubjectPage
from admin_major_manage import MajorPage


class SchedulePage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        self.tab_widget.addTab(self.create_search_tab(), "Tìm kiếm")
        self.tab_widget.addTab(self.create_add_tab(), "Thêm")
        self.tab_widget.addTab(self.create_edit_tab(), "Sửa")
        self.tab_widget.addTab(self.create_delete_tab(), "Xóa")
        self.tab_widget.addTab(self.create_import_tab(), "Nhập")
        self.tab_widget.addTab(self.create_export_tab(), "Xuất")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def create_search_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nội dung Tìm kiếm"))
        layout.addWidget(QPushButton("Nút Tìm kiếm"))
        tab.setLayout(layout)
        return tab

    def create_add_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nội dung Thêm"))
        layout.addWidget(QPushButton("Nút Thêm"))
        tab.setLayout(layout)
        return tab

    def create_edit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nội dung Sửa"))
        layout.addWidget(QPushButton("Nút Sửa"))
        tab.setLayout(layout)
        return tab

    def create_delete_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nội dung Xóa"))
        layout.addWidget(QPushButton("Nút Xóa"))
        tab.setLayout(layout)
        return tab

    def create_import_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nội dung Nhập"))
        layout.addWidget(QPushButton("Nút Nhập"))
        tab.setLayout(layout)
        return tab

    def create_export_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nội dung Xuất"))
        layout.addWidget(QPushButton("Nút Xuất"))
        tab.setLayout(layout)
        return tab


class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quản lý học tập")
        self.setGeometry(100, 100, 600, 400)

        self.menu = self.menuBar()
        self.init_menu()

        self.show_subject()

    def init_menu(self):
        subject_action = QAction("Môn học", self)
        subject_action.triggered.connect(lambda: self.show_subject("Quản lý Môn học"))
        self.menu.addAction(subject_action)

        major_action = QAction("Chuyên ngành", self)
        major_action.triggered.connect(lambda: self.show_major("Quản lý Chuyên ngành"))
        self.menu.addAction(major_action)

        schedule_action = QAction("Lịch học", self)
        schedule_action.triggered.connect(lambda: self.show_schedule("Quản lý Lịch học"))
        self.menu.addAction(schedule_action)

    def show_subject(self, title="Quản lý Môn học"):
        self.setWindowTitle(title)
        self.set_central_widget(SubjectPage())

    def show_major(self, title="Quản lý Chuyên ngành"):
        self.setWindowTitle(title)
        self.set_central_widget(MajorPage())

    def show_schedule(self, title="Quản lý Lịch học"):
        self.setWindowTitle(title)
        self.set_central_widget(SchedulePage())

    def set_central_widget(self, widget):
        self.setCentralWidget(widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = AdminWindow()
    main_window.show()
    sys.exit(app.exec_())

from datetime import datetime
import sys
import httpx
from PyQt5.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QApplication, QPushButton
)

from env import SERVER_PORT
from http_manage import HTTPClientManager


class GradesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.grades_table = QTableWidget()
        self.grades_table.setRowCount(10)
        self.grades_table.setColumnCount(6)

        self.grades_table.setHorizontalHeaderLabels(
            ["Mã môn", "Tên môn", "Số tín chỉ", "Điểm", "Thời gian hoàn thành", "Ghi chú"]
        )

        self.reload_button = QPushButton("Tải lại dữ liệu")
        self.reload_button.clicked.connect(self.load_data)

        layout = QVBoxLayout()
        layout.addWidget(self.grades_table)
        layout.addWidget(self.reload_button)
        self.setLayout(layout)

    def fetch_data(self):
        client = HTTPClientManager.get_client()

        try:
            user_scores_response = client.get(SERVER_PORT + "/user-scores/")
            user_scores_response.raise_for_status()
            return user_scores_response.json()
        except httpx.HTTPStatusError as err:
            print(f"HTTP error occurred: {err}")
            return None
        except Exception as err:
            print(f"An error occurred: {err}")
            return None

    def load_data(self):
        data = self.fetch_data()
        if data:
            self.update_table_with_data(data)

    def update_table_with_data(self, data):
        scores = data.get('scores', [])

        self.grades_table.setRowCount(0)

        for row_data in scores:
            row_position = self.grades_table.rowCount()
            self.grades_table.insertRow(row_position)

            timestamp = datetime.fromtimestamp(row_data["created_at"])
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            self.grades_table.setItem(row_position, 0, QTableWidgetItem(row_data["subject_id"]))  # Mã môn
            self.grades_table.setItem(row_position, 1, QTableWidgetItem(row_data["subject_name"]))  # Tên môn
            self.grades_table.setItem(row_position, 2, QTableWidgetItem(str(row_data["weight"])))  # Số tín chỉ
            self.grades_table.setItem(row_position, 3, QTableWidgetItem(str(row_data["score"])))  # Điểm
            self.grades_table.setItem(row_position, 4, QTableWidgetItem(formatted_time))  # Thời gian hoàn thành
            self.grades_table.setItem(row_position, 5, QTableWidgetItem(row_data.get("note", "")))  # Ghi chú


if __name__ == "__main__":
    app = QApplication(sys.argv)
    grades_tab = GradesTab()
    grades_tab.show()
    sys.exit(app.exec_())

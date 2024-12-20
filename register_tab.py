from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QScrollArea
from PyQt5.QtCore import Qt
from drag_drop_widget import DragWidget, DragItem


class RegisterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.available_items = DragWidget(orientation=Qt.Orientation.Vertical)
        self.selected_items = DragWidget(orientation=Qt.Orientation.Vertical)

        for item_label in ["Môn học 1", "Môn học 2", "Môn học 3", "Môn học 4"] * 10:
            item = DragItem(item_label)
            self.available_items.add_item(item)

        self.available_items.orderChanged.connect(self.on_items_changed)
        self.selected_items.orderChanged.connect(self.on_items_changed)

        layout = QVBoxLayout()

        top_box_label = QLabel("Danh sách môn học")
        top_box_label.setAlignment(Qt.AlignCenter)
        top_box_label.setFixedHeight(30)

        bottom_box_label = QLabel("Danh sách đã chọn")
        bottom_box_label.setAlignment(Qt.AlignCenter)
        bottom_box_label.setFixedHeight(30)

        wrapper_available = QWidget()
        wrapper_available.setStyleSheet("border: 2px solid black;")
        wrapper_available_layout = QVBoxLayout()
        wrapper_available_layout.addWidget(self.available_items)
        wrapper_available.setLayout(wrapper_available_layout)

        wrapper_selected = QWidget()
        wrapper_selected.setStyleSheet("border: 2px solid black;")
        wrapper_selected_layout = QVBoxLayout()
        wrapper_selected_layout.addWidget(self.selected_items)
        wrapper_selected.setLayout(wrapper_selected_layout)

        scroll_area_1 = QScrollArea()
        scroll_area_1.setWidget(wrapper_available)
        scroll_area_1.setWidgetResizable(True)

        scroll_area_2 = QScrollArea()
        scroll_area_2.setWidget(wrapper_selected)
        scroll_area_2.setWidgetResizable(True)

        option_box = QVBoxLayout()
        option_box.addWidget(top_box_label)
        option_box.addWidget(scroll_area_1)
        selected_box = QVBoxLayout()
        selected_box.addWidget(bottom_box_label)
        selected_box.addWidget(scroll_area_2)
        top_box = QHBoxLayout()
        top_box.addLayout(option_box)
        top_box.addLayout(selected_box)
        layout.addLayout(top_box)
        self.setLayout(layout)

    def on_items_changed(self):
        available_data = self.available_items.get_item_data()
        selected_data = self.selected_items.get_item_data()
        print(f"Danh sách môn học khả dụng: {available_data}")
        print(f"Danh sách môn học đã chọn: {selected_data}")

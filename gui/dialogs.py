from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit


class DetailedLogDialog(QDialog):
    def __init__(self, log_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Details")
        self.setGeometry(200, 200, 600, 400)
        self.setup_ui(log_data)

    def setup_ui(self, log_data):
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Format and display log data
        for key, value in log_data.items():
            text_edit.append(f"{key}: {value}")

        layout.addWidget(text_edit)
        self.setLayout(layout)
import sys
import sqlite3
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, 
                             QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox, QDialog, 
                             QTextEdit, QCheckBox, QListWidget, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

class DetailedLogDialog(QDialog):
    def __init__(self, log_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Details")
        self.setGeometry(200, 200, 600, 400)
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        for key, value in log_data.items():
            text_edit.append(f"{key}: {value}")
        layout.addWidget(text_edit)
        self.setLayout(layout)

class LogViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(r'C:\Users\P0037463\Projects\Event Wizard\icon.ico'))
        self.fields = []
        self.saved_searches = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Event Wizard')
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QVBoxLayout()

        # Top controls
        top_layout = QHBoxLayout()
        load_button = QPushButton('Load Parsed Logs', self)
        load_button.clicked.connect(self.load_csv)
        top_layout.addWidget(load_button)
        top_layout.addStretch(1)

        self.dark_mode_checkbox = QCheckBox('Dark Mode', self)
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        top_layout.addWidget(self.dark_mode_checkbox)

        main_layout.addLayout(top_layout)

        # Search bar and saved searches
        search_layout = QHBoxLayout()
        search_label = QLabel('Search Logs (SQL Query):')
        search_layout.addWidget(search_label)

        self.search_bar = QLineEdit(self)
        search_layout.addWidget(self.search_bar)

        search_button = QPushButton('Search', self)
        search_button.clicked.connect(self.run_query)
        search_layout.addWidget(search_button)

        self.search_progress = QProgressBar(self)
        self.search_progress.setRange(0, 100)
        self.search_progress.setTextVisible(True)
        self.search_progress.setFormat("%p%")
        self.search_progress.setFixedWidth(100)
        self.search_progress.setValue(0)
        search_layout.addWidget(self.search_progress)

        save_search_button = QPushButton('Save Search', self)
        save_search_button.clicked.connect(self.save_search)
        search_layout.addWidget(save_search_button)

        main_layout.addLayout(search_layout)

        # Saved searches list
        self.saved_searches_list = QListWidget()
        self.saved_searches_list.itemDoubleClicked.connect(self.load_saved_search)
        self.saved_searches_list.setMaximumHeight(100)
        main_layout.addWidget(QLabel("Saved Searches:"))
        main_layout.addWidget(self.saved_searches_list)

        # Table
        self.table = QTableWidget(self)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.show_detailed_log)
        self.table.horizontalHeader().sectionMoved.connect(self.on_section_moved)
        self.table.horizontalHeader().sectionClicked.connect(self.on_section_clicked)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().setDragEnabled(True)
        self.table.horizontalHeader().setDragDropMode(QTableWidget.InternalMove)
        main_layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Parsed Log File", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.load_csv_into_db(file_path)
            except Exception as e:
                self.show_error("File Load Error", f"An error occurred while loading the file: {str(e)}")

    def load_csv_into_db(self, csv_file):
        try:
            self.conn = sqlite3.connect(':memory:')
            cursor = self.conn.cursor()

            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                self.fields = next(csv_reader)  # Read header row to get field names
                
                # Create table with detected fields
                create_table_sql = f"CREATE TABLE logs ({', '.join([f'[{field}] TEXT' for field in self.fields])})"
                cursor.execute(create_table_sql)

                # Prepare SQL for insertion
                insert_sql = f"INSERT INTO logs ({', '.join(['[' + field + ']' for field in self.fields])}) VALUES ({', '.join(['?' for _ in self.fields])})"
                
                # Insert data
                cursor.executemany(insert_sql, csv_reader)

            self.conn.commit()
            QMessageBox.information(self, "Success", f"Logs loaded successfully. Detected {len(self.fields)} fields.")
            self.run_query("SELECT * FROM logs LIMIT 100")  # Show first 100 logs by default
        except Exception as e:
            raise Exception(f"Error loading CSV: {str(e)}")

    def run_query(self, query=None):
        if not query:
            query = self.search_bar.text()
        if query and hasattr(self, 'conn'):
            try:
                cursor = self.conn.cursor()
                cursor.execute(query)
                result = cursor.fetchall()

                column_names = [description[0] for description in cursor.description]

                self.table.setRowCount(len(result))
                self.table.setColumnCount(len(column_names))
                self.table.setHorizontalHeaderLabels(column_names)

                self.search_progress.setValue(0)
                total_rows = len(result)
                
                for row_idx, row_data in enumerate(result):
                    for col_idx, col_data in enumerate(row_data):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
                    
                    # Update progress every 100 rows
                    if row_idx % 100 == 0 or row_idx == total_rows - 1:
                        progress = int((row_idx + 1) / total_rows * 100)
                        self.search_progress.setValue(progress)
                        QApplication.processEvents()  # Allow GUI to update

                self.table.resizeColumnsToContents()
                self.search_progress.setValue(100)
            except sqlite3.Error as e:
                self.show_error("Query Error", f"An error occurred while executing the query: {str(e)}")
        elif not hasattr(self, 'conn'):
            self.show_error("No Data", "Please load a CSV file before running a query.")

    def show_detailed_log(self, index):
        row = index.row()
        log_data = {self.table.horizontalHeaderItem(col).text(): self.table.item(row, col).text() 
                    for col in range(self.table.columnCount())}
        dialog = DetailedLogDialog(log_data, self)
        dialog.exec_()

    def toggle_dark_mode(self, state):
        if state == Qt.Checked:
            self.setStyleSheet("""
                QWidget { background-color: #2b2b2b; color: #ffffff; }
                QTableWidget { gridline-color: #3a3a3a; }
                QTableWidget::item { border-color: #3a3a3a; }
                QHeaderView::section { background-color: #3a3a3a; color: #ffffff; }
                QLineEdit, QPushButton { background-color: #3a3a3a; border: 1px solid #5a5a5a; padding: 5px; }
                QPushButton:hover { background-color: #4a4a4a; }
                QListWidget { background-color: #2b2b2b; color: #ffffff; border: 1px solid #5a5a5a; }
                QListWidget::item:selected { background-color: #4a4a4a; }
                QProgressBar { 
                    background-color: #2b2b2b;
                    border: 1px solid #5a5a5a;
                    color: #ffffff;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4a4a4a;
                }
            """)
        else:
            self.setStyleSheet("")

    def on_section_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        print(f"Column moved: {logicalIndex} from {oldVisualIndex} to {newVisualIndex}")

    def on_section_clicked(self, logicalIndex):
        for i in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(i)
            font = header_item.font()
            font.setBold(i == logicalIndex)
            header_item.setFont(font)

    def save_search(self):
        query = self.search_bar.text()
        if query and query not in self.saved_searches:
            self.saved_searches.append(query)
            self.saved_searches_list.addItem(query)

    def load_saved_search(self, item):
        self.search_bar.setText(item.text())
        self.run_query(item.text())

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(r'C:\Users\P0037463\Projects\Event Wizard\icon.ico'))
    viewer = LogViewer()
    viewer.show()
    sys.exit(app.exec_())
from PyQt5.QtWidgets import (QMainWindow, QTableView, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
                             QCheckBox, QListWidget, QProgressBar, QMessageBox,
                             QStatusBar)
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QKeySequence
import os
from utils.database import DatabaseManager
from utils.log_parser import LogParser
from gui.dialogs import DetailedLogDialog


class LogViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.log_parser = LogParser()
        self.setup_variables()
        self.setup_ui()
        self.connect_signals()

        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.operation_status_dialog = None

    def setup_variables(self):
        self.fields = []
        self.current_page = 1
        self.rows_per_page = 500
        self.total_rows = 0
        self.model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.current_sort_column = None
        self.current_sort_order = Qt.AscendingOrder
        self.column_states = {}

    def setup_ui(self):
        self.setWindowTitle('Event Wizard')
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QVBoxLayout()

        # Top controls
        top_layout = QHBoxLayout()

        # Load Parsed Logs button
        load_button = QPushButton('Load Parsed Logs', self)
        load_button.clicked.connect(self.load_csv)
        top_layout.addWidget(load_button)

        # Parse Log button
        parse_button = QPushButton('Parse Log', self)
        parse_button.clicked.connect(self.parse_logs)
        top_layout.addWidget(parse_button)

        # Drop DB button
        drop_db_button = QPushButton('Drop DB', self)
        drop_db_button.clicked.connect(self.drop_database)
        top_layout.addWidget(drop_db_button)

        top_layout.addStretch(1)

        # Dark Mode checkbox
        self.dark_mode_checkbox = QCheckBox('Dark Mode', self)
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        top_layout.addWidget(self.dark_mode_checkbox)

        main_layout.addLayout(top_layout)

        # Search controls
        search_layout = QHBoxLayout()
        search_label = QLabel('Search Logs (SQL Query):')
        search_layout.addWidget(search_label)

        self.search_bar = QLineEdit(self)
        search_layout.addWidget(self.search_bar)

        search_button = QPushButton('Search', self)
        search_button.clicked.connect(self.run_query)
        search_layout.addWidget(search_button)

        # Progress bars
        self.search_progress = QProgressBar(self)
        self.search_progress.setRange(0, 100)
        self.search_progress.setTextVisible(True)
        self.search_progress.setFixedWidth(100)
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

        # Table view
        self.table = QTableView(self)
        self.setup_table()
        main_layout.addWidget(self.table)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_page_button = QPushButton('Previous Page')
        self.prev_page_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_page_button)

        self.page_label = QLabel('Page 1')
        pagination_layout.addWidget(self.page_label)

        self.next_page_button = QPushButton('Next Page')
        self.next_page_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_page_button)

        pagination_layout.addStretch(1)
        main_layout.addLayout(pagination_layout)

        # Loading progress bar
        self.load_progress = QProgressBar(self)
        self.load_progress.setRange(0, 100)
        self.load_progress.setTextVisible(True)
        self.load_progress.setFormat("Loading: %p%")
        self.load_progress.hide()
        main_layout.addWidget(self.load_progress)

        # Create central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def setup_table(self):
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.show_detailed_log)
        self.table.setSelectionMode(QTableView.ExtendedSelection)
        self.table.setSelectionBehavior(QTableView.SelectRows)

        # Configure header
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self.on_header_clicked)

    def connect_signals(self):
        # Connect database manager signals
        self.db_manager.progress_updated.connect(self.load_progress.setValue)
        self.db_manager.operation_completed.connect(self.show_status_message)
        self.db_manager.error_occurred.connect(self.show_error_message)

    def parse_logs(self):
        input_dir = QFileDialog.getExistingDirectory(self, "Select Log Directory")
        if not input_dir:
            return

        # Create output directory next to input directory
        output_dir = os.path.join(os.path.dirname(input_dir), "parsed_logs")

        # Show single status message at start
        msg = QMessageBox(self)
        msg.setWindowTitle("Processing")
        msg.setText("Processing logs with EvtxECmd...\nThis may take several minutes.")
        msg.setStandardButtons(QMessageBox.NoButton)  # No buttons during processing
        msg.show()

        # Start parsing
        worker = self.log_parser.start_parsing(input_dir, output_dir)

        # Connect to the correct signal names
        worker.start_parsing.connect(lambda: self.status_bar.showMessage("Started parsing logs..."))
        worker.parser_finished.connect(lambda success, message: self.handle_parsing_finished(success, message, msg))

        # Start worker
        worker.start()

    def handle_parsing_finished(self, success, message, msg_box):
        if success:
            msg_box.setText("Parsing completed successfully!")
            msg_box.setStandardButtons(QMessageBox.Ok)
            output_file = self.log_parser.get_output_file_path(message)
            if output_file:
                self.load_csv(output_file)
        else:
            msg_box.setText(f"Error during parsing: {message}")
            msg_box.setStandardButtons(QMessageBox.Ok)
        self.status_bar.showMessage("Parsing completed")

    def show_operation_status(self, message):
        """Show the initial status dialog"""
        if not self.operation_status_dialog:
            self.operation_status_dialog = QMessageBox(self)
            self.operation_status_dialog.setWindowTitle("Status")
            self.operation_status_dialog.setStandardButtons(QMessageBox.Ok)
            self.operation_status_dialog.button(QMessageBox.Ok).setEnabled(False)

        self.operation_status_dialog.setText(message)
        self.operation_status_dialog.show()

    def update_status(self, message):
        """Update status bar and dialog if it exists"""
        self.status_bar.showMessage(message)
        if self.operation_status_dialog and self.operation_status_dialog.isVisible():
            self.operation_status_dialog.setText(message)

    def handle_parsing_finished(self, success, message, msg_box):
        if success:
            msg_box.setText("Parsing completed successfully!")
            msg_box.setStandardButtons(QMessageBox.Ok)
            output_file = self.log_parser.get_output_file_path(message)
            if output_file:
                self.load_csv(output_file)
        else:
            msg_box.setText(f"Error during parsing: {message}")
            msg_box.setStandardButtons(QMessageBox.Ok)

    def load_csv(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Parsed Log File", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.load_progress.show()
                self.fields = self.db_manager.load_csv(file_path)
                self.display_data()
            except Exception as e:
                self.show_error_message(f"Error loading file: {str(e)}")
            finally:
                self.load_progress.hide()

    def drop_database(self):
        try:
            self.db_manager.drop_database()
            self.model.clear()
            self.setup_variables()
            self.show_status_message("Database dropped successfully")
        except Exception as e:
            self.show_error_message(f"Error dropping database: {str(e)}")

    def run_query(self):
        query = self.search_bar.text() or "SELECT * FROM logs"
        try:
            self.total_rows = self.db_manager.get_total_rows(query)
            self.current_page = 1
            self.display_data(query)
        except Exception as e:
            self.show_error_message(f"Query error: {str(e)}")

    def display_data(self, query="SELECT * FROM logs"):
        try:
            data = self.db_manager.get_paginated_data(query, self.current_page, self.rows_per_page)
            self.update_model(data)
            self.update_pagination_controls()
        except Exception as e:
            self.show_error_message(f"Error displaying data: {str(e)}")

    def update_model(self, data):
        self.model.clear()
        if self.fields:
            self.model.setHorizontalHeaderLabels(self.fields)

        for row_data in data:
            row_items = [QStandardItem(str(item)) for item in row_data]
            self.model.appendRow(row_items)

    def update_pagination_controls(self):
        total_pages = (self.total_rows - 1) // self.rows_per_page + 1
        self.page_label.setText(f'Page {self.current_page} of {total_pages}')
        self.prev_page_button.setEnabled(self.current_page > 1)
        self.next_page_button.setEnabled(self.current_page < total_pages)

    def show_detailed_log(self, index):
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()
        log_data = {
            self.fields[col]: self.model.data(self.model.index(row, col))
            for col in range(self.model.columnCount())
        }
        dialog = DetailedLogDialog(log_data, self)
        dialog.exec_()

    def show_status_message(self, message):
        self.status_bar.showMessage(message)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage(f"Error: {message}")

    def toggle_dark_mode(self, state):
        if state == Qt.Checked:
            self.setStyleSheet("""
                QWidget { background-color: #2b2b2b; color: #ffffff; }
                QTableView { gridline-color: #3a3a3a; }
                QHeaderView::section { background-color: #3a3a3a; color: #ffffff; }
                QLineEdit, QPushButton { 
                    background-color: #3a3a3a; 
                    border: 1px solid #5a5a5a; 
                    padding: 5px; 
                    color: #ffffff;
                }
                QPushButton:hover { background-color: #4a4a4a; }
                QProgressBar { 
                    border: 1px solid #5a5a5a;
                    background-color: #2b2b2b;
                    text-align: center;
                }
                QProgressBar::chunk { background-color: #4a4a4a; }
            """)
        else:
            self.setStyleSheet("")

    def save_search(self):
        query = self.search_bar.text()
        if query:
            self.saved_searches_list.addItem(query)

    def load_saved_search(self, item):
        self.search_bar.setText(item.text())
        self.run_query()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_data()

    def next_page(self):
        total_pages = (self.total_rows - 1) // self.rows_per_page + 1
        if self.current_page < total_pages:
            self.current_page += 1
            self.display_data()

    def on_header_clicked(self, logical_index):
        if self.current_sort_column == logical_index:
            self.current_sort_order = Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.AscendingOrder

        self.table.horizontalHeader().setSortIndicator(self.current_sort_column, self.current_sort_order)
        self.display_data()
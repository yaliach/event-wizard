import sys
import sqlite3
import csv
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableView, QLineEdit, QPushButton, 
                             QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox, QDialog, 
                             QTextEdit, QCheckBox, QListWidget, QProgressBar, QScrollBar, QAbstractItemView,
                             QHeaderView, QShortcut)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QModelIndex
from PyQt5.QtGui import QFont, QIcon, QStandardItemModel, QStandardItem, QClipboard, QKeySequence


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
        self.clipboard = QApplication.clipboard()
        self.setWindowIcon(QIcon(r'C:\Users\P0037463\Projects\Event Wizard\icon.ico'))
        self.fields = []
        self.saved_searches = []
        self.current_page = 1
        self.rows_per_page = 500
        self.total_rows = 0
        self.model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.db_path = '../logs.db'
        self.current_sort_column = None
        self.current_sort_order = Qt.AscendingOrder
        self.column_states = {}
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
        self.table = QTableView(self)
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.show_detailed_log)
        self.table.horizontalHeader().sectionMoved.connect(self.on_section_moved)
        self.table.horizontalHeader().sectionClicked.connect(self.on_section_clicked)
        self.table.horizontalHeader().sectionResized.connect(self.on_section_resized)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().setDragEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Make table read-only
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show horizontal scrollbar
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        main_layout.addWidget(self.table)

        copy_shortcut = QShortcut(QKeySequence.Copy, self.table)
        copy_shortcut.activated.connect(self.copy_selected_data)

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

        # Add loading progress bar
        self.load_progress = QProgressBar(self)
        self.load_progress.setRange(0, 100)
        self.load_progress.setTextVisible(True)
        self.load_progress.setFormat("Loading: %p%")
        self.load_progress.hide()
        main_layout.addWidget(self.load_progress)

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
            # Remove existing database file if it exists
            if os.path.exists(self.db_path):
                os.remove(self.db_path)

            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                self.fields = next(csv_reader)  # Read header row to get field names

                # Create table with detected fields
                create_table_sql = f"CREATE TABLE logs ({', '.join([f'[{field}] TEXT' for field in self.fields])})"
                cursor.execute(create_table_sql)

                # Prepare SQL for insertion
                insert_sql = f"INSERT INTO logs ({', '.join(['[' + field + ']' for field in self.fields])}) VALUES ({', '.join(['?' for _ in self.fields])})"

                # Count total rows for progress calculation
                total_rows = sum(1 for _ in csv_reader)
                f.seek(0)
                next(csv_reader)  # Skip header row again

                # Show loading progress bar
                self.load_progress.show()

                # Insert data in chunks
                chunk_size = 10000
                for i in range(0, total_rows, chunk_size):
                    chunk = [next(csv_reader) for _ in range(min(chunk_size, total_rows - i))]
                    cursor.executemany(insert_sql, chunk)
                    self.conn.commit()  # Commit after each chunk

                    # Update progress
                    progress = int((i + len(chunk)) / total_rows * 100)
                    self.load_progress.setValue(progress)
                    QApplication.processEvents()  # Allow GUI to update

            self.load_progress.hide()
            QMessageBox.information(self, "Success", f"Logs loaded successfully. Detected {len(self.fields)} fields.")
            self.display_initial_data()
        except Exception as e:
            self.load_progress.hide()
            raise Exception(f"Error loading CSV: {str(e)}")

    def copy_selected_data(self):
        selection = self.table.selectedIndexes()
        if not selection:
            return

        # Get the bounds of the selection
        min_row = min(index.row() for index in selection)
        max_row = max(index.row() for index in selection)
        min_col = min(index.column() for index in selection)
        max_col = max(index.column() for index in selection)

        # Create the text table
        text_lines = []
        for row in range(min_row, max_row + 1):
            line = []
            for col in range(min_col, max_col + 1):
                current_index = self.proxy_model.index(row, col)
                if current_index in selection:
                    # Map from proxy model to source model
                    source_index = self.proxy_model.mapToSource(current_index)
                    data = self.model.data(source_index, Qt.DisplayRole)
                    line.append(str(data) if data is not None else '')
                else:
                    line.append('')
            text_lines.append('\t'.join(line))

        text = '\n'.join(text_lines)

        # Debug print to check what's being copied
        print("Copying text:", text)  # This will help us see if data is being captured

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
    def display_initial_data(self):
        self.current_sort_column = None
        self.current_sort_order = Qt.AscendingOrder
        self.run_query("SELECT * FROM logs")

    def run_query(self, query=None):
        if not query:
            query = self.search_bar.text()
        if not query:
            query = "SELECT * FROM logs"
        
        if hasattr(self, 'conn'):
            try:
                cursor = self.conn.cursor()
                
                # Apply sorting if a column is selected
                if self.current_sort_column is not None:
                    sort_order = "ASC" if self.current_sort_order == Qt.AscendingOrder else "DESC"
                    query = f"SELECT * FROM ({query}) ORDER BY [{self.fields[self.current_sort_column]}] {sort_order}"

                # Get total count
                count_query = f"SELECT COUNT(*) FROM ({query})"
                cursor.execute(count_query)
                self.total_rows = cursor.fetchone()[0]
                
                # Execute query with LIMIT and OFFSET for pagination
                paginated_query = f"{query} LIMIT {self.rows_per_page} OFFSET {(self.current_page - 1) * self.rows_per_page}"
                cursor.execute(paginated_query)
                result = cursor.fetchall()

                column_names = [description[0] for description in cursor.description]

                self.model.clear()
                self.model.setHorizontalHeaderLabels(column_names)

                self.search_progress.setValue(0)
                total_rows = len(result)
                
                for row_idx, row_data in enumerate(result):
                    row_items = [QStandardItem(str(item)) for item in row_data]
                    self.model.appendRow(row_items)
                    
                    # Update progress every 10 rows
                    if row_idx % 10 == 0 or row_idx == total_rows - 1:
                        progress = int((row_idx + 1) / total_rows * 100)
                        self.search_progress.setValue(progress)
                        QApplication.processEvents()  # Allow GUI to update

                self.search_progress.setValue(100)
                self.update_pagination_controls()
                self.display_current_page()
                self.restore_column_states()
            except sqlite3.Error as e:
                self.show_error("Query Error", f"An error occurred while executing the query: {str(e)}")
        else:
            self.show_error("No Data", "Please load a CSV file before running a query.")

    def display_current_page(self):
        self.proxy_model.setSourceModel(self.model)
        self.table.setModel(self.proxy_model)
        self.restore_column_states()

    def update_pagination_controls(self):
        total_pages = (self.total_rows - 1) // self.rows_per_page + 1
        self.page_label.setText(f'Page {self.current_page} of {total_pages}')
        self.prev_page_button.setEnabled(self.current_page > 1)
        self.next_page_button.setEnabled(self.current_page < total_pages)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.run_query(self.search_bar.text())

    def next_page(self):
        total_pages = (self.total_rows - 1) // self.rows_per_page + 1
        if self.current_page < total_pages:
            self.current_page += 1
            self.run_query(self.search_bar.text())

    def show_detailed_log(self, index):
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()
        log_data = {self.model.headerData(col, Qt.Horizontal, Qt.DisplayRole): 
                    self.model.data(self.model.index(row, col), Qt.DisplayRole)
                    for col in range(self.model.columnCount())}
        dialog = DetailedLogDialog(log_data, self)
        dialog.exec_()

    def toggle_dark_mode(self, state):
        if state == Qt.Checked:
            self.setStyleSheet("""
                QWidget { background-color: #2b2b2b; color: #ffffff; }
                QTableView { gridline-color: #3a3a3a; }
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
                QScrollBar:vertical, QScrollBar:horizontal {
                    border: none;
                    background: #3a3a3a;
                    width: 14px;
                    height: 14px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                    background-color: #5a5a5a;
                    min-height: 30px;
                    min-width: 30px;
                    border-radius: 7px;
                }
                QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                    background-color: #6a6a6a;
                }
                QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical,
                QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
                    border: none;
                    background: none;
                    height: 0;
                    width: 0;
                }
                QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
                QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal,
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }
                QTableCornerButton::section {
                    background-color: #2b2b2b;
                }
            """)
        else:
            self.setStyleSheet("")

    def on_section_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.save_column_states()

    def on_section_resized(self, logicalIndex, oldSize, newSize):
        self.save_column_states()

    def on_section_clicked(self, logicalIndex):
        if self.current_sort_column == logicalIndex:
            # If clicking the same column, toggle the sort order
            self.current_sort_order = Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            # If clicking a new column, set it as the sort column and reset to ascending order
            self.current_sort_column = logicalIndex
            self.current_sort_order = Qt.AscendingOrder

        self.table.horizontalHeader().setSortIndicator(self.current_sort_column, self.current_sort_order)
        self.current_page = 1  # Reset to first page when sorting
        self.run_query(self.search_bar.text())

    def save_column_states(self):
        header = self.table.horizontalHeader()
        self.column_states = {
            'order': [header.logicalIndex(i) for i in range(header.count())],
            'widths': [header.sectionSize(i) for i in range(header.count())]
        }

    def restore_column_states(self):
        if self.column_states:
            header = self.table.horizontalHeader()
            for visual, logical in enumerate(self.column_states['order']):
                header.moveSection(header.visualIndex(logical), visual)
            for i, width in enumerate(self.column_states['widths']):
                header.resizeSection(i, width)

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
    app.setWindowIcon(QIcon(r'"C:\Users\P0037463\Projects\PycharmProjects\Event Wizard\icon.ico"'))
    viewer = LogViewer()
    viewer.show()
    sys.exit(app.exec_())
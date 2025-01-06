import sqlite3
import os
import csv
from PyQt5.QtCore import QObject, pyqtSignal


class DatabaseManager(QObject):
    # Signals for progress updates
    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_path='logs.db'):
        super().__init__()
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.fields = []

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return self.conn
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Database connection error: {str(e)}")
            raise
    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def drop_database(self):
        """Drop the database file and reset connections"""
        self.close_connection()
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                self.operation_completed.emit("Database dropped successfully")
        except Exception as e:
            self.error_occurred.emit(f"Error dropping database: {str(e)}")
            raise

    def load_csv(self, csv_file):
        """Load CSV file into database"""
        try:
            self.drop_database()
            self.connect()

            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                self.fields = next(csv_reader)  # Read header row

                # Create table with detected fields
                create_table_sql = f"CREATE TABLE logs ({', '.join([f'[{field}] TEXT' for field in self.fields])})"
                self.cursor.execute(create_table_sql)

                # Prepare SQL for insertion
                insert_sql = f"INSERT INTO logs ({', '.join(['[' + field + ']' for field in self.fields])}) VALUES ({', '.join(['?' for _ in self.fields])})"

                # Count total rows for progress calculation
                total_rows = sum(1 for _ in csv_reader)
                f.seek(0)
                next(csv_reader)  # Skip header row again

                # Insert data in chunks
                chunk_size = 10000
                for i in range(0, total_rows, chunk_size):
                    chunk = []
                    for _ in range(min(chunk_size, total_rows - i)):
                        try:
                            chunk.append(next(csv_reader))
                        except StopIteration:
                            break

                    self.cursor.executemany(insert_sql, chunk)
                    self.conn.commit()

                    # Update progress
                    progress = int((i + len(chunk)) / total_rows * 100)
                    self.progress_updated.emit(progress)

            self.operation_completed.emit(f"CSV loaded successfully. Detected {len(self.fields)} fields.")
            return self.fields

        except Exception as e:
            self.error_occurred.emit(f"Error loading CSV: {str(e)}")
            raise

    def execute_query(self, query, params=None):
        """Execute a SQL query and return results"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Query execution error: {str(e)}")
            raise

    def get_column_names(self):
        """Get current table column names"""
        return self.fields

    def get_total_rows(self, query):
        """Get total number of rows for a query"""
        try:
            count_query = f"SELECT COUNT(*) FROM ({query})"
            self.cursor.execute(count_query)
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Error counting rows: {str(e)}")
            raise

    def get_paginated_data(self, query, page, rows_per_page):
        """Get paginated data for a query"""
        try:
            offset = (page - 1) * rows_per_page
            paginated_query = f"{query} LIMIT {rows_per_page} OFFSET {offset}"
            return self.execute_query(paginated_query)
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Error retrieving paginated data: {str(e)}")
            raise

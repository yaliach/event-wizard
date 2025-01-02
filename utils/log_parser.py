import os
import subprocess
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class LogParserWorker(QThread):
    start_parsing = pyqtSignal()
    parser_finished = pyqtSignal(bool, str)

    def __init__(self, input_dir, output_dir):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.is_cancelled = False

    def process_parsing(self):
        try:
            self.start_parsing.emit()

            # Execute EvtxECmd
            process = subprocess.Popen(
                [
                    'EvtxECmd',
                    '-d', self.input_dir,
                    '--csv', self.output_dir
                ],
                stdout=subprocess.DEVNULL,  # Suppress stdout
                stderr=subprocess.PIPE,  # Keep stderr for error checking
                universal_newlines=True
            )

            # Wait for process to complete
            _, stderr = process.communicate()

            # Check if process was successful
            if process.returncode == 0:
                self.parser_finished.emit(True, self.output_dir)
            else:
                self.parser_finished.emit(False, f"EvtxECmd failed: {stderr}")

        except Exception as e:
            self.parser_finished.emit(False, str(e))

    def run(self):
        """Required override of QThread's run method"""
        self.process_parsing()

    def stop_parsing(self):
        """Cancel the parsing operation"""
        self.is_cancelled = True


class LogParser(QObject):
    def __init__(self):
        super().__init__()
        self.worker = None

    def start_parsing(self, input_dir, output_dir):
        """
        Start parsing logs from input_dir and save to output_dir
        Returns the worker object for signal connections

        Args:
            input_dir (str): Directory containing the logs to parse
            output_dir (str): Directory where to save the parsed CSV files

        Returns:
            LogParserWorker: The worker object handling the parsing

        Raises:
            ValueError: If input directory doesn't exist
        """
        if not os.path.exists(input_dir):
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Create and return worker thread
        self.worker = LogParserWorker(input_dir, output_dir)
        return self.worker

    def cancel_parsing(self):
        """Cancel the current parsing operation if one is running"""
        if self.worker and self.worker.isRunning():
            self.worker.stop_parsing()

    @staticmethod
    def get_output_file_path(output_dir):
        """
        Get the path to the latest CSV file in the output directory

        Args:
            output_dir (str): Directory to search for CSV files

        Returns:
            str or None: Path to the latest CSV file or None if no CSV files found
        """
        try:
            csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
            if not csv_files:
                return None

            # Get the most recent CSV file
            latest_file = max(
                [os.path.join(output_dir, f) for f in csv_files],
                key=os.path.getmtime
            )
            return latest_file
        except Exception:
            return None
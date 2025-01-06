# Event Wizard 

Event Wizard is a Python-based GUI application designed for parsing and analyzing Windows Event logs. It provides an intuitive interface for working with EvtxECmd outputs and enables efficient log analysis through SQL queries.

## Features 

- Parse Windows Event logs using EvtxECmd
- Load and view parsed CSV files
- Interactive SQL query interface for log analysis
- Save and reuse frequent queries
- Dark mode support
- Detailed log entry view
- Column sorting and rearrangement

## Prerequisite

- Python 3.8 or higher
- EvtxECmd.exe (from Eric Zimmerman's tools)
- Windows operating system

## Installation

1. Clone the repository:
```bash
git clone https:/YaliAch/Event-Wizard.git
cd event-wizard
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Download EvtxECmd.exe from [Eric Zimmerman's Tools](https://ericzimmerman.github.io/#!index.md) and place it in the project directory.

## Usage

1. Start the application:
```bash
python main.py
```

2. **Parsing Logs:**
   - Click "Parse Log"
   - Select directory containing .evtx files
   - Wait for parsing to complete

3. **Loading Existing Logs:**
   - Click "Load Parsed Logs"
   - Select the CSV file to analyze

4. **Analyzing Logs:**
   - Use SQL queries in the search bar
   - Example queries:
     ```sql
     SELECT * FROM logs WHERE EventID = '4624'
     SELECT * FROM logs WHERE Channel = 'Security' AND TimeCreated LIKE '2024-01%'
     ```
   - Save frequently used queries for quick access

5. **Navigation:**
   - Use pagination controls to browse through results
   - Double-click entries to view detailed information
   - Sort columns by dragging them


## Troubleshooting

1. **Database Issues:**
   - Use "Drop DB" button to reset the database
   - Ensure write permissions in application directory

2. **Parsing Errors:**
   - Verify EvtxECmd.exe is in the correct location
   - Check input logs are not corrupted
   - Ensure sufficient disk space


## License

MIT License - see LICENSE file for details

## Acknowledgments 

- Eric Zimmerman for EvtxECmd
- PyQt team for the GUI framework


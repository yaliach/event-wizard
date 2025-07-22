# Event Wizard

Event Wizard is a powerful Python-based GUI application designed for parsing and analyzing Windows Event logs. It provides an intuitive interface for working with EvtxECmd outputs and enables efficient log analysis through SQL queries.

## Quick Start

### Option 1: Download Executable (Recommended)
1. Go to [Releases](https://github.com/YaliAch/Event-Wizard/releases)
2. Download `EventWizard.exe` from the latest release
3. Download [EvtxECmd.exe](https://ericzimmerman.github.io/#!index.md) from Eric Zimmerman's tools
4. Place both files in the same directory
5. Run `EventWizard.exe`

### Option 2: Run from Source
```bash
git clone https://github.com/YaliAch/Event-Wizard.git
cd Event-Wizard
pip install -r requirements.txt
python main.py
```

## Features

- **Event Log Parsing** - Parse Windows Event logs using EvtxECmd
- **CSV Import** - Load and view pre-parsed CSV files
- **SQL Queries** - Interactive SQL interface for advanced log analysis
- **Query Management** - Save and reuse frequent queries
- **Dark Mode** - Professional dark theme support
- **Detailed Views** - Drill down into individual log entries
- **Data Navigation** - Column sorting, rearrangement, and pagination

## Prerequisites

- **For Executable**: Windows operating system only
- **For Development**: 
  - Python 3.8 or higher
  - Windows operating system
  - EvtxECmd.exe (from Eric Zimmerman's tools)

## Usage

### Parsing Event Logs
1. Click **"Parse Log"**
2. Select directory containing `.evtx` files
3. Wait for parsing to complete
4. Analyze the results using SQL queries

### Loading Existing Data
1. Click **"Load Parsed Logs"**
2. Select the CSV file to analyze
3. Use the SQL interface for queries

### SQL Query Examples
```sql
-- Login events
SELECT * FROM logs WHERE EventID = '4624'

-- Security events from January 2024
SELECT * FROM logs WHERE Channel = 'Security' AND TimeCreated LIKE '2024-01%'

-- Failed login attempts
SELECT * FROM logs WHERE EventID = '4625'

-- Process creation events
SELECT * FROM logs WHERE EventID = '4688'
```

## Troubleshooting

### Database Issues
- Use **"Drop DB"** button to reset the database
- Ensure write permissions in application directory
- Check available disk space

### Parsing Errors
- Verify `EvtxECmd.exe` is in the correct location
- Validate input `.evtx` files are not corrupted
- Ensure sufficient disk space for output files

### Performance Tips
- Use specific date ranges in queries to improve performance
- Index frequently queried columns
- Use pagination for large result sets

## License

MIT License - see [LICENSE](LICENSE) file for details

## Issues & Support

Found a bug or have a feature request? Please open an issue on [GitHub Issues](https://github.com/YaliAch/Event-Wizard/issues).

---

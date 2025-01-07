# Data Reconciliation Tool

A Python-based tool for reconciling and validating employee data from active rosters and insurer-provided active data files.
This tool ensures data integrity by identifying discrepancies and generating detailed reports.

**Website Link:** https://endo-tool-reconciler.onrender.com

## Features

- **Data Cleaning**: Standardizes names, dates, genders, and relationships.
- **Data Validation**: Identifies invalid or missing values in key fields.
- **Matching & Reconciliation**:
  - Exact and partial matching using multiple key combinations.
  - Highlights corrections needed (e.g., name, DOB, gender, relation, etc.).
- **Error Reporting**: Generates error logs for invalid records.
- **Summary Reports**: Creates summary sheets for reconciliation results.
- **Export Results**: Saves results and error reports in a ZIP file.

## Requirements

- Python 3.7+
- Libraries: `pandas`, `numpy`, `re`, `math`, `zipfile`, `matplotlib`, `seaborn`, `plotly`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/data-reconciliation-tool.git
   ```
2. Navigate to the project directory:
   ```bash
   cd data-reconciliation-tool
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place your input files (active roster and active data) in the project directory.
2. Run the reconciliation script:
   ```bash
   python reconcile.py <active_roster_file> <active_data_file>
   ```
3. Outputs will be saved as ZIP files containing:
   - Reconciled data
   - Error logs (if any)

## Example

```bash
python reconcile.py active_roster.xlsx active_data.xlsx
```

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue.

## License

This project is licensed under the loophealth-operation team

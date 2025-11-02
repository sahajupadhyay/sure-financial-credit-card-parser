# Multi-Bank Credit Card Parser

A robust Python-based parser that extracts key information from credit card statements across multiple Indian banks.

## Features

- **Multi-Bank Support**: HDFC, ICICI, SBI, Axis Bank + Generic patterns
- **Auto-Detection**: Automatically detects bank from PDF content
- **Transaction Extraction**: Extracts top transactions with amounts and descriptions
- **Graceful Fallbacks**: Returns 'unknown' instead of crashing on unsupported formats
- **Web Interface**: Simple upload interface via Flask

## Supported Banks

✅ HDFC Bank  
✅ ICICI Bank  
✅ State Bank of India (SBI)  
✅ Axis Bank  
✅ Generic (any other bank)  

## Installation

```bash
pip3 install pdfplumber pyyaml flask python-dateutil
```

## Usage

### Web Interface
```bash
python3 app.py
```
Then open http://127.0.0.1:5001 and upload your PDF.

### Direct Usage
```python
from src.parser import Parser

parser = Parser('path/to/statement.pdf')
result = parser.parse()
print(result)
```

## Output Format

```json
{
  "issuer": "hdfc",
  "card_last4": "3458",
  "billing_cycle": {
    "start": "12/03/2023",
    "end": "12/03/2023"
  },
  "due_date": "01/04/2023",
  "total_balance": 22935.0,
  "top_transactions": [
    {
      "date": "26/02/2023",
      "description": "PAYTM NOIDA",
      "amount": 5217.5,
      "type": "debit"
    }
  ]
}
```

## Project Structure

```
credit-card-parser/
├── src/
│   ├── parser.py      # Main parser logic
│   └── utils.py       # Utility functions
├── config/
│   └── issuers.yaml   # Bank-specific patterns
├── samples/
│   └── statement.pdf  # Sample HDFC statement
├── app.py            # Flask web interface
├── requirements.txt  # Dependencies
└── README.md        # This file
```

## Robustness

- Never crashes on unknown formats
- Returns consistent JSON structure
- Auto-detects bank and uses appropriate patterns
- Graceful degradation for unsupported statements
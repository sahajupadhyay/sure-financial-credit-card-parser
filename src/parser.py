import pdfplumber
import re
from datetime import datetime
from dateutil import parser as date_parser
from src.utils import load_config, detect_issuer
import json

class StatementParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.pages = []
        self.tables = []
        self.issuer = None
        self.config = None

    def load_pdf(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            self.pages = [page.extract_text() or "" for page in pdf.pages]
            self.text = "\n".join(self.pages)
            self.tables = [page.extract_table() for page in pdf.pages if page.extract_table()]

    def detect_and_set_issuer(self):
        self.issuer = detect_issuer(self.text)
        if not self.issuer:
            raise ValueError("Issuer not detected")
        self.config = load_config()["issuers"][self.issuer]

    def extract_text_with_regex(self, pattern: str) -> str:
        match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match and match.group(1) else ""

    def extract_last4(self) -> str:
        match = re.search(self.config["last4_pattern"], self.text, re.IGNORECASE | re.DOTALL)
        if match:
            # Handle different group patterns
            groups = match.groups()
            if len(groups) >= 2 and groups[1]:  # Format like 4375XXXXXXXX4006
                return groups[1]
            elif len(groups) >= 1 and groups[0]:  # Standard format
                return groups[0]
        return ""

    def extract_due_date(self) -> str:
        match = re.search(self.config["due_date_pattern"], self.text, re.IGNORECASE | re.DOTALL)
        if match:
            groups = match.groups()
            # Find the first non-empty group
            for group in groups:
                if group and group.strip():
                    try:
                        # Handle formats like "July 22, 2024" and "22/07/2024"
                        return date_parser.parse(group.strip(), dayfirst=True).strftime("%d %b %Y")
                    except:
                        continue
        return ""

    def extract_balance(self) -> float:
        match = re.search(self.config["balance_pattern"], self.text, re.IGNORECASE | re.DOTALL)
        if match:
            groups = match.groups()
            # Find the first non-empty group
            for group in groups:
                if group and group.strip():
                    try:
                        return float(group.replace(",", "").replace("₹", "").replace("Rs.", "").replace("`", "").strip())
                    except:
                        continue
        return 0.0

    def extract_billing_cycle(self) -> dict:
        # Try direct pattern matching first
        text = re.sub(r'\s+', ' ', self.text.lower())
        patterns = [
            r"statement.*?(\d{1,2}[\/\-\s][a-z]{3,9}[\/\-\s]\d{4}).*?(\d{1,2}[\/\-\s][a-z]{3,9}[\/\-\s]\d{4})",
            r"from.*?(\d{1,2}[\/\-\s][a-z]{3,9}[\/\-\s]\d{4}).*?to.*?(\d{1,2}[\/\-\s][a-z]{3,9}[\/\-\s]\d{4})",
            r"period.*?(\d{1,2}[\/\-\s][a-z]{3,9}[\/\-\s]\d{4}).*?(\d{1,2}[\/\-\s][a-z]{3,9}[\/\-\s]\d{4})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m and len(m.groups()) == 2:
                try:
                    s = date_parser.parse(m.group(1), dayfirst=True).strftime("%d %b %Y")
                    e = date_parser.parse(m.group(2), dayfirst=True).strftime("%d %b %Y")
                    return {"start": s, "end": e}
                except:
                    continue
        
        # Fallback: Calculate from statement date or due date
        ref_date = None
        stmt_match = re.search(r"statement\s*date[:\s]*(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
        if stmt_match:
            try:
                ref_date = date_parser.parse(stmt_match.group(1), dayfirst=True)
            except:
                pass
        
        # If no statement date, try due date
        if not ref_date:
            due_match = re.search(r"due.*?date.*?(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
            if due_match:
                try:
                    from datetime import timedelta
                    due_date = date_parser.parse(due_match.group(1), dayfirst=True)
                    ref_date = due_date - timedelta(days=20)  # Approximate statement date
                except:
                    pass
        
        if ref_date:
            try:
                from datetime import timedelta
                cycle_start = ref_date - timedelta(days=30)
                cycle_end = ref_date - timedelta(days=1)
                return {
                    "start": cycle_start.strftime("%d %b %Y"),
                    "end": cycle_end.strftime("%d %b %Y")
                }
            except:
                pass
        
        return {"start": "", "end": ""}

    def extract_transactions(self, max_n=5) -> list:
        trans = []
        
        # Try table extraction first
        for table in self.tables:
            if not table or len(table) < 2: continue
            
            # For ICICI format: [Date, SerNo, Description, Intl, Amount]
            for row in table:
                if not row or len(row) < 3: continue
                
                # Check if first column looks like a date
                date_str = str(row[0]).strip() if row[0] else ""
                if not re.match(r'\d{2}/\d{2}/\d{4}', date_str): continue
                
                # Find description (usually column 2)
                desc = str(row[2]).strip() if len(row) > 2 and row[2] else ""
                if not desc or desc == 'None': continue
                
                # Find amount (usually last column)
                amt_str = str(row[-1]).strip() if row[-1] else ""
                if not amt_str or amt_str == 'None': continue
                
                try:
                    # Clean amount string
                    clean_amt = amt_str.replace(",", "").replace("₹", "").replace("Rs.", "").replace("`", "")
                    is_credit = "cr" in clean_amt.lower()
                    clean_amt = clean_amt.replace(" CR", "").replace(" DR", "").strip()
                    
                    amount = float(clean_amt)
                    # Keep credits as positive, debits as negative
                    if not is_credit: amount = -amount
                    
                    trans.append({
                        "date": date_str,
                        "desc": desc,
                        "amount": abs(amount)  # Show absolute value for clarity
                    })
                except: 
                    continue
        
        # If no table transactions, try text-based extraction
        if not trans:
            lines = self.text.split('\n')
            for line in lines:
                # Pattern: Date Description Amount
                match = re.search(r'(\d{2}/\d{2}/\d{4})\s+([A-Z][A-Za-z\s]+?)\s+([\d,]+\.?\d{0,2})', line.strip())
                if match:
                    try:
                        date = match.group(1)
                        desc = match.group(2).strip()
                        amount = float(match.group(3).replace(',', ''))
                        trans.append({"date": date, "desc": desc, "amount": amount})
                    except: continue
        
        # Sort by amount (highest first) and return top N
        trans.sort(key=lambda x: x["amount"], reverse=True)
        return trans[:max_n]

    def parse(self) -> dict:
        self.load_pdf()
        self.detect_and_set_issuer()
        return {
            "issuer": self.issuer,
            "card_last4": self.extract_last4(),
            "billing_cycle": self.extract_billing_cycle(),
            "due_date": self.extract_due_date(),
            "total_balance": self.extract_balance(),
            "top_transactions": self.extract_transactions()
        }
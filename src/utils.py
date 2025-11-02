import yaml
import re
from dateutil import parser

def load_config(issuer_name="hdfc"):
    import os
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "..", "config", "issuers.yaml")
    
    with open(config_path) as f:
        return yaml.safe_load(f)

def detect_issuer(text):
    """
    Auto-detect the bank/issuer from the PDF text
    """
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "..", "config", "issuers.yaml")
    
    with open(config_path) as f:
        all_configs = yaml.safe_load(f)["issuers"]
    
    text_lower = text.lower()
    
    # Check each issuer's keywords
    for issuer, config in all_configs.items():
        if issuer == "generic":  # Skip generic for auto-detection
            continue
            
        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in text_lower:
                print(f"Detected issuer: {issuer.upper()} (matched keyword: '{keyword}')")
                return issuer
    
    # No specific issuer detected, use generic patterns
    print("No specific issuer detected, using generic patterns")
    return "generic"

def extract(pattern, text):
    """Extract information using regex pattern"""
    if not pattern or not text:
        return None
    
    match = re.search(pattern, text, re.I | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def extract_with_fallback(patterns, text, field_name="field"):
    """
    Try multiple patterns and fallback to generic patterns
    """
    if isinstance(patterns, str):
        patterns = [patterns]
    
    # Try each pattern
    for pattern in patterns:
        result = extract(pattern, text)
        if result:
            print(f"  ✓ Extracted {field_name} using pattern: {pattern[:50]}...")
            return result
    
    # Try generic patterns as fallback
    generic_patterns = {
        "card": [
            r"(?:Card\s+(?:No|Number))[:\s]*.*?(\d{4})(?:\s|$)",
            r"\b(\d{4})\s*(?:XXXX|X{4}|\*{4})",
            r"(?:ending|last).*?(\d{4})"
        ],
        "date": [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
            r"(\d{2}\s+\w+\s+\d{4})"
        ],
        "amount": [
            r"(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d{0,2})",
            r"([\d,]+\.\d{2})(?:\s|$)"
        ]
    }
    
    # Try generic patterns based on field type
    if "card" in field_name.lower():
        for pattern in generic_patterns["card"]:
            result = extract(pattern, text)
            if result:
                print(f"  ⚠️  Extracted {field_name} using generic pattern")
                return result
    elif "date" in field_name.lower():
        for pattern in generic_patterns["date"]:
            result = extract(pattern, text)
            if result:
                print(f"  ⚠️  Extracted {field_name} using generic pattern")
                return result
    elif any(word in field_name.lower() for word in ["balance", "amount", "due"]):
        for pattern in generic_patterns["amount"]:
            result = extract(pattern, text)
            if result:
                print(f"  ⚠️  Extracted {field_name} using generic pattern")
                return result
    
    print(f"  ❌ Failed to extract {field_name}")
    return None

def clean_amount(s):
    if not s:
        return 0.0
    return float(s.replace(',', ''))
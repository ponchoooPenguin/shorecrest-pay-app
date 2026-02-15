"""
Parser Module - Extract structured fields from OCR text
"""

import re
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal, InvalidOperation


@dataclass
class InvoiceData:
    """Structured invoice data extracted from OCR"""
    vendor_name: str
    total_completed: Decimal  # Total completed & stored to date
    amount_due: Decimal       # 90% of total (or explicitly stated)
    retainage: Decimal        # 10% of total (or explicitly stated)
    commitment_id: Optional[str] = None  # From CSV lookup
    cost_code: Optional[str] = None      # From CSV lookup
    raw_text: str = ""        # Original OCR text for reference


def parse_currency(text: str) -> Optional[Decimal]:
    """
    Parse a currency string into a Decimal.
    Handles: $1,234.56, 1234.56, $1,234, etc.
    """
    if not text:
        return None
    
    # Remove $ and commas, keep digits and decimal point
    cleaned = re.sub(r'[^\d.]', '', text)
    
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def extract_vendor_name(text: str) -> Optional[str]:
    """
    Extract vendor/contractor name from AIA G702 form.
    
    Looks for company names ending in Corp, Inc, LLC, Construction, Electric, etc.
    """
    # Look for company name patterns (entities ending in Corp, Inc, LLC, etc.)
    company_patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)*\s+(?:Corp|Corporation|Inc|LLC|Co\.|Company|Management|Construction|Electric|Plumbing|Air))\b',
    ]
    
    candidates = []
    for pattern in company_patterns:
        matches = re.findall(pattern, text)  # Case sensitive to get proper names
        for match in matches:
            vendor = match.strip()
            vendor = re.sub(r'\s+', ' ', vendor)
            # Skip if it's the owner company (Shorecrest)
            if 'shorecrest' in vendor.lower():
                continue
            # Skip if it's too short
            if len(vendor) > 5:
                candidates.append(vendor)
    
    # Return the longest match (usually the full company name)
    if candidates:
        return max(candidates, key=len)
    
    # Fallback: Look for "CONTRACTOR:" section
    contractor_match = re.search(r'CONTRACTOR:\s*([A-Za-z][A-Za-z0-9\s&\-\.]+)', text, re.IGNORECASE)
    if contractor_match:
        vendor = contractor_match.group(1).strip()
        vendor = re.sub(r'\s+', ' ', vendor)
        if len(vendor) > 3 and 'shorecrest' not in vendor.lower():
            return vendor
    
    return None


def extract_total_completed(text: str) -> Optional[Decimal]:
    """
    Extract "TOTAL COMPLETED & STORED TO DATE" from AIA G702 form.
    This is line 4 on the form.
    """
    patterns = [
        r'TOTAL\s+COMPLETED\s*[&+]\s*STORED\s+TO\s+DATE\s*\$?\s*([\d,]+\.?\d*)',
        r'4\.\s*TOTAL\s+COMPLETED.*?\$\s*([\d,]+\.?\d*)',
        r'Line\s+4.*?\$\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return parse_currency(match.group(1))
    
    return None


def extract_current_payment_due(text: str) -> Optional[Decimal]:
    """
    Extract "CURRENT PAYMENT DUE" from AIA G702 form.
    This is line 8 on the form - the amount after retainage.
    """
    patterns = [
        # Look for stamp DUE first (most reliable)
        r'DUE:\s*\$\s*([\d,]+\.?\d*)',
        # Line 8 pattern
        r'8\.\s*CURRENT\s+PAYMENT\s+DUE\s*\$?\s*([\d,]+\.?\d*)',
        # General current payment due
        r'CURRENT\s+PAYMENT\s+DUE\s*\$?\s*([\d,]+\.?\d*)',
        # Look for pattern near "930" with $ before it
        r'\$\s*([\d,]+\.[\d]{2})\s*\]?\s*$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            amount = parse_currency(match.group(1))
            if amount and amount > 0:
                return amount
    
    return None


def extract_total_earned_less_retainage(text: str) -> Optional[Decimal]:
    """
    Extract "TOTAL EARNED LESS RETAINAGE" from AIA G702 form.
    This is line 6 on the form.
    """
    patterns = [
        r'TOTAL\s+EARNED\s+LESS\s+RETAINAGE[^$]*\$\s*([\d,]+\.?\d*)',
        r'6\.\s*TOTAL\s+EARNED\s+LESS\s+RETAINAGE.*?\$\s*([\d,]+\.?\d*)',
        r'Line\s+6.*?\$\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return parse_currency(match.group(1))
    
    return None


def extract_retainage(text: str, total_completed: Optional[Decimal] = None) -> Optional[Decimal]:
    """
    Extract retainage amount from AIA G702 form.
    
    Tries multiple methods:
    1. Explicit retainage value in text
    2. Calculate: Total Completed - Total Earned Less Retainage
    3. Assume 10% of total completed
    """
    # Method 1: Look for explicit retainage value
    patterns = [
        # Look for stamp RET first (most reliable)
        r'RET:\s*\$\s*([\d,]+\.?\d*)',
        # Then look for Total Retainage with $ sign
        r'Total\s+Retainage[^$]*\$\s*([\d,]+\.?\d*)',
        # Generic retainage pattern
        r'RETAINAGE[^$]*\$\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = parse_currency(match.group(1))
            if amount and amount > 0:
                return amount
    
    # Method 2: Calculate from Total Completed - Total Earned Less Retainage
    total_earned_less_ret = extract_total_earned_less_retainage(text)
    if total_completed and total_earned_less_ret:
        calculated_retainage = total_completed - total_earned_less_ret
        if calculated_retainage > 0:
            return calculated_retainage
    
    return None


def extract_existing_stamp(text: str) -> dict:
    """
    Extract any existing stamp data from the OCR text.
    Alan's invoices may already have stamps we can read.
    """
    stamp_data = {}
    
    # COM (Commitment ID)
    com_match = re.search(r'COM:\s*([A-Za-z0-9\-]+)', text, re.IGNORECASE)
    if com_match:
        stamp_data['commitment_id'] = com_match.group(1).strip()
    
    # C.C (Cost Code)
    cc_match = re.search(r'[Cc]\.?[Cc]\.?:\s*([\d\-]+)', text)
    if cc_match:
        stamp_data['cost_code'] = cc_match.group(1).strip()
    
    return stamp_data


def parse_invoice(text: str) -> InvoiceData:
    """
    Parse OCR text and extract all relevant invoice fields.
    
    Args:
        text: Raw OCR text from invoice PDF
        
    Returns:
        InvoiceData with extracted fields
    """
    # Extract vendor name
    vendor_name = extract_vendor_name(text) or "Unknown Vendor"
    
    # Extract amounts
    total_completed = extract_total_completed(text)
    current_payment = extract_current_payment_due(text)
    
    # Extract retainage (pass total_completed for fallback calculation)
    retainage = extract_retainage(text, total_completed)
    
    # Calculate if not explicitly found
    if total_completed and not current_payment:
        # Amount due is 90% of total (or total - retainage if we have retainage)
        if retainage:
            current_payment = total_completed - retainage
        else:
            current_payment = total_completed * Decimal('0.9')
    
    if total_completed and not retainage:
        # Retainage is 10% of total as last resort
        retainage = total_completed * Decimal('0.1')
    
    # Try to extract any existing stamp data
    stamp_data = extract_existing_stamp(text)
    
    return InvoiceData(
        vendor_name=vendor_name,
        total_completed=total_completed or Decimal('0'),
        amount_due=current_payment or Decimal('0'),
        retainage=retainage or Decimal('0'),
        commitment_id=stamp_data.get('commitment_id'),
        cost_code=stamp_data.get('cost_code'),
        raw_text=text
    )


if __name__ == "__main__":
    # Test with sample OCR text
    sample_text = """
    FROM CONTRACTOR:
    LUIS UGARDE 305-592-8552
    Archon Air Management Corp
    2606 NW 72nd Ave
    Miami, FL 33122
    
    4. TOTAL COMPLETED & STORED TO DATE $ 7,700.00
    
    Total Retainage $ 770.00
    
    8. CURRENT PAYMENT DUE $6,930.00
    
    COM: OAKHS
    c.c: 23-3000
    DUE: $6,930.00
    RET: $770.00
    """
    
    result = parse_invoice(sample_text)
    print(f"Vendor: {result.vendor_name}")
    print(f"Total Completed: ${result.total_completed}")
    print(f"Amount Due: ${result.amount_due}")
    print(f"Retainage: ${result.retainage}")
    print(f"Commitment ID: {result.commitment_id}")
    print(f"Cost Code: {result.cost_code}")

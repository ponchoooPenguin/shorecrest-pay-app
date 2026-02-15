# Pay Application Processor

**Automated invoice stamping for Shorecrest Construction**

## Quick Start

```bash
# Navigate to app directory
cd clients/shorecrest-alan/app

# Activate virtual environment
source .venv/bin/activate

# Run the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## What It Does

1. **Upload** a subcontractor payment application (AIA G702 form)
2. **OCR** extracts vendor name, amounts, and existing stamp data
3. **Auto-lookup** finds Commitment ID and Cost Code from your spreadsheet
4. **Verify** all fields (edit if needed)
5. **Stamp** applies approval stamp to PDF
6. **Download** the approved, stamped PDF

## Stamp Format

```
┌────────────────────────────────┐
│  COM: RES-OAKHS-13             │
│  C.C: 23-3000                  │
│  DUE: $6,930.00                │
│  RET: $770.00                  │
│  By:  Alan Sar Shalom          │
│  Date: 2/13/2026               │
└────────────────────────────────┘
```

## Files

- `app.py` - Main Streamlit application
- `modules/ocr.py` - PDF → Text extraction (Tesseract)
- `modules/parser.py` - Text → Structured fields
- `modules/lookup.py` - Vendor → Codes (CSV fuzzy match)
- `modules/stamper.py` - PDF stamp overlay (PyMuPDF)
- `data/commitments.csv` - Vendor lookup database

## Updating Vendors

To add/update vendors, edit `data/commitments.csv`:

```csv
Number,Vendor,Cost Code
RES-OAKHS-13,Archon Air,23-3000
RES-OAKHS-02,Bello Construction,03-3000
```

The system uses fuzzy matching, so "Archon Air Management Corp" will match "Archon Air".

## Requirements

- Python 3.11+
- Tesseract OCR (installed via Homebrew)
- poppler (for PDF rendering)

## Support

Built by **Blue Scarf Solutions** 🐧

For issues or feature requests, contact your BSS representative.

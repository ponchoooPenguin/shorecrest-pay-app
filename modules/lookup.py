"""
Lookup Module - CSV-based vendor → Commitment ID + Cost Code lookup
"""

import os
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from thefuzz import fuzz, process


class VendorLookup:
    """
    Lookup vendor information from commitments CSV.
    Supports fuzzy matching for vendor name variations.
    """
    
    def __init__(self, csv_path: str = None):
        """
        Initialize the lookup with CSV data.
        
        Args:
            csv_path: Path to commitments CSV. If None, uses default location.
        """
        if csv_path is None:
            # Default to data/commitments.csv relative to this module
            module_dir = Path(__file__).parent.parent
            csv_path = module_dir / "data" / "commitments.csv"
        
        self.df = pd.read_csv(csv_path)
        self.df.columns = ['commitment_id', 'vendor', 'cost_code']
        
        # Clean up data
        self.df['vendor'] = self.df['vendor'].fillna('').str.strip()
        self.df['cost_code'] = self.df['cost_code'].fillna('').str.strip()
        self.df['commitment_id'] = self.df['commitment_id'].fillna('').str.strip()
        
        # Build vendor list for fuzzy matching
        self.vendors = self.df['vendor'].tolist()
    
    def get_codes(self, vendor_name: str, threshold: int = 70) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Look up commitment ID and cost code for a vendor.
        
        Args:
            vendor_name: Name of the vendor to look up
            threshold: Minimum fuzzy match score (0-100)
        
        Returns:
            Tuple of (commitment_id, cost_code, matched_vendor_name)
            Returns (None, None, None) if no match found
        """
        if not vendor_name:
            return None, None, None
        
        # Normalize vendor name - remove common suffixes
        import re
        normalized = re.sub(r'\s+(Corp|Corporation|Inc|LLC|Co\.?|Company|Ltd)\.?$', '', vendor_name, flags=re.IGNORECASE).strip()
        
        # Try exact match first (case-insensitive)
        for name_to_try in [vendor_name, normalized]:
            exact_match = self.df[self.df['vendor'].str.lower() == name_to_try.lower()]
            if not exact_match.empty:
                row = exact_match.iloc[0]
                return (
                    row['commitment_id'] if row['commitment_id'] else None,
                    row['cost_code'] if row['cost_code'] else None,
                    row['vendor']
                )
        
        # Try fuzzy matching with multiple strategies
        best_match = None
        best_score = 0
        
        for name_to_try in [vendor_name, normalized]:
            # Strategy 1: Token sort ratio (handles word order)
            result = process.extractOne(
                name_to_try, 
                self.vendors, 
                scorer=fuzz.token_sort_ratio
            )
            if result and result[1] > best_score:
                best_match = result
                best_score = result[1]
            
            # Strategy 2: Partial ratio (handles substrings)
            result2 = process.extractOne(
                name_to_try, 
                self.vendors, 
                scorer=fuzz.partial_ratio
            )
            if result2 and result2[1] > best_score:
                best_match = result2
                best_score = result2[1]
        
        if best_match and best_score >= threshold:
            matched_vendor = best_match[0]
            row = self.df[self.df['vendor'] == matched_vendor].iloc[0]
            return (
                row['commitment_id'] if row['commitment_id'] else None,
                row['cost_code'] if row['cost_code'] else None,
                matched_vendor
            )
        
        return None, None, None
    
    def list_vendors(self) -> list:
        """Return list of all vendors in the CSV."""
        return [v for v in self.vendors if v]


# Module-level singleton for easy access
_lookup_instance = None


def get_lookup() -> VendorLookup:
    """Get or create the singleton VendorLookup instance."""
    global _lookup_instance
    if _lookup_instance is None:
        _lookup_instance = VendorLookup()
    return _lookup_instance


def lookup_vendor(vendor_name: str, threshold: int = 80) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Convenience function to look up a vendor.
    
    Returns:
        Tuple of (commitment_id, cost_code, matched_vendor_name)
    """
    return get_lookup().get_codes(vendor_name, threshold)


if __name__ == "__main__":
    # Test the lookup
    lookup = VendorLookup()
    
    test_vendors = [
        "Archon Air Management Corp",
        "Bello Construction LLC",
        "Lima Electric LLC",
        "Archon Air",  # Partial match test
        "Bello",       # Partial match test
        "Unknown Vendor",  # Should fail
    ]
    
    print("Testing vendor lookup...")
    print()
    for vendor in test_vendors:
        com_id, cost_code, matched = lookup.get_codes(vendor)
        print(f"Input: '{vendor}'")
        print(f"  → Commitment ID: {com_id}")
        print(f"  → Cost Code: {cost_code}")
        print(f"  → Matched: {matched}")
        print()

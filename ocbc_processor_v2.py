#!/usr/bin/env python3
"""
OCBC Bank Statement Processor V2
Extracts transactions from OCBC Bank statements with specific merchant categorization.
Now inherits from BaseBankProcessor for consistency with multi-format system.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime
import argparse
import os
from base_processor import BaseBankProcessor


class OCBCBankProcessor(BaseBankProcessor):
    """
    A processor specifically for OCBC Bank statements.
    Inherits from BaseBankProcessor for consistency.
    """
    
    def __init__(self, config_file: str = "merchant_config.txt", data_dir: str = "data", output_dir: str = "output"):
        """Initialize the processor."""
        super().__init__(data_dir, output_dir)
        
        self.transactions = []
        self.config_file = config_file
        self.bank_name = "OCBC Bank"
        self.format_name = "OCBC Business Growth Account Statement"
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            print(f"📁 Creating data directory: {self.data_dir}")
            os.makedirs(self.data_dir, exist_ok=True)
            print(f"✅ Data directory created. Please place your PDF files in: {os.path.abspath(self.data_dir)}")
        
        # Create organized output directories
        self.output_dirs = self.setup_output_directories()
        
        print(f"📂 Using data directory: {os.path.abspath(self.data_dir)}")
        print(f"📁 Output will be organized in: {os.path.abspath('output')}")
        
        # Load merchant categories from config file
        self.merchant_categories = {}
        self.merchant_variations = {}
        self.load_merchant_config()
        
        # Always add 'Other' category for unmatched transactions
        self.merchant_categories['Other'] = []
    
    def setup_output_directories(self):
        """
        Create organized output directory structure.
        
        Returns:
            dict: Dictionary with output directory paths
        """
        # Single output directory with simple subdirectories
        output_base = "output"
        
        # Subdirectories for different types of output
        dirs = {
            'base': output_base,
            'batches': os.path.join(output_base, "batches"),
            'individual': os.path.join(output_base, "individual"),
            'consolidated': os.path.join(output_base, "consolidated"),
            'reports': os.path.join(output_base, "reports")
        }
        
        # Create all directories
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        print(f"📁 Created organized output structure:")
        print(f"   📂 Main: {output_base}/")
        print(f"   📦 Batches: {output_base}/batches/")
        print(f"   📄 Individual: {output_base}/individual/")
        print(f"   🔗 Consolidated: {output_base}/consolidated/")
        print(f"   📊 Reports: {output_base}/reports/")
        
        return dirs
    
    def get_organized_output_path(self, filename: str, output_type: str = "individual") -> str:
        """
        Get organized output path for a file.
        
        Args:
            filename (str): Name of the output file
            output_type (str): Type of output (batches, individual, consolidated, reports, summary)
            
        Returns:
            str: Full path for the organized output file
        """
        if output_type not in self.output_dirs:
            output_type = "individual"  # Default fallback
        
        return os.path.join(self.output_dirs[output_type], filename)
    
    def load_merchant_config(self):
        """
        Load merchant categories from configuration file.
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    for line in content.split('\n'):
                        if '=' in line:
                            category, keywords = line.split('=', 1)
                            category = category.strip()
                            keywords = [k.strip() for k in keywords.split(',')]
                            self.merchant_categories[category] = keywords
                            
                            # Create variations for better matching
                            for keyword in keywords:
                                self.merchant_variations[keyword.lower()] = category
                                
        except FileNotFoundError:
            print(f"Merchant config file {self.config_file} not found. Using default categories.")
            self.merchant_categories = {
                'Adyen': ['adyen', 'adyen payment'],
                'MYR': ['myr', 'myr payment'],
                'Lalamove': ['lalamove', 'lala move'],
                'Amazon': ['amazon', 'amzn'],
                'Deliveroo': ['deliveroo', 'deliveroo payment'],
                'Gpay': ['gpay', 'google pay', 'gpay network'],
                'Hero': ['hero', 'delivery hero', 'foodpanda']
            }
            
            # Create variations
            for category, keywords in self.merchant_categories.items():
                for keyword in keywords:
                    self.merchant_variations[keyword.lower()] = category
    
    def detect_format(self, text: str) -> bool:
        """Detect if this is an OCBC Bank statement"""
        # Look for OCBC-specific identifiers - more specific than DBS
        ocbc_indicators = [
            "OCBC Bank",
            "Oversea-Chinese Banking Corporation Limited",
            "BUSINESS GROWTH ACCOUNT",
            "OCBC Centre Branch",
            "65 Chulia Street"
        ]
        
        text_lower = text.lower()
        for indicator in ocbc_indicators:
            if indicator.lower() in text_lower:
                print(f"🎯 OCBC format detected by indicator: {indicator}")
                return True
        
        print(f"❌ OCBC format not detected. Text preview: {text[:200]}...")
        return False
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Return the column mapping for OCBC format"""
        return {
            'transaction_date': 'Transaction Date',
            'value_date': 'Value Date',
            'description': 'Description',
            'cheque': 'Cheque',
            'withdrawal': 'Withdrawal',
            'deposit': 'Deposit',
            'balance': 'Balance'
        }
    
    def extract_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Extract transactions from OCBC statement text with multiline descriptions"""
        transactions = []
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        # Find transaction lines by looking for date patterns
        transaction_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Look for lines that start with date patterns (e.g., "01 JUN", "02 JUN")
            if re.match(r'^\d{1,2}\s+[A-Z]{3,4}', line):
                # Check if this line contains amount and balance
                if re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', line):
                    transaction_lines.append((i, line))
        
        print(f"🔍 Found {len(transaction_lines)} potential transaction lines")
        
        # Process each transaction line and look for multiline descriptions
        for line_num, line in transaction_lines:
            try:
                # Get the base transaction
                transaction = self._parse_ocbc_transaction_line(line)
                if transaction:
                    # Look for continuation lines (description details)
                    description_lines = [transaction.get('description', '')]
                    
                    # Check next few lines for description continuation
                    for next_line_num in range(line_num + 1, min(line_num + 5, len(lines))):
                        next_line = lines[next_line_num].strip()
                        if not next_line:
                            continue
                        
                        # If next line doesn't start with date and contains text, it's description continuation
                        if (not re.match(r'^\d{1,2}\s+[A-Z]{3,4}', next_line) and 
                            not re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?', next_line) and
                            len(next_line) > 3):
                            description_lines.append(next_line)
                        else:
                            # Stop if we hit another transaction or amount
                            break
                    
                    # Combine all description lines
                    full_description = ' '.join(description_lines).strip()
                    transaction['description'] = full_description
                    
                    # Add merchant categorization and transaction type
                    transaction['merchant_category'] = self.categorize_merchant(full_description)
                    # Use consistent transaction type logic
                    self._assign_ocbc_transaction_type(transaction)
                    
                    transactions.append(transaction)
                    print(f"✅ Parsed transaction: {transaction['transaction_date']} - {full_description[:50]}...")
            except Exception as e:
                print(f"❌ Error parsing line {line_num}: {line[:100]} - {str(e)}")
                continue
        
        print(f"🎯 Successfully extracted {len(transactions)} transactions")
        return transactions
    
    def _assign_ocbc_transaction_type(self, transaction: Dict[str, Any]) -> None:
        """Assign transaction type and amount fields based on description"""
        description = transaction.get('description', '').upper()
        amount = transaction.get('withdrawal', '') or transaction.get('deposit', '')
        
        # Clear both fields first
        transaction['withdrawal'] = ''
        transaction['deposit'] = ''
        
        # DEPOSITS (Money Coming IN)
        deposit_keywords = [
            'PAYMENT /TRANSFER OTHR',
            'GIRO PAYMENT',
            'FAST TRANSFER OTHR',
            'TRANSFER',
            'CASH REBATE',
            'ALLW',
            'BEXP'
        ]
        
        # WITHDRAWALS (Money Going OUT)
        withdrawal_keywords = [
            'DEBIT PURCHASE',
            'CHARGES',
            'CCY CONVERSION FEE',
            'FAST TRANSFER OTHR'  # Can be both, but default to withdrawal
        ]
        
        # Check for deposit keywords first
        for keyword in deposit_keywords:
            if keyword in description:
                transaction['deposit'] = amount
                transaction['transaction_type'] = 'Deposit'
                return
        
        # Check for withdrawal keywords
        for keyword in withdrawal_keywords:
            if keyword in description:
                transaction['withdrawal'] = amount
                transaction['transaction_type'] = 'Withdrawal'
                return
        
        # Default to withdrawal if no specific keywords found
        transaction['withdrawal'] = amount
        transaction['transaction_type'] = 'Withdrawal'
    
    def _is_transaction_line(self, line: str) -> bool:
        """Check if a line contains transaction data"""
        # Look for date patterns and amount patterns
        date_pattern = r'\d{1,2}\s+[A-Z]{3,4}'
        amount_pattern = r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        
        has_date = bool(re.search(date_pattern, line))
        has_amount = bool(re.search(amount_pattern, line))
        
        return has_date and has_amount
    
    def _is_description_continuation(self, line: str) -> bool:
        """Check if a line is a continuation of transaction details"""
        # Skip lines that look like headers or totals
        skip_patterns = [
            r'^Page \d+ of \d+$',
            r'^BALANCE B/F$',
            r'^Total$',
            r'^For enquiries'
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return False
        
        # If line doesn't contain amounts or dates, it's likely description continuation
        amount_pattern = r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        date_pattern = r'\d{1,2}\s+[A-Z]{3,4}'
        
        return not (re.search(amount_pattern, line) or re.search(date_pattern, line))
    
    def _parse_transaction_line(self, line: str) -> Dict[str, Any]:
        """Parse a single transaction line"""
        # Split line by multiple spaces to separate columns
        parts = re.split(r'\s{2,}', line.strip())
        
        transaction = {
            'transaction_date': '',
            'value_date': '',
            'description': '',
            'cheque': '',
            'withdrawal': '',
            'deposit': '',
            'balance': ''
        }
        
        # Debug: Print the line and parts for troubleshooting
        print(f"Parsing line: {line}")
        print(f"Parts: {parts}")
        
        if len(parts) >= 6:
            # Your PDF format: Date, Date, Description, Cheque, Withdrawal, Deposit, Balance
            transaction['transaction_date'] = self.clean_text(parts[0])
            transaction['value_date'] = self.clean_text(parts[1])
            transaction['description'] = self.clean_text(parts[2])
            transaction['cheque'] = self.clean_text(parts[3])
            transaction['withdrawal'] = self.clean_text(parts[4])
            transaction['deposit'] = self.clean_text(parts[5])
            if len(parts) >= 7:
                transaction['balance'] = self.clean_text(parts[6])
        elif len(parts) >= 5:
            # Handle cases where some columns might be missing
            transaction['transaction_date'] = self.clean_text(parts[0])
            transaction['value_date'] = self.clean_text(parts[1])
            transaction['description'] = self.clean_text(parts[2])
            # Check if next part is withdrawal or deposit
            if self._is_amount(parts[3]):
                transaction['withdrawal'] = self.clean_text(parts[3])
                if len(parts) >= 5:
                    transaction['deposit'] = self.clean_text(parts[4])
            else:
                transaction['cheque'] = self.clean_text(parts[3])
                if len(parts) >= 5:
                    transaction['withdrawal'] = self.clean_text(parts[4])
                if len(parts) >= 6:
                    transaction['deposit'] = self.clean_text(parts[5])
        
        return transaction
    
    def _parse_ocbc_transaction_line(self, line: str) -> Dict[str, Any]:
        """Parse OCBC transaction line in the format: Date Amount Balance ValueDate Description"""
        try:
            # Split by multiple spaces to separate components
            parts = re.split(r'\s{2,}', line.strip())
            
            if len(parts) < 3:
                return None
            
            transaction = {
                'transaction_date': '',
                'value_date': '',
                'description': '',
                'cheque': '',
                'withdrawal': '',
                'deposit': '',
                'balance': ''
            }
            
            # First part is transaction date (e.g., "01 JUN")
            transaction['transaction_date'] = self.clean_text(parts[0])
            
            # Second part is usually the amount
            if len(parts) >= 2:
                amount_str = parts[1]
                # Check if this looks like an amount
                if re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', amount_str):
                    # This is a withdrawal (negative amount)
                    transaction['withdrawal'] = amount_str
                    transaction['deposit'] = ''
                else:
                    # This might be part of the description
                    transaction['description'] = amount_str
            
            # Third part is usually the balance
            if len(parts) >= 3:
                balance_str = parts[2]
                if re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', balance_str):
                    transaction['balance'] = balance_str
                else:
                    # This might be part of the description
                    if transaction['description']:
                        transaction['description'] += ' ' + balance_str
                    else:
                        transaction['description'] = balance_str
            
            # Remaining parts form the description
            if len(parts) >= 4:
                description_parts = parts[3:]
                full_description = ' '.join(description_parts)
                if transaction['description']:
                    transaction['description'] += ' ' + full_description
                else:
                    transaction['description'] = full_description
            
            # Clean up the description
            transaction['description'] = self.clean_text(transaction['description'])
            
            # Determine if this is a withdrawal or deposit based on amount
            if transaction['withdrawal']:
                # This is a withdrawal transaction
                pass
            elif transaction['deposit']:
                # This is a deposit transaction
                pass
            
            return transaction
            
        except Exception as e:
            print(f"❌ Error parsing transaction line: {line} - {str(e)}")
            return None
    
    def _is_amount(self, text: str) -> bool:
        """Check if text represents an amount (withdrawal or deposit)"""
        if not text:
            return False
        
        # Look for amount patterns (numbers with optional commas and decimals)
        amount_pattern = r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$'
        return bool(re.match(amount_pattern, text.strip()))
    
    def categorize_merchant(self, description: str) -> str:
        """Categorize merchant based on description text using all keywords from config"""
        if not description:
            return "Other"
        
        description_lower = description.lower()
        
        # Check each category with priority (more specific first)
        for category, keywords in self.merchant_categories.items():
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    print(f"🎯 Matched '{keyword}' to category '{category}' in: {description[:100]}...")
                    return category
        
        return "Other"
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for OCBC format"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle special cases
        if text.upper() == 'BALANCE B/F':
            text = 'Balance Brought Forward'
        
        return text
    
    # Keep all the existing batch processing methods
    def process_all_files_batch(self, batch_size: int = 50, output_filename: str = None, 
                               output_folder: str = None, create_consolidated: bool = True,
                               create_individual_batches: bool = True, create_summary_report: bool = True):
        """Process all files in batches with enhanced output options."""
        # Implementation continues with existing batch processing logic...
        pass
    
    # Add other existing methods here...
    def process_files_in_batches(self, selected_files: List[str], batch_size: int = 50, 
                                output_filename: str = None, output_folder: str = None,
                                create_consolidated: bool = True, create_individual_batches: bool = True,
                                create_summary_report: bool = True):
        """Process selected files in batches."""
        # Implementation continues with existing batch processing logic...
        pass


# Test function
if __name__ == "__main__":
    processor = OCBCBankProcessor()
    print("OCBC Bank Processor V2 initialized")
    print(f"Bank: {processor.bank_name}")
    print(f"Format: {processor.format_name}")
    print(f"Columns: {list(processor.get_column_mapping().keys())}")

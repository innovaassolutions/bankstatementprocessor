"""
Base Bank Statement Processor
Provides common interface and functionality for all bank statement processors
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd


class BaseBankProcessor(ABC):
    """Abstract base class for all bank statement processors"""
    
    def __init__(self, data_dir: str = "data", output_dir: str = "output"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.merchant_config = {}
        self.bank_name = "Unknown"
        self.format_name = "Unknown"
        
    @abstractmethod
    def detect_format(self, text: str) -> bool:
        """Detect if this processor can handle the given text format"""
        pass
    
    @abstractmethod
    def extract_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Extract transactions from the text - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """Return the column mapping for this bank format"""
        pass
    
    def load_merchant_config(self, config_file: str = "merchant_config.txt"):
        """Load merchant categorization configuration"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    for line in content.split('\n'):
                        # Skip comment lines and empty lines
                        if line.strip().startswith('#') or not line.strip():
                            continue
                        if '=' in line:
                            category, keywords = line.split('=', 1)
                            self.merchant_config[category.strip()] = [
                                k.strip() for k in keywords.split(',')
                            ]
        except FileNotFoundError:
            print(f"Merchant config file {config_file} not found. Using default categories.")
            self.merchant_config = {
                'Adyen': ['adyen', 'adyen payment'],
                'MYR': ['myr', 'myr payment'],
                'Lalamove': ['lalamove', 'lala move'],
                'Amazon': ['amazon', 'amzn'],
                'Deliveroo': ['deliveroo', 'deliveroo payment'],
                'Gpay': ['gpay', 'google pay', 'gpay network'],
                'Hero': ['hero', 'delivery hero', 'foodpanda']
            }
    
    def categorize_merchant(self, description: str) -> str:
        """Categorize merchant based on description text"""
        description_lower = description.lower()
        
        # Check each category with priority (more specific first)
        for category, keywords in self.merchant_config.items():
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return category
        
        return "Other"
    
    def determine_transaction_type(self, description: str, withdrawal: str, deposit: str) -> str:
        """Determine if transaction is withdrawal, deposit, or mixed"""
        description_lower = description.lower()
        
        # Priority system for transaction type determination
        withdrawal_keywords = ['debit purchase', 'giro payment', 'fast transfer', 'charges', 
                             'ccy conversion fee', 'fast payment', 'fund transfer', 'fast payment']
        deposit_keywords = ['payment/transfer', 'ibg giro', 'transfer', 'fund transfer', 
                           'cash rebate', 'transfer', 'remittance transfer of funds']
        
        # Check for specific deposit keywords first (higher priority)
        for keyword in deposit_keywords:
            if keyword.lower() in description_lower:
                return "Deposit"
        
        # Check for specific withdrawal keywords
        for keyword in withdrawal_keywords:
            if keyword.lower() in description_lower:
                return "Withdrawal"
        
        # Fallback to amount-based determination
        if withdrawal and float(withdrawal.replace(',', '')) > 0:
            return "Withdrawal"
        elif deposit and float(deposit.replace(',', '')) > 0:
            return "Deposit"
        
        return "Mixed"
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str or date_str.strip() == "":
            return None
        
        # Common date formats
        date_formats = [
            '%d %b %Y',    # 01 JUN 2025
            '%d-%b-%Y',    # 01-Sep-2022
            '%d/%m/%Y',    # 01/06/2025
            '%d-%m-%Y',    # 01-06-2025
            '%Y-%m-%d',    # 2025-06-01
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def save_to_excel(self, transactions: List[Dict[str, Any]], filename: str):
        """Save transactions to Excel file"""
        if not transactions:
            print("No transactions to save")
            return
        
        df = pd.DataFrame(transactions)
        
        # Create output directory if it doesn't exist
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        output_path = os.path.join(self.output_dir, filename)
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"Transactions saved to: {output_path}")
        
        return output_path
    
    def print_summary(self, transactions: List[Dict[str, Any]]):
        """Print transaction summary"""
        if not transactions:
            print("No transactions found")
            return
        
        total_withdrawals = sum(
            float(t.get('withdrawal', '0').replace(',', '')) 
            for t in transactions if t.get('withdrawal')
        )
        total_deposits = sum(
            float(t.get('deposit', '0').replace(',', '')) 
            for t in transactions if t.get('deposit')
        )
        
        print(f"\n=== {self.bank_name} Statement Summary ===")
        print(f"Total Transactions: {len(transactions)}")
        print(f"Total Withdrawals: ${total_withdrawals:,.2f}")
        print(f"Total Deposits: ${total_deposits:,.2f}")
        print(f"Net Change: ${total_deposits - total_withdrawals:,.2f}")
        
        # Merchant summary
        merchant_counts = {}
        for t in transactions:
            category = t.get('merchant_category', 'Other')
            merchant_counts[category] = merchant_counts.get(category, 0) + 1
        
        print(f"\nMerchant Categories:")
        for category, count in sorted(merchant_counts.items()):
            print(f"  {category}: {count} transactions")
    
    def process_file(self, filename: str) -> List[Dict[str, Any]]:
        """Process a single PDF file"""
        import os
        from PyPDF2 import PdfReader
        
        filepath = os.path.join(self.data_dir, filename) if not os.path.isabs(filename) else filename
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return []
        
        try:
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Detect format
            if not self.detect_format(text):
                print(f"Format not supported by {self.bank_name} processor")
                return []
            
            # Extract transactions
            transactions = self.extract_transactions(text)
            
            if transactions:
                print(f"Successfully extracted {len(transactions)} transactions from {filename}")
                return transactions
            else:
                print(f"No transactions found in {filename}")
                return []
                
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            return []
    
    def get_processor_info(self) -> Dict[str, str]:
        """Get information about this processor"""
        return {
            'bank_name': self.bank_name,
            'format_name': self.format_name,
            'supported_columns': list(self.get_column_mapping().keys())
        }
    
    def update_merchant_config(self, merchants: Dict[str, List[str]]) -> bool:
        """Update merchant configuration file"""
        try:
            with open('merchant_config.txt', 'w', encoding='utf-8') as f:
                f.write("# Merchant Categories Configuration\n")
                f.write("# Format: CategoryName = search_term1, search_term2, search_term3\n")
                f.write("# Lines starting with # are comments and ignored\n\n")
                
                for category, keywords in merchants.items():
                    if category and keywords:
                        f.write(f"{category} = {', '.join(keywords)}\n")
            
            # Reload the configuration
            self.load_merchant_config()
            return True
            
        except Exception as e:
            print(f"Error updating merchant config: {str(e)}")
            return False
    
    def add_merchant_category(self, category: str, keywords: str) -> bool:
        """Add a new merchant category"""
        try:
            # Parse keywords
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            
            if not category or not keyword_list:
                return False
            
            # Add to current config
            self.merchant_config[category] = keyword_list
            
            # Save to file
            return self.update_merchant_config(self.merchant_config)
            
        except Exception as e:
            print(f"Error adding merchant category: {str(e)}")
            return False
    
    def delete_merchant_category(self, category: str) -> bool:
        """Delete a merchant category"""
        try:
            if category in self.merchant_config:
                del self.merchant_config[category]
                return self.update_merchant_config(self.merchant_config)
            return False
            
        except Exception as e:
            print(f"Error deleting merchant category: {str(e)}")
            return False
    
    def get_merchant_config(self) -> Dict[str, List[str]]:
        """Get current merchant configuration"""
        return self.merchant_config

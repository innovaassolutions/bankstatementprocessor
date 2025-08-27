"""
DBS Bank Statement Processor
Handles DBS Bank statement format with columns:
Transaction Date, Value Date, Transaction Details, Withdrawal, Deposit, Balance
"""

import re
from typing import List, Dict, Any
from base_processor import BaseBankProcessor


class DBSBankProcessor(BaseBankProcessor):
    """Processor for DBS Bank statements"""
    
    def __init__(self, data_dir: str = "data", output_dir: str = "output"):
        super().__init__(data_dir, output_dir)
        self.bank_name = "DBS Bank"
        self.format_name = "DBS Corporate Account Statement"
        
        # Load merchant configuration
        self.load_merchant_config()
    
    def detect_format(self, text: str) -> bool:
        """Detect if this is a DBS Bank statement"""
        # Look for DBS-specific identifiers - more specific than OCBC
        dbs_indicators = [
            "DBS Bank Ltd",
            "DBS Corporate Current Account",
            "Marina Bay Financial Centre",
            "www.dbs.com"
        ]
        
        text_lower = text.lower()
        for indicator in dbs_indicators:
            if indicator.lower() in text_lower:
                print(f"🎯 DBS format detected by indicator: {indicator}")
                return True
        
        print(f"❌ DBS format not detected. Text preview: {text[:200]}...")
        return False
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Return the column mapping for DBS format"""
        return {
            'transaction_date': 'Transaction Date',
            'value_date': 'Value Date', 
            'transaction_details': 'Transaction Details',
            'withdrawal': 'Withdrawal',
            'deposit': 'Deposit',
            'balance': 'Balance'
        }
    
    def extract_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Extract transactions from DBS statement text"""
        transactions = []
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        # Find transaction lines by looking for ALL DBS transaction formats
        transaction_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Format 1: "01-Sep-22 580.00 REMITTANCE..." (starts with date)
            if re.match(r'^\d{1,2}-[A-Za-z]{3}-\d{2}\s+\d{1,3}(?:,\d{3})*(?:\.\d{2})?', line):
                transaction_lines.append((i, line))
                continue
            
            # Format 2: "273.92 01-Sep-22 FAST PAYMENT..." (amount first, then date)
            if re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s+\d{1,2}-[A-Za-z]{3}-\d{2}', line):
                transaction_lines.append((i, line))
                continue
            
            # Format 3: "BELGARATH INVESTMENTS PTE. LTD. SGD 58001-Sep-22 540.14" (date embedded)
            if re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\d{1,2}-[A-Za-z]{3}-\d{2}', line):
                transaction_lines.append((i, line))
                continue
        
        print(f"🔍 Found {len(transaction_lines)} potential DBS transaction lines")
        
        # Process each transaction line and look for multiline descriptions
        for line_num, line in transaction_lines:
            try:
                # Get the base transaction
                transaction = self._parse_dbs_transaction_line(line)
                if transaction:
                    # Look for continuation lines (description details)
                    description_lines = [transaction.get('transaction_details', '')]
                    
                    # Check next few lines for description continuation
                    for next_line_num in range(line_num + 1, min(line_num + 5, len(lines))):
                        next_line = lines[next_line_num].strip()
                        if not next_line:
                            continue
                        
                        # If next line doesn't start with date and contains text, it's description continuation
                        if (not re.match(r'^\d{1,2}-[A-Za-z]{3}-\d{2}', next_line) and 
                            not re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?', next_line) and
                            len(next_line) > 3):
                            description_lines.append(next_line)
                        else:
                            # Stop if we hit another transaction or amount
                            break
                    
                    # Combine all description lines
                    full_description = ' '.join(description_lines).strip()
                    transaction['transaction_details'] = full_description
                    
                    # Add merchant categorization and transaction type
                    transaction['merchant_category'] = self.categorize_merchant(full_description)
                    transaction['transaction_type'] = self.determine_transaction_type(
                        full_description,
                        transaction.get('withdrawal', ''),
                        transaction.get('deposit', '')
                    )
                    
                    transactions.append(transaction)
                    print(f"✅ Parsed DBS transaction: {transaction['transaction_date']} - {full_description[:50]}...")
            except Exception as e:
                print(f"❌ Error parsing DBS line {line_num}: {line[:100]} - {str(e)}")
                continue
        
        print(f"🎯 Successfully extracted {len(transactions)} DBS transactions")
        return transactions
    
    def _is_transaction_line(self, line: str) -> bool:
        """Check if a line contains transaction data"""
        # Look for date patterns and amount patterns
        date_pattern = r'\d{1,2}-[A-Za-z]{3}-\d{2,4}|\d{1,2}\s+[A-Za-z]{3,4}\s+\d{2,4}'
        amount_pattern = r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        
        has_date = bool(re.search(date_pattern, line))
        has_amount = bool(re.search(amount_pattern, line))
        
        return has_date and has_amount
    
    def _is_description_continuation(self, line: str) -> bool:
        """Check if a line is a continuation of transaction details"""
        # Skip lines that look like headers or totals
        skip_patterns = [
            r'^Page \d+ of \d+$',
            r'^Balance Brought Forward$',
            r'^Total$',
            r'^Currency:',
            r'^Account No:'
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return False
        
        # If line doesn't contain amounts or dates, it's likely description continuation
        amount_pattern = r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        date_pattern = r'\d{1,2}-[A-Za-z]{3}-\d{2,4}|\d{1,2}\s+[A-Za-z]{3,4}\s+\d{2,4}'
        
        return not (re.search(amount_pattern, line) or re.search(date_pattern, line))
    
    def _parse_transaction_line(self, line: str) -> Dict[str, Any]:
        """Parse a single transaction line"""
        # Split line by multiple spaces to separate columns
        parts = re.split(r'\s{2,}', line.strip())
        
        transaction = {
            'transaction_date': '',
            'value_date': '',
            'transaction_details': '',
            'withdrawal': '',
            'deposit': '',
            'balance': ''
        }
        
        if len(parts) >= 6:
            # Standard format: Date, Date, Description, Withdrawal, Deposit, Balance
            transaction['transaction_date'] = self.clean_text(parts[0])
            transaction['value_date'] = self.clean_text(parts[1])
            transaction['transaction_details'] = self.clean_text(parts[2])
            transaction['withdrawal'] = self.clean_text(parts[3])
            transaction['deposit'] = self.clean_text(parts[4])
            transaction['balance'] = self.clean_text(parts[5])
        elif len(parts) >= 5:
            # Handle cases where description might be missing
            transaction['transaction_date'] = self.clean_text(parts[0])
            transaction['value_date'] = self.clean_text(parts[1])
            transaction['withdrawal'] = self.clean_text(parts[2])
            transaction['deposit'] = self.clean_text(parts[3])
            transaction['balance'] = self.clean_text(parts[4])
        elif len(parts) >= 4:
            # Handle cases with minimal data
            transaction['transaction_date'] = self.clean_text(parts[0])
            transaction['value_date'] = self.clean_text(parts[1])
            transaction['balance'] = self.clean_text(parts[3])
        
        return transaction
    
    def _parse_dbs_transaction_line(self, line: str) -> Dict[str, Any]:
        """Parse DBS transaction line in multiple formats"""
        try:
            transaction = {
                'transaction_date': '',
                'value_date': '',
                'transaction_details': '',
                'withdrawal': '',
                'deposit': '',
                'balance': ''
            }
            
            # Format 1: "01-Sep-22 580.00 REMITTANCE..." (starts with date)
            if re.match(r'^\d{1,2}-[A-Za-z]{3}-\d{2}\s+\d{1,3}(?:,\d{3})*(?:\.\d{2})?', line):
                parts = line.strip().split()
                if len(parts) >= 3:
                    transaction['transaction_date'] = self.clean_text(parts[0])
                    transaction['withdrawal'] = parts[1]
                    transaction['transaction_details'] = ' '.join(parts[2:])
                    transaction['value_date'] = transaction['transaction_date']
            
            # Format 2: "273.92 01-Sep-22 FAST PAYMENT..." (amount first, then date)
            elif re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s+\d{1,2}-[A-Za-z]{3}-\d{2}', line):
                parts = line.strip().split()
                if len(parts) >= 3:
                    transaction['withdrawal'] = parts[0]
                    transaction['transaction_date'] = self.clean_text(parts[1])
                    transaction['transaction_details'] = ' '.join(parts[2:])
                    transaction['value_date'] = transaction['transaction_date']
            
            # Format 3: "BELGARATH INVESTMENTS PTE. LTD. SGD 58001-Sep-22 540.14" (date embedded)
            elif re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\d{1,2}-[A-Za-z]{3}-\d{2}', line):
                # Extract amount and date using regex
                amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', line)
                date_match = re.search(r'(\d{1,2}-[A-Za-z]{3}-\d{2})', line)
                
                if amount_match and date_match:
                    transaction['withdrawal'] = amount_match.group(1)
                    transaction['transaction_date'] = self.clean_text(date_match.group(1))
                    transaction['transaction_details'] = line.replace(amount_match.group(1), '').replace(date_match.group(1), '').strip()
                    transaction['value_date'] = transaction['transaction_date']
            
            # Clean up the description
            transaction['transaction_details'] = self.clean_text(transaction['transaction_details'])
            
            # Determine transaction type and assign amounts correctly
            self._assign_dbs_transaction_type(transaction)
            
            print(f"🔍 Parsed DBS transaction: Date={transaction['transaction_date']}, Amount={transaction.get('withdrawal', transaction.get('deposit', ''))}, Type={transaction.get('transaction_type', 'Unknown')}, Desc={transaction['transaction_details'][:50]}...")
            
            return transaction
            
        except Exception as e:
            print(f"❌ Error parsing DBS transaction line: {line} - {str(e)}")
            return None
    
    def _assign_dbs_transaction_type(self, transaction: Dict[str, Any]) -> None:
        """Assign transaction type and amount fields based on description"""
        description = transaction.get('transaction_details', '').upper()
        amount = transaction.get('withdrawal', '')
        
        # Clear both fields first
        transaction['withdrawal'] = ''
        transaction['deposit'] = ''
        
        # DEPOSITS (Money Coming IN)
        deposit_keywords = [
            'REMITTANCE TRANSFER OF FUNDS RTF',
            'IBG GIRO',
            'TRANSFER',
            'CASH TRANSACTION'  # Based on your updated document
        ]
        
        # WITHDRAWALS (Money Going OUT)
        withdrawal_keywords = [
            'FAST PAYMENT',
            'GIRO PAYMENT',
            'SERVICE CHARGE',
            'INTERBANK GIRO IBG'
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
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for DBS format"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle special cases
        if text.lower() == 'balance b/f':
            text = 'Balance Brought Forward'
        
        return text


# Test function
if __name__ == "__main__":
    processor = DBSBankProcessor()
    print("DBS Bank Processor initialized")
    print(f"Bank: {processor.bank_name}")
    print(f"Format: {processor.format_name}")
    print(f"Columns: {list(processor.get_column_mapping().keys())}")

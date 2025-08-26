#!/usr/bin/env python3
"""
OCBC Bank Statement Processor
Extracts transactions from OCBC Bank statements with specific merchant categorization.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime
import argparse
import os

class OCBCBankProcessor:
    """
    A processor specifically for OCBC Bank statements.
    """
    
    def __init__(self, config_file: str = "merchant_config.txt", data_dir: str = "data"):
        """Initialize the processor."""
        self.transactions = []
        self.config_file = config_file
        self.data_dir = data_dir
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            print(f"📁 Creating data directory: {self.data_dir}")
            os.makedirs(self.data_dir)
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
            print(f"📋 Loading merchant configuration from: {self.config_file}")
            
            if not Path(self.config_file).exists():
                print(f"⚠️  Configuration file '{self.config_file}' not found. Using default categories.")
                self.load_default_categories()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                try:
                    # Parse format: CategoryName = search_term1, search_term2, search_term3
                    if '=' in line:
                        category_name, search_terms = line.split('=', 1)
                        category_name = category_name.strip()
                        search_terms = [term.strip() for term in search_terms.split(',')]
                        
                        if category_name and search_terms:
                            # First search term becomes the main category name
                            main_name = search_terms[0]
                            
                            # Initialize the category
                            self.merchant_categories[main_name] = []
                            self.merchant_variations[main_name] = search_terms
                            
                            print(f"✅ Loaded category: {main_name} (search terms: {', '.join(search_terms)})")
                        else:
                            print(f"⚠️  Invalid format on line {line_num}: {line}")
                    else:
                        print(f"⚠️  Missing '=' on line {line_num}: {line}")
                        
                except Exception as e:
                    print(f"⚠️  Error parsing line {line_num}: {line} - {str(e)}")
            
            print(f"📊 Loaded {len(self.merchant_categories)} merchant categories")
            
        except Exception as e:
            print(f"❌ Error loading configuration: {str(e)}")
            print("🔄 Falling back to default categories...")
            self.load_default_categories()
    
    def load_default_categories(self):
        """
        Load default merchant categories if config file fails.
        """
        print("📋 Loading default merchant categories...")
        
        self.merchant_categories = {
            'Adyen': [],
            'MYR': [],
            'Lalamove': [],
            'Amazon': [],
            'Deliveroo': [],
            'Gpay': [],
            'Hero': [],
            'Other': []
        }
        
        self.merchant_variations = {
            'Adyen': ['adyen', 'ADYEN'],
            'MYR': ['myr', 'MYR', 'Malaysian Ringgit'],
            'Lalamove': ['lalamove', 'LALAMOVE', 'LalaMove'],
            'Amazon': ['amazon', 'AMAZON', 'Amazon.com'],
            'Deliveroo': ['deliveroo', 'DELIVEROO'],
            'Gpay': ['gpay', 'GPAY', 'Google Pay'],
            'Hero': ['hero', 'HERO', 'Hero Supermarket']
        }
        
        print("✅ Default categories loaded")
    
    def reload_config(self):
        """
        Reload merchant configuration from file.
        """
        print("🔄 Reloading merchant configuration...")
        self.merchant_categories = {}
        self.merchant_variations = {}
        self.load_merchant_config()
        self.merchant_categories['Other'] = []  # Always add Other category
    
    def add_merchant_category(self, category_name: str, search_terms: List[str]):
        """
        Add a new merchant category programmatically.
        
        Args:
            category_name (str): Name of the category
            search_terms (List[str]): List of search terms
        """
        if category_name and search_terms:
            self.merchant_categories[category_name] = []
            self.merchant_variations[category_name] = search_terms
            print(f"✅ Added category: {category_name} with search terms: {', '.join(search_terms)}")
    
    def remove_merchant_category(self, category_name: str):
        """
        Remove a merchant category.
        
        Args:
            category_name (str): Name of the category to remove
        """
        if category_name in self.merchant_categories and category_name != 'Other':
            del self.merchant_categories[category_name]
            del self.merchant_variations[category_name]
            print(f"✅ Removed category: {category_name}")
        else:
            print(f"⚠️  Cannot remove '{category_name}' category")
    
    def list_merchant_categories(self):
        """
        List all current merchant categories and their search terms.
        """
        print("\n📋 Current Merchant Categories:")
        print("-" * 60)
        
        for category, search_terms in self.merchant_variations.items():
            if category != 'Other':
                print(f"🏪 {category}: {', '.join(search_terms)}")
        
        print(f"\n📊 Total categories: {len(self.merchant_categories) - 1} (excluding 'Other')")

    def get_merchant_config(self):
        """Get current merchant configuration as dictionary for API"""
        config = {}
        for category, search_terms in self.merchant_variations.items():
            if category != 'Other':
                config[category] = search_terms
        return config

    def update_merchant_config(self, merchants):
        """Update merchant configuration file from API"""
        try:
            # Clear current configuration
            self.merchant_categories.clear()
            self.merchant_variations.clear()
            
            # Write new configuration to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write("# Merchant Categories Configuration\n")
                f.write("# Format: CategoryName = search_term1, search_term2, search_term3\n")
                f.write("# Lines starting with # are comments and ignored\n\n")
                
                for category, search_terms in merchants.items():
                    if isinstance(search_terms, list) and search_terms:
                        # Format: Category = term1, term2, term3
                        terms_str = ', '.join(search_terms)
                        f.write(f"{category} = {terms_str}\n")
            
            # Reload configuration
            self.load_merchant_config()
            print(f"✅ Merchant configuration updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error updating merchant config: {e}")
            return False

    def add_merchant_category(self, category, keywords):
        """Add a new merchant category from API"""
        try:
            # Parse keywords
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            
            if not keyword_list:
                print("❌ No valid keywords provided")
                return False
            
            # Add to file
            with open(self.config_file, 'a', encoding='utf-8') as f:
                f.write(f"{category} = {', '.join(keyword_list)}\n")
            
            # Reload configuration
            self.load_merchant_config()
            print(f"✅ Added merchant category: {category}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding merchant category: {e}")
            return False

    def delete_merchant_category(self, category):
        """Delete a merchant category from API"""
        try:
            if category == 'Other':
                print("⚠️ Cannot delete 'Other' category")
                return False
            
            # Read all lines
            with open(self.config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out the category to delete
            filtered_lines = []
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped.startswith(f"{category} ="):
                    filtered_lines.append(line)
            
            # Write back to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            
            # Reload configuration
            self.load_merchant_config()
            print(f"✅ Deleted merchant category: {category}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting merchant category: {e}")
            return False
            self.merchant_variations.clear()
            
            # Write new configuration to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                for category, search_terms in merchants.items():
                    if isinstance(search_terms, list):
                        search_terms_str = ', '.join(search_terms)
                    else:
                        search_terms_str = str(search_terms)
                    f.write(f"{category} = {search_terms_str}\n")
            
            # Reload configuration
            self.load_merchant_config()
            print(f"✅ Updated merchant configuration with {len(merchants)} categories")
            return True
        except Exception as e:
            print(f"❌ Error updating merchant config: {str(e)}")
            return False

    def add_merchant_category(self, category, keywords):
        """Add a new merchant category from API"""
        try:
            # Parse keywords
            keyword_list = [k.strip() for k in keywords.split(',')]
            
            # Add to file
            with open(self.config_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{category} = {', '.join(keyword_list)}\n")
            
            # Reload configuration
            self.load_merchant_config()
            print(f"✅ Added merchant category: {category}")
            return True
        except Exception as e:
            print(f"❌ Error adding merchant category: {str(e)}")
            return False

    def delete_merchant_category(self, category):
        """Delete a merchant category from API"""
        try:
            # Read all lines
            with open(self.config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out the category to delete
            filtered_lines = []
            for line in lines:
                if not line.strip().startswith(f"{category} ="):
                    filtered_lines.append(line)
            
            # Write back to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            
            # Reload configuration
            self.load_merchant_config()
            print(f"✅ Deleted merchant category: {category}")
            return True
        except Exception as e:
            print(f"❌ Error deleting merchant category: {str(e)}")
            return False
    
    def clean_text(self, text: str) -> str:
        """
        Clean up messy PDF text extraction while preserving transaction boundaries.
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove garbage characters but preserve line breaks for transaction parsing
        cleaned = text
        
        # Remove common PDF artifacts but keep newlines
        cleaned = re.sub(r'[^\x00-\x7F\n]+', ' ', cleaned)  # Remove non-ASCII but keep newlines
        # Don't remove punctuation - it's essential for transaction descriptions
        # cleaned = re.sub(r'[^\w\s\.\,\-\+\$\n]', ' ', cleaned)  # This was too restrictive
        
        # Normalize whitespace within lines but preserve line breaks
        lines = cleaned.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Clean individual lines
            clean_line = re.sub(r'\s+', ' ', line.strip())
            if clean_line:  # Only add non-empty lines
                cleaned_lines.append(clean_line)
        
        # Rejoin with newlines
        cleaned = '\n'.join(cleaned_lines)
        
        return cleaned
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract and clean text from PDF.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Cleaned text content
        """
        try:
            print(f"📄 Processing PDF: {pdf_path}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"📊 Total pages found: {total_pages}")
                
                # Extract text from all pages
                all_text = ""
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    if page_num % 5 == 0:  # Progress indicator every 5 pages
                        print(f"⏳ Processing page {page_num}/{total_pages}")
                    
                    page_text = page.extract_text()
                    if page_text:
                        # Try to preserve some structure by looking for common patterns
                        # and adding artificial line breaks
                        page_text = re.sub(r'(\d{2}\s+[A-Z]{3})', r'\n\1', page_text)
                        page_text = re.sub(r'([\d,]+\.\d{2})', r'\1\n', page_text)
                        
                        # Preserve line breaks by adding newlines between pages
                        if all_text:  # Don't add newline before first page
                            all_text += "\n"
                        all_text += page_text
                
                print(f"✅ Successfully extracted text from {total_pages} pages")
                
                # Skip text cleaning for now - it's removing transaction data
                # cleaned_text = self.clean_text(all_text)
                # print(f"🧹 Cleaned text length: {len(cleaned_text)} characters")
                
                print(f"📊 Raw text length: {len(all_text)} characters")
                return all_text
                
        except Exception as e:
            print(f"❌ Error processing PDF: {str(e)}")
            return ""
    
    def parse_date(self, date_str: str) -> str:
        """
        Parse date string to standard format.
        
        Args:
            date_str (str): Date string like "07 APR"
            
        Returns:
            str: Formatted date
        """
        try:
            # Parse date like "07 APR" to "07/04/2025"
            date_match = re.match(r'(\d{2})\s+([A-Z]{3})', date_str.strip())
            if date_match:
                day = date_match.group(1)
                month = date_match.group(2)
                
                # Map month abbreviations to numbers
                month_map = {
                    'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
                }
                
                month_num = month_map.get(month, '00')
                year = '2025'  # From the filename
                
                return f"{day}/{month_num}/{year}"
        except:
            pass
        
        return date_str.strip()
    
    def categorize_merchant(self, description: str) -> str:
        """
        Categorize merchant based on description with priority system.
        
        Args:
            description (str): Transaction description
            
        Returns:
            str: Merchant category
        """
        description_lower = description.lower()
        
        # Define priority order - more specific categories first
        priority_categories = [
            'hero', 'amazon', 'deliveroo', 'lalamove', 'grab', 'foodpanda', 'freshmart',
            'adyen', 'myr', 'gpay', 'bf', 'bidford', 'cyclepac', 'foodxervices',
            'savouri', 'phoon huat', 'foodedge', 'revelsystems', 'grab rides', 'gojek'
        ]
        
        # First check priority categories in order
        for category in priority_categories:
            if category in self.merchant_variations:
                for variation in self.merchant_variations[category]:
                    if variation.lower() in description_lower:
                        print(f"🔍 Categorized '{description[:50]}...' as '{category}' (matched: '{variation}')")
                        return category
        
        # Then check remaining categories
        for category, variations in self.merchant_variations.items():
            if category not in priority_categories and category != 'Other':
                for variation in variations:
                    if variation.lower() in description_lower:
                        print(f"🔍 Categorized '{description[:50]}...' as '{category}' (matched: '{variation}')")
                        return category
        
        print(f"🔍 No specific category found for '{description[:50]}...' - marked as 'Other'")
        return 'Other'
    
    def extract_transactions(self, text: str) -> List[Dict]:
        """
        Extract transactions from OCBC statement text using the correct format.
        
        Args:
            text (str): Cleaned text content
            
        Returns:
            List[Dict]: List of transaction dictionaries
        """
        print("🔍 Extracting transactions from OCBC statement...")
        
        transactions = []
        
        # Use the working approach that found 222 transactions
        # Pattern: Date + Description + Value Date + Amount
        # Example: "02 JUN PAYMENT /TRANSFER OTHR S$ MUHAMMAD HARITH BIN PayNow : NA 01 JUN 213.38"
        transaction_pattern = r'(\d{2}\s+[A-Z]{3})\s+(.+?)\s+(\d{2}\s+[A-Z]{3})\s+([\d,]+\.\d{2})'
        
        # Apply minimal text cleaning to preserve transaction data
        cleaned_text = re.sub(r'\s+', ' ', text)
        
        # Search for transaction patterns
        matches = re.findall(transaction_pattern, cleaned_text)
        
        print(f"🔍 Found {len(matches)} transaction matches")
        print(f"🔍 Raw text length: {len(text)}")
        print(f"🔍 Cleaned text length: {len(cleaned_text)}")
        
        # Debug: Show first few matches
        if matches:
            print(f"🔍 First 3 matches:")
            for i, match in enumerate(matches[:3], 1):
                date, description, value_date, amount = match
                print(f"  {i}. Date: '{date}' | Desc: '{description[:50]}...' | Value Date: '{value_date}' | Amount: '{amount}'")
        
        for match in matches:
            try:
                # Extract basic transaction info from the tuple
                date_str = match[0]  # Transaction date
                description = match[1]  # Description
                value_date_str = match[2]  # Value date
                amount_str = match[3]  # Amount
                
                # Parse amount
                amount = float(amount_str.replace(',', ''))
                
                # Improved deposit detection based on description patterns
                description_upper = description.upper()
                
                # Keywords that indicate deposits/credits (from user specification)
                deposit_keywords = [
                    'PAYMENT/TRANSFER', 'IBG GIRO', 'TRANSFER', 'FUND TRANSFER', 'CASH REBATE'
                ]
                
                # Keywords that indicate withdrawals/debits (from user specification)
                withdrawal_keywords = [
                    'DEBIT PURCHASE', 'GIRO PAYMENT', 'FAST TRANSFER', 'CHARGES', 
                    'CCY CONVERSION FEE', 'FAST PAYMENT', 'FUND TRANSFER'
                ]
                
                # Check for deposit patterns first (priority given to deposits)
                is_deposit = any(keyword in description_upper for keyword in deposit_keywords)
                
                # Check for withdrawal patterns
                is_withdrawal = any(keyword in description_upper for keyword in withdrawal_keywords)
                
                # Priority system: If both patterns match, prioritize based on business logic
                if is_deposit and is_withdrawal:
                    # Conflict resolution: Some keywords can be ambiguous
                    # Check for specific deposit indicators that should override
                    if any(keyword in description_upper for keyword in ['PAYMENT/TRANSFER', 'IBG GIRO', 'CASH REBATE']):
                        is_deposit = True
                        is_withdrawal = False
                    else:
                        # Default to withdrawal for ambiguous cases
                        is_deposit = False
                        is_withdrawal = True
                
                # If we can't determine, assume withdrawal (most common for business accounts)
                if not is_deposit and not is_withdrawal:
                    is_withdrawal = True
                
                # Determine transaction type (no more MIXED transactions)
                if is_deposit:
                    transaction_type = "DEPOSIT"
                else:
                    transaction_type = "WITHDRAWAL"
                
                # Clean up description
                full_description = re.sub(r'\s+', ' ', description).strip()
                
                # Determine currency
                currency = 'SGD'  # Default for OCBC Singapore
                if 'USD' in full_description.upper():
                    currency = 'USD'
                elif 'MYR' in full_description.upper():
                    currency = 'MYR'
                elif 'EUR' in full_description.upper():
                    currency = 'EUR'
                
                # Categorize merchant
                merchant_category = self.categorize_merchant(full_description)
                
                # Create transaction record
                transaction = {
                    'value_date': self.parse_date(value_date_str),
                    'description': full_description,
                    'withdrawal': amount if is_withdrawal else 0.0,
                    'deposit': amount if is_deposit else 0.0,
                    'merchant_category': merchant_category,
                    'currency': currency,
                    'amount_formatted': f"{currency} {amount:,.2f}"
                }
                
                transactions.append(transaction)
                
                # Add to merchant category tracking
                if merchant_category in self.merchant_categories:
                    self.merchant_categories[merchant_category].append(transaction)
                
                print(f"✅ Extracted: {transaction['value_date']} - {full_description[:50]}... - {currency} {amount:,.2f} ({transaction_type})")
                
            except (ValueError, IndexError) as e:
                print(f"⚠️  Error parsing transaction: {str(match)} - {str(e)}")
                continue
        
        print(f"🎯 Total transactions extracted: {len(transactions)}")
        self.transactions = transactions  # Store transactions for summary calculations
        return transactions
    
    def generate_merchant_summary(self) -> Dict:
        """
        Generate summary by merchant category.
        
        Returns:
            Dict: Summary by merchant category
        """
        summary = {}
        
        for category, transactions in self.merchant_categories.items():
            if transactions:
                total_withdrawal = sum(t['withdrawal'] for t in transactions)
                total_deposit = sum(t['deposit'] for t in transactions)
                count = len(transactions)
                
                summary[category] = {
                    'count': count,
                    'total_withdrawal': total_withdrawal,
                    'total_deposit': total_deposit,
                    'net_amount': total_deposit - total_withdrawal
                }
        
        return summary
    
    def calculate_totals(self) -> Dict:
        """
        Calculate overall totals.
        
        Returns:
            Dict: Summary statistics
        """
        if not self.transactions:
            return {
                'total_transactions': 0,
                'total_withdrawal': 0.0,
                'total_deposit': 0.0,
                'net_amount': 0.0
            }
        
        total_withdrawal = sum(t['withdrawal'] for t in self.transactions)
        total_deposit = sum(t['deposit'] for t in self.transactions)
        
        return {
            'total_transactions': len(self.transactions),
            'total_withdrawal': total_withdrawal,
            'total_deposit': total_deposit,
            'net_amount': total_deposit - total_withdrawal
        }
    
    def save_to_excel(self, transactions: List[Dict], output_path: str = "ocbc_transactions.xlsx", output_type: str = "individual"):
        """
        Save extracted transactions to Excel with multiple sheets.
        
        Args:
            transactions (List[Dict]): List of transaction dictionaries
            output_path (str): Path for the output Excel file
            output_type (str): Type of output for organization (individual, batches, consolidated, etc.)
        """
        if not transactions:
            print("⚠️  No transactions to save")
            return
        
        try:
            # Organize output path
            organized_path = self.get_organized_output_path(output_path, output_type)
            
            print(f"💾 Saving transactions to: {organized_path}")
            
            # Create main transactions DataFrame
            df_transactions = pd.DataFrame(transactions)
            
            # Reorder columns for better readability
            column_order = ['value_date', 'description', 'withdrawal', 'deposit', 'merchant_category', 'currency', 'amount_formatted']
            df_transactions = df_transactions[column_order]
            
            # Create merchant summary DataFrame
            merchant_summary = self.generate_merchant_summary()
            merchant_data = []
            for category, data in merchant_summary.items():
                merchant_data.append({
                    'Merchant Category': category,
                    'Transaction Count': data['count'],
                    'Total Withdrawal': data['total_withdrawal'],
                    'Total Deposit': data['total_deposit'],
                    'Net Amount': data['net_amount']
                })
            
            df_merchant_summary = pd.DataFrame(merchant_data)
            
            # Create overall summary DataFrame
            overall_summary = self.calculate_totals()
            df_overall = pd.DataFrame([overall_summary])
            
            # Save to Excel with multiple sheets
            with pd.ExcelWriter(organized_path, engine='openpyxl') as writer:
                # Transactions sheet
                df_transactions.to_excel(writer, sheet_name='All_Transactions', index=False)
                
                # Merchant summary sheet
                df_merchant_summary.to_excel(writer, sheet_name='Merchant_Summary', index=False)
                
                # Overall summary sheet
                df_overall.to_excel(writer, sheet_name='Overall_Summary', index=False)
                
                # Auto-adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            print(f"✅ Transactions saved successfully!")
            print(f"📊 Excel file contains {len(transactions)} transactions")
            print(f"📁 Organized in: {os.path.dirname(organized_path)}")
            
        except Exception as e:
            print(f"❌ Error saving to Excel: {str(e)}")
    
    def print_summary(self, transactions: List[Dict] = None):
        """Print a summary of extracted transactions and merchant categories."""
        if transactions is None:
            transactions = self.transactions

        if not transactions:
            print("\n📋 No transactions found to display")
            return
        
        print("\n" + "="*80)
        print("📋 OCBC BANK STATEMENT - TRANSACTIONS SUMMARY")
        print("="*80)
        
        # Display transactions
        print("\n📊 All Transactions:")
        print("-" * 80)
        print(f"{'Date':<12} {'Description':<40} {'Withdrawal':<12} {'Deposit':<12} {'Category':<15}")
        print("-" * 80)
        
        for transaction in transactions:
            print(f"{transaction['value_date']:<12} "
                  f"{transaction['description'][:38]:<40} "
                  f"{transaction['withdrawal']:<12.2f} "
                  f"{transaction['deposit']:<12.2f} "
                  f"{transaction['merchant_category']:<15}")
        
        # Display merchant category summary
        print("\n" + "="*80)
        print("🏪 MERCHANT CATEGORY SUMMARY")
        print("="*80)
        
        merchant_summary = self.generate_merchant_summary()
        for category, data in merchant_summary.items():
            if data['count'] > 0:
                print(f"\n📁 {category}:")
                print(f"   Transactions: {data['count']}")
                print(f"   Total Withdrawal: ${data['total_withdrawal']:,.2f}")
                print(f"   Total Deposit: ${data['total_deposit']:,.2f}")
                print(f"   Net Amount: ${data['net_amount']:,.2f}")
        
        # Display overall totals
        print("\n" + "="*80)
        print("💰 OVERALL SUMMARY")
        print("="*80)
        
        totals = self.calculate_totals()
        print(f"Total Transactions: {totals['total_transactions']}")
        print(f"Total Withdrawal: ${totals['total_withdrawal']:,.2f}")
        print(f"Total Deposit: ${totals['total_deposit']:,.2f}")
        print(f"Net Amount: ${totals['net_amount']:,.2f}")
        print("="*80)

    def get_pdf_files(self) -> List[str]:
        """
        Get a list of PDF files from the data directory.
        """
        pdf_files = []
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(self.data_dir, file))
        
        if not pdf_files:
            print(f"📁 No PDF files found in {self.data_dir}/")
            print(f"💡 Please place your PDF files in: {os.path.abspath(self.data_dir)}")
        else:
            print(f"📄 Found {len(pdf_files)} PDF file(s) in {self.data_dir}/")
            for pdf in pdf_files:
                print(f"   • {os.path.basename(pdf)}")
        
        return pdf_files

    def process_file(self, pdf_path: str) -> List[Dict]:
        """
        Process a single PDF file.
        """
        # Handle both full paths and just filenames
        if not os.path.isabs(pdf_path):
            # If just filename, look in data directory
            pdf_path = os.path.join(self.data_dir, pdf_path)
        
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            print(f"💡 Available files in {self.data_dir}/:")
            self.get_pdf_files()
            return []
        
        print(f"\n🔄 Processing: {os.path.basename(pdf_path)}")
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print(f"❌ Failed to extract text from {pdf_path}")
            return []
        
        transactions = self.extract_transactions(text)
        return transactions

    def process_all_files(self) -> List[Dict]:
        """
        Process all PDF files in the data directory.
        """
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            return []
        
        all_transactions = []
        successful_files = []
        failed_files = []
        
        for pdf_file in pdf_files:
            try:
                print(f"\n{'='*60}")
                # Pass just the filename, not the full path
                filename = os.path.basename(pdf_file)
                transactions = self.process_file(filename)
                if transactions:
                    all_transactions.extend(transactions)
                    successful_files.append(filename)
                    print(f"✅ Successfully processed: {filename} ({len(transactions)} transactions)")
                else:
                    failed_files.append(filename)
                    print(f"❌ Failed to process: {filename}")
            except Exception as e:
                filename = os.path.basename(pdf_file)
                failed_files.append(filename)
                print(f"❌ Error processing {filename}: {e}")
        
        print(f"\n{'='*60}")
        print("📊 Processing Summary:")
        print(f"✅ Successful: {len(successful_files)} files")
        print(f"❌ Failed: {len(failed_files)} files")
        print(f"📈 Total transactions: {len(all_transactions)}")
        
        if successful_files:
            print(f"\n✅ Successfully processed: {', '.join(successful_files)}")
        if failed_files:
            print(f"\n❌ Failed to process: {', '.join(failed_files)}")
        
        return all_transactions

    def process_files_in_batches(self, batch_size: int = 50, output_prefix: str = "batch", selected_files: List[str] = None) -> List[Dict]:
        """
        Process PDF files in configurable batches with individual output files.
        
        Args:
            batch_size (int): Number of files to process per batch (default: 50)
            output_prefix (str): Prefix for batch output files (default: "batch")
            selected_files (List[str]): List of specific filenames to process (if None, processes all)
            
        Returns:
            List[Dict]: All transactions from all batches
        """
        if selected_files:
            # Use only the selected files
            pdf_files = selected_files
            print(f"🎯 Processing {len(selected_files)} selected files")
        else:
            # Fall back to processing all files
            pdf_files = self.get_pdf_files()
            print(f"📁 Processing all {len(pdf_files)} files in data directory")
        
        if not pdf_files:
            print("📁 No PDF files found to process")
            return []
        
        total_files = len(pdf_files)
        total_batches = (total_files + batch_size - 1) // batch_size  # Ceiling division
        
        print(f"\n🚀 BATCH PROCESSING MODE")
        print(f"📊 Total files: {total_files}")
        print(f"📦 Batch size: {batch_size}")
        print(f"🔄 Total batches: {total_batches}")
        print("=" * 80)
        
        all_transactions = []
        batch_results = []
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_files)
            batch_files = pdf_files[start_idx:end_idx]
            
            print(f"\n📦 PROCESSING BATCH {batch_num + 1}/{total_batches}")
            print(f"📄 Files {start_idx + 1}-{end_idx} of {total_files}")
            print("-" * 60)
            
            batch_transactions = []
            successful_files = []
            failed_files = []
            
            # Process each file in the current batch
            for pdf_file in batch_files:
                try:
                    filename = os.path.basename(pdf_file)
                    print(f"🔄 Processing: {filename}")
                    
                    transactions = self.process_file(filename)
                    if transactions:
                        batch_transactions.extend(transactions)
                        successful_files.append(filename)
                        print(f"   ✅ Success: {len(transactions)} transactions")
                    else:
                        failed_files.append(filename)
                        print(f"   ❌ Failed: 0 transactions")
                        
                except Exception as e:
                    filename = os.path.basename(pdf_file)
                    failed_files.append(filename)
                    print(f"   ❌ Error: {str(e)}")
            
            # Save batch results with human-readable naming
            batch_filename = f"Batch_{batch_num + 1}_of_{total_batches}.xlsx"
            if batch_transactions:
                self.save_to_excel(batch_transactions, batch_filename, "batches")
                print(f"💾 Batch {batch_num + 1} saved: {batch_filename}")
            
            # Batch summary
            batch_summary = {
                'batch_num': batch_num + 1,
                'total_batches': total_batches,
                'files_in_batch': len(batch_files),
                'successful_files': len(successful_files),
                'failed_files': len(failed_files),
                'transactions': len(batch_transactions),
                'output_file': batch_filename,
                'successful_filenames': successful_files,
                'failed_filenames': failed_files
            }
            batch_results.append(batch_summary)
            
            # Print batch summary
            print(f"\n📊 BATCH {batch_num + 1} SUMMARY:")
            print(f"   📄 Files processed: {len(batch_files)}")
            print(f"   ✅ Successful: {len(successful_files)}")
            print(f"   ❌ Failed: {len(failed_files)}")
            print(f"   📈 Transactions: {len(batch_transactions)}")
            print(f"   💾 Output: {batch_filename}")
            
            # Add to overall results
            all_transactions.extend(batch_transactions)
            
            # Progress indicator
            progress = ((batch_num + 1) / total_batches) * 100
            print(f"📈 Overall Progress: {progress:.1f}% ({batch_num + 1}/{total_batches} batches)")
            print("=" * 80)
        
        # Final summary
        print(f"\n🎉 BATCH PROCESSING COMPLETE!")
        print("=" * 80)
        print(f"📊 FINAL SUMMARY:")
        print(f"   📦 Total batches: {total_batches}")
        print(f"   📄 Total files: {total_files}")
        print(f"   📈 Total transactions: {len(all_transactions)}")
        
        # Save consolidated results
        consolidated_filename = f"All_Files_Combined.xlsx"
        if all_transactions:
            self.save_to_excel(all_transactions, consolidated_filename, "consolidated")
            print(f"💾 Consolidated results saved: {consolidated_filename}")
        
        # Save batch summary report
        self.save_batch_summary_report(batch_results, "Batch_Processing_Summary.xlsx")
        print(f"📋 Batch summary report saved: Batch_Processing_Summary.xlsx")
        
        return all_transactions
    
    def save_batch_summary_report(self, batch_results: List[Dict], output_filename: str):
        """
        Save a summary report of all batch processing results.
        
        Args:
            batch_results (List[Dict]): List of batch result dictionaries
            output_filename (str): Name of the output Excel file
        """
        try:
            # Create summary data
            summary_data = []
            for batch in batch_results:
                summary_data.append({
                    'Batch': f"Batch {batch['batch_num']:03d}",
                    'Files_Processed': batch['files_in_batch'],
                    'Successful': batch['successful_files'],
                    'Failed': batch['failed_files'],
                    'Transactions': batch['transactions'],
                    'Output_File': batch['output_file'],
                    'Success_Rate': f"{(batch['successful_files'] / batch['files_in_batch'] * 100):.1f}%" if batch['files_in_batch'] > 0 else "0%"
                })
            
            # Create DataFrame
            df_summary = pd.DataFrame(summary_data)
            
            # Calculate totals
            total_files = sum(batch['files_in_batch'] for batch in batch_results)
            total_successful = sum(batch['successful_files'] for batch in batch_results)
            total_failed = sum(batch['failed_files'] for batch in batch_results)
            total_transactions = sum(batch['transactions'] for batch in batch_results)
            
            # Add totals row
            totals_row = {
                'Batch': 'TOTALS',
                'Files_Processed': total_files,
                'Successful': total_successful,
                'Failed': total_failed,
                'Transactions': total_transactions,
                'Output_File': f"Consolidated: {len(batch_results)} batches",
                'Success_Rate': f"{(total_successful / total_files * 100):.1f}%" if total_files > 0 else "0%"
            }
            df_summary = pd.concat([df_summary, pd.DataFrame([totals_row])], ignore_index=True)
            
            # Save to Excel with organized path
            organized_path = self.get_organized_output_path(output_filename, "reports")
            with pd.ExcelWriter(organized_path, engine='openpyxl') as writer:
                df_summary.to_excel(writer, sheet_name='Batch Summary', index=False)
                
                # Add detailed batch information
                detailed_data = []
                for batch in batch_results:
                    for filename in batch['successful_filenames']:
                        detailed_data.append({
                            'Batch': f"Batch {batch['batch_num']:03d}",
                            'Status': 'Success',
                            'Filename': filename,
                            'Transactions': batch['transactions']
                        })
                    for filename in batch['failed_filenames']:
                        detailed_data.append({
                            'Batch': f"Batch {batch['batch_num']:03d}",
                            'Status': 'Failed',
                            'Filename': filename,
                            'Transactions': 0
                        })
                
                if detailed_data:
                    df_detailed = pd.DataFrame(detailed_data)
                    df_detailed.to_excel(writer, sheet_name='File Details', index=False)
            
            print(f"✅ Batch summary report saved: {output_filename}")
            
        except Exception as e:
            print(f"❌ Error saving batch summary report: {str(e)}")

    def process_all_files_batch(self, pdf_files: List[str], batch_size: int = 50, 
                               output_filename: str = None, output_folder: str = None,
                               output_options: Dict = None) -> Dict:
        """
        Process multiple PDF files in batches with custom output settings.
        
        Args:
            pdf_files (List[str]): List of PDF filenames to process
            batch_size (int): Number of files to process in each batch
            output_filename (str): Custom filename for output (without extension)
            output_folder (str): Custom folder for output files
            output_options (Dict): Options for what output files to create
            
        Returns:
            Dict: Summary of batch processing results
        """
        # Set default output options
        if output_options is None:
            output_options = {
                'create_consolidated': True,
                'create_individual_batches': True,
                'create_summary_report': True
            }
        if not pdf_files:
            print("❌ No PDF files provided for batch processing")
            return {}
        
        print(f"🚀 Starting enhanced batch processing of {len(pdf_files)} files in batches of {batch_size}")
        
        # Override output settings if provided
        if output_folder and output_folder != 'output':
            # Create custom output directory structure
            custom_dirs = {
                'base': output_folder,
                'batches': os.path.join(output_folder, "batches"),
                'individual': os.path.join(output_folder, "individual"),
                'consolidated': os.path.join(output_folder, "consolidated"),
                'reports': os.path.join(output_folder, "reports")
            }
            
            # Create custom directories
            for dir_path in custom_dirs.values():
                os.makedirs(dir_path, exist_ok=True)
            
            # Temporarily override output directories
            original_dirs = self.output_dirs
            self.output_dirs = custom_dirs
        
        try:
            # Process files using existing batch method with selected files
            all_transactions = self.process_files_in_batches(batch_size, selected_files=pdf_files)
            
            # Get batch results for return
            batch_results = []
            total_files = len(pdf_files)
            total_batches = (total_files + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, total_files)
                batch_files = pdf_files[start_idx:end_idx]
                
                batch_results.append({
                    'batch_num': batch_num + 1,
                    'files': batch_files,
                    'files_processed': len(batch_files)
                })
            
            # Create output files based on options
            output_files = {}
            
            # Individual batch files
            if output_options.get('create_individual_batches', True):
                output_files['batches'] = [f"Batch_{b['batch_num']:03d}_of_{total_batches:03d}.xlsx" for b in batch_results]
            
            # Consolidated master file
            if output_options.get('create_consolidated', True) and all_transactions:
                consolidated_filename = f"{output_filename}_MasterData.xlsx" if output_filename else "MasterData_Consolidated.xlsx"
                consolidated_path = self.get_organized_output_path(consolidated_filename, 'consolidated')
                
                # Create comprehensive consolidated file with multiple sheets
                self.save_consolidated_master_file(all_transactions, batch_results, consolidated_path, output_filename)
                output_files['consolidated'] = consolidated_filename
                print(f"💾 Consolidated master file created: {consolidated_filename}")
            
            # Summary report
            if output_options.get('create_summary_report', True):
                summary_filename = f"{output_filename}_Summary.xlsx" if output_filename else "Batch_Processing_Summary.xlsx"
                summary_path = self.get_organized_output_path(summary_filename, "reports")
                self.save_batch_summary_report(batch_results, summary_filename)
                output_files['summary'] = summary_filename
                print(f"💾 Summary report created: {summary_filename}")
            
            return {
                'total_files': total_files,
                'total_batches': total_batches,
                'total_transactions': len(all_transactions),
                'batches': batch_results,
                'output_files': output_files
            }
            
        finally:
            # Restore original output directories
            if output_folder and output_folder != 'output':
                self.output_dirs = original_dirs

    def save_consolidated_master_file(self, all_transactions: List[Dict], batch_results: List[Dict], 
                                    output_path: str, custom_filename: str = None) -> None:
        """
        Create a comprehensive consolidated master file with multiple sheets.
        
        Args:
            all_transactions (List[Dict]): All transactions from all batches
            batch_results (List[Dict]): Summary of each batch
            output_path (str): Path where to save the file
            custom_filename (str): Custom filename prefix if provided
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                
                # Sheet 1: All Transactions (Master Data)
                if all_transactions:
                    df_transactions = pd.DataFrame(all_transactions)
                    df_transactions.to_excel(writer, sheet_name='Master_Data', index=False)
                    print(f"✅ Master data sheet created with {len(all_transactions)} transactions")
                
                # Sheet 2: Batch Summary
                if batch_results:
                    batch_summary_data = []
                    for batch in batch_results:
                        batch_summary_data.append({
                            'Batch_Number': batch['batch_num'],
                            'Files_Processed': batch['files_processed'],
                            'Files': ', '.join(batch['files'])
                        })
                    
                    df_batch_summary = pd.DataFrame(batch_summary_data)
                    df_batch_summary.to_excel(writer, sheet_name='Batch_Summary', index=False)
                    print(f"✅ Batch summary sheet created with {len(batch_results)} batches")
                
                # Sheet 3: Merchant Summary
                if all_transactions:
                    merchant_summary = self.generate_merchant_summary()
                    if merchant_summary:
                        merchant_data = []
                        for category, data in merchant_summary.items():
                            merchant_data.append({
                                'Merchant_Category': category,
                                'Transaction_Count': data['count'],
                                'Total_Withdrawal': data['total_withdrawal'],
                                'Total_Deposit': data['total_deposit'],
                                'Net_Amount': data['net_amount']
                            })
                        
                        df_merchant = pd.DataFrame(merchant_data)
                        df_merchant.to_excel(writer, sheet_name='Merchant_Summary', index=False)
                        print(f"✅ Merchant summary sheet created with {len(merchant_summary)} categories")
                
                # Sheet 4: Overall Statistics
                if all_transactions:
                    total_withdrawals = sum(t.get('withdrawal', 0) for t in all_transactions if t.get('is_withdrawal'))
                    total_deposits = sum(t.get('deposit', 0) for t in all_transactions if not t.get('is_withdrawal'))
                    
                    stats_data = [{
                        'Metric': 'Total_Transactions',
                        'Value': len(all_transactions)
                    }, {
                        'Metric': 'Total_Withdrawals',
                        'Value': total_withdrawals
                    }, {
                        'Metric': 'Total_Deposits', 
                        'Value': total_deposits
                    }, {
                        'Metric': 'Net_Amount',
                        'Value': total_deposits - total_withdrawals
                    }, {
                        'Metric': 'Total_Batches',
                        'Value': len(batch_results)
                    }]
                    
                    df_stats = pd.DataFrame(stats_data)
                    df_stats.to_excel(writer, sheet_name='Overall_Statistics', index=False)
                    print(f"✅ Overall statistics sheet created")
                
                # Sheet 5: File Processing Details
                if batch_results:
                    file_details = []
                    for batch in batch_results:
                        for filename in batch['files']:
                            file_details.append({
                                'Batch_Number': batch['batch_num'],
                                'Filename': filename,
                                'Processing_Status': 'Completed'
                            })
                    
                    df_files = pd.DataFrame(file_details)
                    df_files.to_excel(writer, sheet_name='File_Details', index=False)
                    print(f"✅ File details sheet created with {len(file_details)} files")
            
            print(f"💾 Consolidated master file saved: {output_path}")
            
        except Exception as e:
            print(f"❌ Error creating consolidated master file: {str(e)}")
            raise

    def generate_merchant_summary(self) -> Dict:
        """
        Generate a summary of transactions by merchant category.
        
        Returns:
            Dict: Summary data organized by merchant category
        """
        if not hasattr(self, 'transactions') or not self.transactions:
            return {}
        
        merchant_summary = {}
        
        for transaction in self.transactions:
            category = transaction.get('merchant_category', 'Other')
            
            if category not in merchant_summary:
                merchant_summary[category] = {
                    'count': 0,
                    'total_withdrawal': 0,
                    'total_deposit': 0,
                    'net_amount': 0
                }
            
            merchant_summary[category]['count'] += 1
            
            if transaction.get('is_withdrawal'):
                amount = transaction.get('withdrawal', 0)
                merchant_summary[category]['total_withdrawal'] += amount
                merchant_summary[category]['net_amount'] -= amount
            else:
                amount = transaction.get('deposit', 0)
                merchant_summary[category]['total_deposit'] += amount
                merchant_summary[category]['net_amount'] += amount
        
        return merchant_summary

def main():
    """Main function to run the OCBC processor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='OCBC Bank Statement Processor')
    parser.add_argument('pdf_file', nargs='?', help='PDF file to process (optional - will use data/ folder if not specified)')
    parser.add_argument('--config', choices=['list', 'reload', 'edit'], 
                       help='Configuration management: list categories, reload config, or edit instructions')
    parser.add_argument('--all', action='store_true', 
                       help='Process all PDF files in the data/ folder')
    parser.add_argument('--batch', type=int, metavar='SIZE',
                       help='Process files in batches of specified size (e.g., --batch 50)')
    parser.add_argument('--batch-prefix', default='batch',
                       help='Prefix for batch output files (default: batch)')
    parser.add_argument('--data-dir', default='data', 
                       help='Directory containing PDF files (default: data)')
    
    args = parser.parse_args()
    
    # Initialize processor with specified data directory
    processor = OCBCBankProcessor(data_dir=args.data_dir)
    
    # Handle configuration management
    if args.config:
        if args.config == 'list':
            processor.list_merchant_categories()
        elif args.config == 'reload':
            processor.reload_config()
        elif args.config == 'edit':
            print("\n📝 How to Edit Merchant Categories:")
            print("=" * 50)
            print("1. Open 'merchant_config.txt' in any text editor")
            print("2. Each line should follow this format:")
            print("   CategoryName = search_term1, search_term2, search_term3")
            print("3. Save the file")
            print("4. Run: python ocbc_processor.py --config reload")
            print("\n💡 Example lines:")
            print("   Netflix = netflix, NETFLIX, Netflix.com")
            print("   Spotify = spotify, SPOTIFY, Spotify Premium")
            print("\n📁 Config file location: merchant_config.txt")
        return
    
    # Handle file processing
    if args.batch:
        print(f"🚀 Processing files in batches of {args.batch}...")
        transactions = processor.process_files_in_batches(
            batch_size=args.batch, 
            output_prefix=args.batch_prefix
        )
        if transactions:
            processor.print_summary(transactions)
    elif args.all:
        print("🔄 Processing all PDF files in data folder...")
        transactions = processor.process_all_files()
        if transactions:
            processor.save_to_excel(transactions, "All_Files_Processed.xlsx", "consolidated")
            processor.print_summary(transactions)
    elif args.pdf_file:
        # Process specific file
        transactions = processor.process_file(args.pdf_file)
        if transactions:
            filename_base = os.path.splitext(os.path.basename(args.pdf_file))[0]
            output_file = f"{filename_base}_Processed.xlsx"
            processor.save_to_excel(transactions, output_file, "individual")
            processor.print_summary(transactions)
    else:
        # No file specified - show available options
        print("\n🎯 OCBC Bank Statement Processor")
        print("=" * 50)
        print("📁 Data directory:", os.path.abspath(args.data_dir))
        
        # Check for PDF files
        pdf_files = processor.get_pdf_files()
        
        if pdf_files:
            print(f"\n💡 Available options:")
            print("1. Process all files: python ocbc_processor.py --all")
            print("2. Process in batches: python ocbc_processor.py --batch 50")
            print("3. Process specific file: python ocbc_processor.py filename.pdf")
            print("4. List merchant categories: python ocbc_processor.py --config list")
            print("5. Reload configuration: python ocbc_processor.py --config reload")
            
            # Ask user what they want to do
            print(f"\n🤔 What would you like to do?")
            print("   Enter 'all' to process all files")
            print("   Enter 'batch 50' to process in batches of 50")
            print("   Enter a filename (e.g., '2025-04.pdf') to process specific file")
            print("   Enter 'list' to see merchant categories")
            print("   Enter 'quit' to exit")
            
            while True:
                choice = input("\n🎯 Your choice: ").strip().lower()
                
                if choice == 'quit':
                    print("👋 Goodbye!")
                    break
                elif choice == 'all':
                    transactions = processor.process_all_files()
                    if transactions:
                        processor.save_to_excel(transactions, "All_Files_Processed.xlsx", "consolidated")
                        processor.print_summary(transactions)
                    break
                elif choice.startswith('batch '):
                    try:
                        batch_size = int(choice.split()[1])
                        print(f"🚀 Processing in batches of {batch_size}...")
                        transactions = processor.process_files_in_batches(batch_size=batch_size)
                        if transactions:
                            processor.print_summary(transactions)
                        break
                    except (ValueError, IndexError):
                        print("❌ Invalid batch size. Use format: 'batch 50'")
                elif choice == 'list':
                    processor.list_merchant_categories()
                elif choice.endswith('.pdf'):
                    transactions = processor.process_file(choice)
                    if transactions:
                        filename_base = os.path.splitext(choice)[0]
                        output_file = f"{filename_base}_Processed.xlsx"
                        processor.save_to_excel(transactions, output_file, "individual")
                        processor.print_summary(transactions)
                    break
                else:
                    print("❌ Invalid choice. Please enter 'all', 'batch 50', a filename, 'list', or 'quit'")
        else:
            print(f"\n💡 To get started:")
            print(f"1. Place your PDF files in: {os.path.abspath(args.data_dir)}")
            print("2. Run: python ocbc_processor.py --all")
            print("3. Or run: python ocbc_processor.py filename.pdf")

if __name__ == "__main__":
    main()

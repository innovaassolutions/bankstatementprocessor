"""
Multi-Format Bank Statement Processor
Automatically detects bank statement formats and uses appropriate processors
"""

import os
from typing import List, Dict, Any, Optional
from base_processor import BaseBankProcessor
from ocbc_processor_v2 import OCBCBankProcessor
from dbs_processor import DBSBankProcessor


class MultiFormatProcessor:
    """Main processor that automatically detects and uses appropriate bank processors"""
    
    def __init__(self, data_dir: str = "data", output_dir: str = "output"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.merchant_config = {}
        
        # Register all available processors
        self.processors = self._register_processors()
        
        # Load merchant configuration
        self.load_merchant_config()
        
        print(f"🔧 Multi-Format Processor initialized with {len(self.processors)} bank formats:")
        for processor in self.processors:
            print(f"   ✅ {processor.bank_name} - {processor.format_name}")
    
    def _register_processors(self) -> List[BaseBankProcessor]:
        """Register all available bank processors"""
        processors = [
            OCBCBankProcessor(data_dir=self.data_dir, output_dir=self.output_dir),
            DBSBankProcessor(data_dir=self.data_dir, output_dir=self.output_dir)
        ]
        return processors
    
    def detect_bank_format(self, text: str) -> Optional[BaseBankProcessor]:
        """Detect which bank format the text represents"""
        for processor in self.processors:
            if processor.detect_format(text):
                print(f"🎯 Detected format: {processor.bank_name} - {processor.format_name}")
                return processor
        
        print("❌ No supported bank format detected")
        return None
    
    def process_file(self, filename: str) -> Dict[str, Any]:
        """Process a single PDF file with automatic format detection"""
        import os
        from PyPDF2 import PdfReader
        
        filepath = os.path.join(self.data_dir, filename) if not os.path.isabs(filename) else filename
        
        if not os.path.exists(filepath):
            return {
                'success': False,
                'error': f"File not found: {filepath}",
                'transactions': [],
                'processor_info': None
            }
        
        try:
            # Extract text from PDF
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Detect bank format
            processor = self.detect_bank_format(text)
            if not processor:
                return {
                    'success': False,
                    'error': "Unsupported bank format",
                    'transactions': [],
                    'processor_info': None
                }
            
            # Extract transactions using the detected processor
            transactions = processor.extract_transactions(text)
            
            if transactions:
                print(f"✅ Successfully extracted {len(transactions)} transactions using {processor.bank_name} processor")
                
                # Get processor information
                processor_info = processor.get_processor_info()
                
                return {
                    'success': True,
                    'transactions': transactions,
                    'processor_info': processor_info,
                    'bank_name': processor.bank_name,
                    'format_name': processor.format_name,
                    'filename': filename
                }
            else:
                return {
                    'success': False,
                    'error': f"No transactions found in {filename}",
                    'transactions': [],
                    'processor_info': processor.get_processor_info() if processor else None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error processing {filename}: {str(e)}",
                'transactions': [],
                'processor_info': None
            }
    
    def process_all_files(self) -> List[Dict[str, Any]]:
        """Process all PDF files in the data directory"""
        results = []
        
        if not os.path.exists(self.data_dir):
            print(f"❌ Data directory not found: {self.data_dir}")
            return results
        
        # Get all PDF files
        pdf_files = [f for f in os.listdir(self.data_dir) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"📁 No PDF files found in {self.data_dir}")
            return results
        
        print(f"📁 Found {len(pdf_files)} PDF files to process")
        
        for filename in pdf_files:
            print(f"\n🔄 Processing: {filename}")
            result = self.process_file(filename)
            results.append(result)
            
            if result['success']:
                print(f"✅ {filename}: {len(result['transactions'])} transactions extracted")
            else:
                print(f"❌ {filename}: {result['error']}")
        
        return results
    
    def get_supported_formats(self) -> List[Dict[str, str]]:
        """Get list of all supported bank formats"""
        formats = []
        for processor in self.processors:
            formats.append({
                'bank_name': processor.bank_name,
                'format_name': processor.format_name,
                'columns': list(processor.get_column_mapping().keys())
            })
        return formats
    
    def add_processor(self, processor: BaseBankProcessor):
        """Add a new bank processor to the registry"""
        self.processors.append(processor)
        print(f"✅ Added new processor: {processor.bank_name} - {processor.format_name}")
    
    def get_processor_by_bank(self, bank_name: str) -> Optional[BaseBankProcessor]:
        """Get a specific processor by bank name"""
        for processor in self.processors:
            if processor.bank_name.lower() == bank_name.lower():
                return processor
        return None
    
    def load_merchant_config(self, config_file: str = "merchant_config.txt"):
        """Load merchant categorization configuration"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    for line in content.split('\n'):
                        if '=' in line and not line.strip().startswith('#'):
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
    
    def save_to_excel(self, transactions: List[Dict[str, Any]], filename: str) -> str:
        """Save transactions to Excel file using the first available processor"""
        if not transactions:
            raise ValueError("No transactions to save")
        
        # Use the first processor to save (they all have the same save_to_excel method)
        if self.processors:
            return self.processors[0].save_to_excel(transactions, filename)
        else:
            raise ValueError("No processors available")


# Test function
if __name__ == "__main__":
    processor = MultiFormatProcessor()
    
    print("\n🔍 Supported Formats:")
    formats = processor.get_supported_formats()
    for fmt in formats:
        print(f"   🏦 {fmt['bank_name']}: {fmt['format_name']}")
        print(f"      Columns: {', '.join(fmt['columns'])}")
    
    print(f"\n📁 Data directory: {os.path.abspath(processor.data_dir)}")
    print(f"📁 Output directory: {os.path.abspath(processor.output_dir)}")
    
    # Test with a sample file if available
    pdf_files = [f for f in os.listdir(processor.data_dir) if f.lower().endswith('.pdf')]
    if pdf_files:
        print(f"\n🧪 Testing with first PDF file: {pdf_files[0]}")
        result = processor.process_file(pdf_files[0])
        if result['success']:
            print(f"✅ Test successful! Extracted {len(result['transactions'])} transactions")
        else:
            print(f"❌ Test failed: {result['error']}")
    else:
        print("\n📝 No PDF files found for testing. Place PDF files in the data directory to test.")

from flask import Flask, request, jsonify, send_file, render_template

# Version information
VERSION = "1.0.0"
BUILD_DATE = "2025-08-26 16:52:34"
from flask_cors import CORS
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename
from multi_format_processor import MultiFormatProcessor
import json

app = Flask(__name__)
CORS(app)

# Global configuration for file locations
FILE_CONFIG = {
    'upload_folder': 'uploads',
    'output_folder': 'output',
    'data_folder': 'data'
}

def get_upload_folder():
    """Get the current upload folder path"""
    return os.path.join(os.getcwd(), FILE_CONFIG['upload_folder'])

def get_output_folder():
    """Get the current output folder path"""
    return os.path.join(os.getcwd(), FILE_CONFIG['output_folder'])

def get_data_folder():
    """Get the current data folder path"""
    return os.path.join(os.getcwd(), FILE_CONFIG['data_folder'])

# Update UPLOAD_FOLDER and OUTPUT_FOLDER to use functions
UPLOAD_FOLDER = get_upload_folder()
OUTPUT_FOLDER = get_output_folder()

# Configuration
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload PDF file for processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'filepath': filepath
            })
        else:
            return jsonify({'error': 'Invalid file type. Only PDF files allowed.'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/process', methods=['POST'])
def process_file():
    """Process the uploaded PDF file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Initialize multi-format processor with uploads directory
        processor = MultiFormatProcessor(data_dir=get_upload_folder(), output_dir=get_output_folder())
        
        # Process the file
        result = processor.process_file(filename)
        
        if result['success']:
            transactions = result['transactions']
            bank_name = result['bank_name']
            format_name = result['format_name']
            
            # Calculate totals from transactions
            total_withdrawal = sum(float(t.get('withdrawal', '0').replace(',', '')) for t in transactions if t.get('withdrawal'))
            total_deposit = sum(float(t.get('deposit', '0').replace(',', '')) for t in transactions if t.get('deposit'))
            net_amount = total_deposit - total_withdrawal
            
            # Generate merchant summary
            merchant_summary = {}
            for t in transactions:
                category = t.get('merchant_category', 'Other')
                merchant_summary[category] = merchant_summary.get(category, 0) + 1
            
            # Save to Excel with production-ready naming
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_prefix = datetime.now().strftime("%Y-%m-%d")
            
            # Create professional filename
            base_filename = os.path.splitext(filename)[0]
            bank_short = bank_name.replace(' ', '_').replace('Bank', '').strip('_')
            output_filename = f"{date_prefix}_{base_filename}_{bank_short}_Processed.xlsx"
            output_path = processor.save_to_excel(transactions, output_filename)
            
            return jsonify({
                'message': f'File processed successfully using {bank_name} processor',
                'filename': filename,
                'total_transactions': len(transactions),
                'total_withdrawal': total_withdrawal,
                'total_deposit': total_deposit,
                'net_amount': net_amount,
                'merchant_summary': merchant_summary,
                'output_file': output_path,
                'bank_name': bank_name,
                'format_name': format_name,
                'processor_info': result['processor_info']
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download processed results"""
    try:
        filepath = os.path.join(OUTPUT_FOLDER, 'individual', filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/files')
def list_files():
    """List available PDF files for processing"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.pdf'):
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(os.path.join(UPLOAD_FOLDER, filename)),
                    'uploaded': os.path.getctime(os.path.join(UPLOAD_FOLDER, filename))
                })
        
        return jsonify({'files': files})
        
    except Exception as e:
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete uploaded file"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': 'File deleted successfully'})
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@app.route('/api/merchants', methods=['GET'])
def get_merchants():
    """Get current merchant configuration"""
    try:
        # Use any processor to get merchant config (they all share the same base)
        processor = MultiFormatProcessor()
        # Load merchant config from file
        processor.load_merchant_config()
        return jsonify({'merchants': processor.merchant_config})
    except Exception as e:
        return jsonify({'error': f'Failed to get merchants: {str(e)}'}), 500

@app.route('/api/merchants', methods=['POST'])
def update_merchants():
    """Update merchant configuration"""
    try:
        data = request.get_json()
        merchants = data.get('merchants', {})
        
        # Validate merchant data
        if not isinstance(merchants, dict):
            return jsonify({'error': 'Invalid merchant data format'}), 400
        
        # Update merchant config file
        processor = MultiFormatProcessor()
        success = processor.update_merchant_config(merchants)
        
        if success:
            return jsonify({'message': 'Merchant configuration updated successfully'})
        else:
            return jsonify({'error': 'Failed to update merchant configuration'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500

@app.route('/api/merchants/add', methods=['POST'])
def add_merchant():
    """Add a new merchant category"""
    try:
        data = request.get_json()
        category = data.get('category', '').strip()
        keywords = data.get('keywords', '').strip()
        
        if not category or not keywords:
            return jsonify({'error': 'Category and keywords are required'}), 400
        
        processor = MultiFormatProcessor()
        success = processor.add_merchant_category(category, keywords)
        
        if success:
            return jsonify({'message': f'Merchant category "{category}" added successfully'})
        else:
            return jsonify({'error': 'Failed to add merchant category'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Add failed: {str(e)}'}), 500

@app.route('/api/merchants/delete/<category>', methods=['DELETE'])
def delete_merchant(category):
    """Delete a merchant category"""
    try:
        processor = MultiFormatProcessor()
        success = processor.delete_merchant_category(category)
        
        if success:
            return jsonify({'message': f'Merchant category "{category}" deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete merchant category'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@app.route('/api/batch/process', methods=['POST'])
def process_batch():
    """Process multiple PDF files in batch using multi-format processor"""
    try:
        data = request.get_json()
        selected_files = data.get('selected_files', [])
        batch_size = data.get('batch_size', 50)
        output_filename = data.get('output_filename', 'Batch_Processing_Results.xlsx')
        output_folder = data.get('output_folder', 'output')
        output_options = data.get('output_options', {
            'create_consolidated': True,
            'create_individual_batches': True,
            'create_summary_report': True
        })
        
        if not selected_files:
            return jsonify({'error': 'No files selected for processing'}), 400
        
        # Initialize multi-format processor
        processor = MultiFormatProcessor(data_dir='data', output_dir=output_folder)
        
        # Validate that selected files exist
        data_dir = 'data'
        valid_files = []
        for filename in selected_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath) and filename.lower().endswith('.pdf'):
                valid_files.append(filename)
            else:
                print(f"Warning: File {filename} not found or not a PDF")
        
        if not valid_files:
            return jsonify({'error': 'No valid PDF files found among selected files'}), 400
        
        # Process selected files using multi-format processor
        print(f"🔍 Debug: Processing {len(valid_files)} selected files: {valid_files}")
        print(f"🔍 Debug: Batch size: {batch_size}")
        print(f"🔍 Debug: Output options: {output_options}")
        
        # Process files individually and collect results
        all_transactions = []
        processed_files = []
        bank_summary = {}
        
        for filename in valid_files:
            print(f"🔄 Processing: {filename}")
            result = processor.process_file(filename)
            
            if result['success']:
                transactions = result['transactions']
                bank_name = result['bank_name']
                
                # Add bank information to transactions
                for transaction in transactions:
                    transaction['source_file'] = filename
                    transaction['bank_name'] = bank_name
                    transaction['format_name'] = result['format_name']
                
                all_transactions.extend(transactions)
                processed_files.append({
                    'filename': filename,
                    'bank_name': bank_name,
                    'format_name': result['format_name'],
                    'transaction_count': len(transactions)
                })
                
                # Update bank summary
                if bank_name not in bank_summary:
                    bank_summary[bank_name] = 0
                bank_summary[bank_name] += len(transactions)
                
                print(f"✅ {filename}: {len(transactions)} transactions extracted using {bank_name} processor")
            else:
                print(f"❌ {filename}: {result['error']}")
                processed_files.append({
                    'filename': filename,
                    'error': result['error']
                })
        
        if not all_transactions:
            return jsonify({'error': 'No transactions extracted from any files'}), 400
        
        # Create output files based on options
        output_files = []
        
        if output_options.get('create_consolidated'):
            # Create consolidated master file with standardized column structure
            import pandas as pd
            from datetime import datetime
            
            # Generate production-ready filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_prefix = datetime.now().strftime("%Y-%m-%d")
            
            # Create professional filename
            if output_filename and output_filename.strip():
                base_name = output_filename.strip()
            else:
                base_name = "Bank_Statement_Analysis"
            
            consolidated_filename = f"{date_prefix}_{base_name}_Master_Data.xlsx"
            
            # Standardize field names for consistent output
            standardized_transactions = []
            for transaction in all_transactions:
                standardized_transaction = {
                    'Transaction_Date': transaction.get('transaction_date', ''),
                    'Value_Date': transaction.get('value_date', ''),
                    'Description': transaction.get('description', transaction.get('transaction_details', '')),  # Standardize description field
                    'Withdrawal': transaction.get('withdrawal', ''),
                    'Deposit': transaction.get('deposit', ''),
                    'Balance': transaction.get('balance', ''),
                    'Merchant_Category': transaction.get('merchant_category', 'Other'),
                    'Transaction_Type': transaction.get('transaction_type', 'Unknown'),
                    'Source_File': transaction.get('source_file', ''),
                    'Bank_Name': transaction.get('bank_name', 'Unknown'),
                    'Account_Type': transaction.get('account_type', 'Unknown')
                }
                standardized_transactions.append(standardized_transaction)
            
            df = pd.DataFrame(standardized_transactions)
            consolidated_path = os.path.join(output_folder, consolidated_filename)
            df.to_excel(consolidated_path, index=False, engine='openpyxl')
            output_files.append(consolidated_path)
            print(f"📊 Master Data file created: {consolidated_filename}")
        
        if output_options.get('create_individual_batches'):
            # Create individual batch files with standardized column structure
            for i in range(0, len(all_transactions), batch_size):
                batch_transactions = all_transactions[i:i + batch_size]
                
                # Standardize field names for consistent output
                standardized_batch = []
                for transaction in batch_transactions:
                    standardized_transaction = {
                        'Transaction_Date': transaction.get('transaction_date', ''),
                        'Value_Date': transaction.get('value_date', ''),
                        'Description': transaction.get('description', transaction.get('transaction_details', '')),  # Standardize description field
                        'Withdrawal': transaction.get('withdrawal', ''),
                        'Deposit': transaction.get('deposit', ''),
                        'Balance': transaction.get('balance', ''),
                        'Merchant_Category': transaction.get('merchant_category', 'Other'),
                        'Transaction_Type': transaction.get('transaction_type', 'Unknown'),
                        'Source_File': transaction.get('source_file', ''),
                        'Bank_Name': transaction.get('bank_name', 'Unknown'),
                        'Account_Type': transaction.get('account_type', 'Unknown')
                    }
                    standardized_batch.append(standardized_transaction)
                
                batch_df = pd.DataFrame(standardized_batch)
                
                # Create professional batch filename
                batch_number = i//batch_size + 1
                batch_filename = f"{date_prefix}_{base_name}_Batch_{batch_number:02d}_of_{((len(all_transactions) + batch_size - 1) // batch_size):02d}.xlsx"
                batch_path = os.path.join(output_folder, batch_filename)
                
                batch_df.to_excel(batch_path, index=False, engine='openpyxl')
                output_files.append(batch_path)
                print(f"📦 Batch file created: {batch_filename}")
        
        if output_options.get('create_summary_report'):
            # Create summary report
            summary_data = {
                'Processing_Summary': [
                    {'Metric': 'Total Files Processed', 'Value': len(processed_files)},
                    {'Metric': 'Total Transactions', 'Value': len(all_transactions)},
                    {'Metric': 'Output Files Created', 'Value': len(output_files)},
                    {'Metric': 'Batch Size Used', 'Value': batch_size}
                ],
                'Bank_Summary': [
                    {'Bank': bank, 'Transaction_Count': count} 
                    for bank, count in bank_summary.items()
                ],
                'File_Details': [
                    {'Filename': f['filename'], 'Bank': f.get('bank_name', 'Unknown'), 
                     'Transactions': f.get('transaction_count', 0), 'Status': 'Success' if 'bank_name' in f else 'Failed'}
                    for f in processed_files
                ]
            }
            
            # Generate merchant category summary totals
            merchant_summary = {}
            for transaction in all_transactions:
                category = transaction.get('merchant_category', 'Other')
                transaction_type = transaction.get('transaction_type', 'Unknown')
                bank_name = transaction.get('bank_name', 'Unknown')
                
                if category not in merchant_summary:
                    merchant_summary[category] = {
                        'total_count': 0,
                        'total_withdrawal': 0.0,
                        'total_deposit': 0.0,
                        'by_bank': {},
                        'by_type': {'Deposit': 0, 'Withdrawal': 0}
                    }
                
                # Update totals
                merchant_summary[category]['total_count'] += 1
                
                # Update by transaction type
                if transaction_type in merchant_summary[category]['by_type']:
                    merchant_summary[category]['by_type'][transaction_type] += 1
                
                # Update by bank
                if bank_name not in merchant_summary[category]['by_bank']:
                    merchant_summary[category]['by_bank'][bank_name] = {
                        'count': 0,
                        'withdrawal': 0.0,
                        'deposit': 0.0
                    }
                
                merchant_summary[category]['by_bank'][bank_name]['count'] += 1
                
                # Handle amounts
                withdrawal = transaction.get('withdrawal', '')
                deposit = transaction.get('deposit', '')
                
                if withdrawal and withdrawal != '':
                    try:
                        withdrawal_amount = float(str(withdrawal).replace(',', ''))
                        merchant_summary[category]['total_withdrawal'] += withdrawal_amount
                        merchant_summary[category]['by_bank'][bank_name]['withdrawal'] += withdrawal_amount
                    except (ValueError, TypeError):
                        pass
                
                if deposit and deposit != '':
                    try:
                        deposit_amount = float(str(deposit).replace(',', ''))
                        merchant_summary[category]['total_deposit'] += deposit_amount
                        merchant_summary[category]['by_bank'][bank_name]['deposit'] += deposit_amount
                    except (ValueError, TypeError):
                        pass
            
            # Add merchant summary to summary data
            merchant_summary_list = []
            for category, data in merchant_summary.items():
                merchant_summary_list.append({
                    'Merchant_Category': category,
                    'Total_Count': data['total_count'],
                    'Total_Withdrawal': f"${data['total_withdrawal']:,.2f}",
                    'Total_Deposit': f"${data['total_deposit']:,.2f}",
                    'Net_Amount': f"${data['total_deposit'] - data['total_withdrawal']:,.2f}",
                    'Deposits_Count': data['by_type']['Deposit'],
                    'Withdrawals_Count': data['by_type']['Withdrawal']
                })
            
            summary_data['Merchant_Category_Summary'] = merchant_summary_list
            
            # Add detailed bank breakdown
            bank_breakdown = []
            for category, data in merchant_summary.items():
                for bank_name, bank_data in data['by_bank'].items():
                    bank_breakdown.append({
                        'Merchant_Category': category,
                        'Bank_Name': bank_name,
                        'Transaction_Count': bank_data['count'],
                        'Withdrawal_Amount': f"${bank_data['withdrawal']:,.2f}",
                        'Deposit_Amount': f"${bank_data['deposit']:,.2f}",
                        'Net_Amount': f"${bank_data['deposit'] - bank_data['withdrawal']:,.2f}"
                    })
            
            summary_data['Bank_Breakdown'] = bank_breakdown
            
            # Create professional summary filename
            summary_filename = f"{date_prefix}_{base_name}_Summary_Report.xlsx"
            summary_path = os.path.join(output_folder, summary_filename)
            
            with pd.ExcelWriter(summary_path, engine='openpyxl') as writer:
                for sheet_name, data in summary_data.items():
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            output_files.append(summary_path)
            print(f"📋 Summary Report created: {summary_filename}")
        
        print(f"🔍 Debug: Processing completed. {len(all_transactions)} total transactions from {len(processed_files)} files")
        
        return jsonify({
            'message': 'Multi-format batch processing completed successfully',
            'total_files': len(processed_files),
            'total_transactions': len(all_transactions),
            'batches_processed': (len(all_transactions) + batch_size - 1) // batch_size,
            'output_files': output_files,
            'bank_summary': bank_summary,
            'processed_files': processed_files
        })
        
    except Exception as e:
        print(f"❌ Batch processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500

@app.route('/api/batch/status', methods=['GET'])
def get_batch_status():
    """Get current batch processing status"""
    try:
        # Check if there are any PDF files in data directory
        pdf_files = [f for f in os.listdir('data') if f.lower().endswith('.pdf')]
        
        return jsonify({
            'pdf_files_count': len(pdf_files),
            'pdf_files': pdf_files[:10],  # Show first 10 files
            'data_directory': os.path.abspath('data'),
            'output_directory': os.path.abspath('output')
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get batch status: {str(e)}'}), 500

@app.route('/api/folders', methods=['GET'])
def get_folders():
    """Get available folders for output"""
    try:
        # Get current working directory and common output locations
        current_dir = os.getcwd()
        
        # For Docker containers, use host mount if available
        host_root = '/host'
        if os.path.exists(host_root):
            # We're in Docker with host mount
            folders = {
                'current': current_dir,
                'output': os.path.join(current_dir, 'output'),
                'home': os.path.join(host_root, 'Users', os.environ.get('USER', 'toddabraham')),
                'desktop': os.path.join(host_root, 'Users', os.environ.get('USER', 'toddabraham'), 'Desktop'),
                'documents': os.path.join(host_root, 'Users', os.environ.get('USER', 'toddabraham'), 'Documents'),
                'downloads': os.path.join(host_root, 'Users', os.environ.get('USER', 'toddabraham'), 'Downloads'),
                'root': host_root
            }
        else:
            # We're running locally
            folders = {
                'current': current_dir,
                'output': os.path.join(current_dir, 'output'),
                'home': os.path.expanduser('~'),
                'desktop': os.path.expanduser('~/Desktop'),
                'documents': os.path.expanduser('~/Documents'),
                'downloads': os.path.expanduser('~/Downloads')
            }
        
        # Check which folders exist and are accessible
        available_folders = {}
        for name, path in folders.items():
            if os.path.exists(path):
                # Check if readable (for host mount) or writable (for local)
                is_accessible = os.access(path, os.R_OK)
                if name in ['current', 'output']:
                    is_accessible = is_accessible and os.access(path, os.W_OK)
                
                if is_accessible:
                    available_folders[name] = {
                        'path': path,
                        'name': name.replace('_', ' ').title(),
                        'writable': name in ['current', 'output'],
                        'host_path': path
                    }
        
        return jsonify({'folders': available_folders})
        
    except Exception as e:
        return jsonify({'error': f'Failed to get folders: {str(e)}'}), 500

@app.route('/api/folders/browse', methods=['POST'])
def browse_folder():
    """Browse folder contents"""
    try:
        data = request.get_json()
        path = data.get('path', os.getcwd())
        
        # Handle special paths
        if path == '.':
            path = os.getcwd()
        elif path == 'output':
            path = os.path.join(os.getcwd(), 'output')
        
        if not os.path.exists(path):
            return jsonify({'error': f'Path does not exist: {path}'}), 404
        
        if not os.path.isdir(path):
            return jsonify({'error': 'Path is not a directory'}), 400
        
        # Get directory contents
        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    if os.path.isdir(item_path):
                        # Check if this is a host mount path
                        is_host_path = path.startswith('/host')
                        items.append({
                            'name': item,
                            'type': 'folder',
                            'path': item_path,
                            'writable': os.access(item_path, os.W_OK) if not is_host_path else False,
                            'is_host_path': is_host_path
                        })
                    else:
                        items.append({
                            'name': item,
                            'type': 'file',
                            'path': item_path,
                            'size': os.path.getsize(item_path) if os.path.exists(item_path) else 0
                        })
                except (PermissionError, OSError):
                    # Skip items we can't access
                    continue
            
            # Sort: folders first, then files, both alphabetically
            items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
            
        except PermissionError:
            return jsonify({'error': 'Permission denied accessing directory'}), 403
        
        # Determine parent path
        parent_path = None
        if path != '/' and path != os.getcwd():
            parent_path = os.path.dirname(path)
        
        return jsonify({
            'current_path': path,
            'items': items,
            'parent_path': parent_path
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to browse folder: {str(e)}'}), 500

@app.route('/api/folders/create', methods=['POST'])
def create_folder():
    """Create a new folder"""
    try:
        data = request.get_json()
        parent_path = data.get('parent_path')
        folder_name = data.get('folder_name')
        
        if not parent_path or not folder_name:
            return jsonify({'error': 'Parent path and folder name are required'}), 400
        
        # Validate folder name
        if not folder_name or '/' in folder_name or '\\' in folder_name:
            return jsonify({'error': 'Invalid folder name'}), 400
        
        new_folder_path = os.path.join(parent_path, folder_name)
        
        if os.path.exists(new_folder_path):
            return jsonify({'error': 'Folder already exists'}), 409
        
        # Create the folder
        os.makedirs(new_folder_path, exist_ok=False)
        
        return jsonify({
            'message': 'Folder created successfully',
            'path': new_folder_path
        })
        
    except PermissionError:
        return jsonify({'error': 'Permission denied creating folder'}), 403
    except Exception as e:
        return jsonify({'error': f'Failed to create folder: {str(e)}'}), 500

@app.route('/api/config/locations', methods=['GET'])
def get_file_locations():
    """Get current file location configuration"""
    try:
        return jsonify({
            'upload_folder': FILE_CONFIG['upload_folder'],
            'output_folder': FILE_CONFIG['output_folder'],
            'data_folder': FILE_CONFIG['data_folder'],
            'full_paths': {
                'upload': get_upload_folder(),
                'output': get_output_folder(),
                'data': get_data_folder()
            }
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get locations: {str(e)}'}), 500

@app.route('/api/config/locations', methods=['POST'])
def update_file_locations():
    """Update file location configuration"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['upload_folder', 'output_folder', 'data_folder']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Update configuration
        FILE_CONFIG['upload_folder'] = data['upload_folder']
        FILE_CONFIG['output_folder'] = data['output_folder']
        FILE_CONFIG['data_folder'] = data['data_folder']
        
        # Create directories if they don't exist
        os.makedirs(get_upload_folder(), exist_ok=True)
        os.makedirs(get_output_folder(), exist_ok=True)
        os.makedirs(get_data_folder(), exist_ok=True)
        
        # Update global variables
        global UPLOAD_FOLDER, OUTPUT_FOLDER
        UPLOAD_FOLDER = get_upload_folder()
        OUTPUT_FOLDER = get_output_folder()
        
        return jsonify({
            'message': 'File locations updated successfully',
            'config': FILE_CONFIG,
            'full_paths': {
                'upload': get_upload_folder(),
                'output': get_output_folder(),
                'data': get_data_folder()
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update locations: {str(e)}'}), 500

@app.route('/api/config/locations/test', methods=['POST'])
def test_file_locations():
    """Test if the configured file locations are accessible"""
    try:
        data = request.get_json()
        
        test_results = {}
        for folder_type, folder_path in data.items():
            full_path = os.path.join(os.getcwd(), folder_path)
            test_results[folder_type] = {
                'path': folder_path,
                'full_path': full_path,
                'exists': os.path.exists(full_path),
                'writable': os.access(full_path, os.W_OK) if os.path.exists(full_path) else False,
                'can_create': os.access(os.path.dirname(full_path), os.W_OK) if not os.path.exists(full_path) else False
            }
        
        return jsonify({
            'message': 'Location test completed',
            'results': test_results
        })
        
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

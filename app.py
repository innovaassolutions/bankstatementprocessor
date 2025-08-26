from flask import Flask, request, jsonify, send_file, render_template

# Version information
VERSION = "1.0.0"
BUILD_DATE = "2025-08-26 16:52:34"
from flask_cors import CORS
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename
from ocbc_processor import OCBCBankProcessor
import json

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
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
        
        # Initialize processor
        processor = OCBCBankProcessor()
        
        # Process the file
        result = processor.process_file(filename)
        
        if result:
            # Get summary data
            totals = processor.calculate_totals()
            merchant_summary = processor.generate_merchant_summary()
            
            return jsonify({
                'message': 'Processing completed successfully',
                'filename': filename,
                'total_transactions': totals['total_transactions'],
                'total_withdrawal': totals['total_withdrawal'],
                'total_deposit': totals['total_deposit'],
                'net_amount': totals['net_amount'],
                'merchant_summary': merchant_summary,
                'output_file': f"{filename.replace('.pdf', '_Processed.xlsx')}"
            })
        else:
            return jsonify({'error': 'Processing failed'}), 500
            
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
        processor = OCBCBankProcessor()
        merchants = processor.get_merchant_config()
        return jsonify({'merchants': merchants})
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
        processor = OCBCBankProcessor()
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
        
        processor = OCBCBankProcessor()
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
        processor = OCBCBankProcessor()
        success = processor.delete_merchant_category(category)
        
        if success:
            return jsonify({'message': f'Merchant category "{category}" deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete merchant category'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@app.route('/api/batch/process', methods=['POST'])
def process_batch():
    """Process multiple PDF files in batch"""
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
        
        processor = OCBCBankProcessor()
        
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
        
        # Process selected files in batches
        print(f"🔍 Debug: Processing {len(valid_files)} selected files: {valid_files}")
        print(f"🔍 Debug: Batch size: {batch_size}")
        print(f"🔍 Debug: Output options: {output_options}")
        
        results = processor.process_all_files_batch(
            valid_files, 
            batch_size=batch_size,
            output_filename=output_filename,
            output_folder=output_folder,
            output_options=output_options
        )
        
        print(f"🔍 Debug: Results: {results}")
        
        return jsonify({
            'message': 'Batch processing completed successfully',
            'total_files': len(valid_files),
            'batches_processed': len(results['batches']),
            'output_files': results['output_files']
        })
        
    except Exception as e:
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

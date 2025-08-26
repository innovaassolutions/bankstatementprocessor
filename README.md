# 🏦 Bank Statement Processor v2.0

A professional-grade Python application that processes PDF bank statements with a modern Web UI, Docker support, and advanced batch processing capabilities.

## 🎯 What This Application Does

This application provides multiple ways to process bank statements:

### **Core Features:**
- **📄 PDF Processing**: Extract transactions from any PDF bank statement
- **🏷️ Smart Categorization**: Automatically categorize transactions by merchant
- **📊 Batch Processing**: Process hundreds of files in organized batches
- **🌐 Web Interface**: Modern, responsive web UI for easy interaction
- **🐳 Docker Support**: Cross-platform containerized deployment
- **📁 Flexible Output**: Customizable output locations and file naming

### **Transaction Types Supported:**
- **OCBC Bank Statements**: Specialized processor for OCBC format
- **Generic PDFs**: General-purpose PDF text extraction
- **Custom Patterns**: Configurable regex patterns for different banks

## 🚀 Quick Start

### **Option 1: Docker (Recommended)**
```bash
# Clone the repository
git clone https://github.com/innovaassolutions/bankstatementprocessor.git
cd bankstatementprocessor

# Start the application
./start.sh          # Mac/Linux
start.bat           # Windows

# Open your browser to: http://localhost:3005
```

### **Option 2: Python Development**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 🌐 Web Interface Features

### **📤 File Management**
- **Drag & Drop Upload**: Easy PDF file uploads
- **Batch Selection**: Choose specific files for processing
- **File Organization**: Clean, paginated file listing
- **Multi-Selection**: Process multiple files at once

### **⚙️ Processing Options**
- **Individual Processing**: Process single files with detailed results
- **Batch Processing**: Process hundreds of files in organized batches
- **Custom Output**: Choose output folder and filename
- **Output Options**: Select which files to generate

### **🏷️ Merchant Management**
- **Configurable Categories**: Edit merchant search terms through the UI
- **Smart Categorization**: Automatic transaction categorization
- **Priority System**: More specific categories take precedence

### **📁 Folder Browser**
- **Full System Access**: Browse any folder on your system
- **Create New Folders**: Build custom output directory structures
- **Quick Access**: Home, Desktop, Documents, Downloads shortcuts

## 🐳 Docker Deployment

### **Docker Compose**
```yaml
version: '3.8'
services:
  bank-processor:
    image: yourusername/bank-processor:latest
    ports:
      - "3005:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./output:/app/output
      - ./data:/app/data
      - ./merchant_config.txt:/app/merchant_config.txt
    restart: unless-stopped
```

### **Manual Docker Commands**
```bash
# Build image
docker build -t bank-processor .

# Run container
docker run -d -p 3005:5000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/data:/app/data \
  --name bank-processor bank-processor

# Access application
open http://localhost:3005
```

## 📊 Batch Processing

### **Large-Scale Processing**
```bash
# Process 500 files in batches of 50
# Creates organized output structure:

output/
├── batches/                    # Individual batch results
│   ├── Batch_001_of_010.xlsx  # Files 1-50
│   ├── Batch_002_of_010.xlsx  # Files 51-100
│   └── ...
├── consolidated/               # All data combined
│   └── MasterData_Consolidated.xlsx
└── reports/                    # Processing summaries
    └── Batch_Processing_Summary.xlsx
```

### **Output Options**
- **✅ Individual Batch Files**: Separate Excel files for each batch
- **✅ Consolidated Master File**: All transactions in one comprehensive file
- **✅ Summary Reports**: Processing statistics and batch information

### **Master Data File Structure**
The consolidated file contains multiple sheets:
- **Master_Data**: All transactions from all batches
- **Batch_Summary**: Overview of each batch processed
- **Merchant_Summary**: Categorized transaction totals
- **Overall_Statistics**: Key metrics and totals
- **File_Details**: Which files were in which batch

## 🏷️ Merchant Categorization

### **Default Categories**
The system comes pre-configured with common merchant categories:
- **Adyen**: Payment processing
- **MYR**: Malaysian Ringgit transactions
- **Lalamove**: Delivery services
- **Amazon**: Online shopping
- **Deliveroo**: Food delivery
- **Gpay**: Google Pay transactions
- **Hero**: Delivery Hero services
- **Grab**: Ride-hailing and delivery
- **Foodpanda**: Food delivery
- **Freshmart**: Grocery delivery
- **Lily**: Various services

### **Customization**
- **Edit Through UI**: Modify categories directly in the web interface
- **Add New Categories**: Create custom merchant classifications
- **Priority System**: More specific categories take precedence
- **Real-time Updates**: Changes apply immediately

## 📁 Directory Structure

```
BankStatementExtraction/
├── app.py                     # Flask web application
├── ocbc_processor.py          # Core PDF processing engine
├── templates/                 # Web UI templates
│   └── index.html            # Main interface
├── data/                      # PDF input directory
├── uploads/                   # File upload directory
├── output/                    # Results directory
│   ├── batches/              # Individual batch outputs
│   ├── consolidated/         # Master data files
│   ├── individual/           # Single file results
│   └── reports/              # Summary reports
├── merchant_config.txt        # Merchant configuration
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker container definition
├── docker-compose.yml         # Docker orchestration
├── start.sh                   # Mac/Linux startup script
├── start.bat                  # Windows startup script
└── README.md                  # This documentation
```

## 🔧 Configuration

### **Merchant Configuration**
Edit `merchant_config.txt` to customize transaction categorization:
```txt
adyen:ADYEN,adyen,payment
amazon:AMAZON,amazon,amzn
deliveroo:DELIVEROO,deliveroo,food delivery
```

### **Environment Variables**
```bash
FLASK_APP=app.py
FLASK_ENV=production
```

## 📈 Performance & Scalability

### **Large File Handling**
- **Memory Efficient**: Processes files page by page
- **Progress Tracking**: Shows processing status for large files
- **Batch Optimization**: Configurable batch sizes for optimal performance

### **Recommended Batch Sizes**
- **Small Files (< 10 pages)**: 100-200 files per batch
- **Medium Files (10-50 pages)**: 50-100 files per batch
- **Large Files (50+ pages)**: 25-50 files per batch

## 🆘 Troubleshooting

### **Common Issues**

1. **Port Already in Use**
   ```bash
   # Check what's using port 3005
   lsof -i :3005
   
   # Change port in docker-compose.yml
   ports:
     - "3006:5000"  # Use different host port
   ```

2. **Permission Errors**
   ```bash
   # Ensure directories are writable
   chmod 755 output/ data/ uploads/
   ```

3. **Docker Build Fails**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild from scratch
   docker-compose build --no-cache
   ```

### **Logs and Debugging**
```bash
# View application logs
docker logs bank-processor

# Check container status
docker ps -a

# Access container shell
docker exec -it bank-processor /bin/bash
```

## 🔄 Updates and Maintenance

### **Getting Updates**
```bash
# Pull latest version
docker pull yourusername/bank-processor:latest

# Update with Docker Compose
docker-compose pull && docker-compose up -d
```

### **Version Management**
- **Latest**: Most recent stable version
- **Specific Versions**: Tagged releases (e.g., `:1.1.0`)
- **Development**: Latest development builds

## 🎯 Use Cases

### **Personal Finance**
- Process monthly bank statements
- Categorize spending patterns
- Track income and expenses

### **Business Accounting**
- Process vendor invoices
- Categorize business expenses
- Generate financial reports

### **Audit and Compliance**
- Process large volumes of statements
- Generate audit trails
- Maintain data integrity

## 🔮 Future Enhancements

- **API Integration**: REST API for external applications
- **Cloud Storage**: Support for cloud-based file storage
- **Advanced Analytics**: Machine learning for transaction categorization
- **Multi-Language**: Support for international bank formats
- **Mobile App**: Native mobile applications

## 📞 Support and Community

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and examples
- **Community**: Share configurations and best practices

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy Processing! 🚀**

*Built with ❤️ for the financial processing community*

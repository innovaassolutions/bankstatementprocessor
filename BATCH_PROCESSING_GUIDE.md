# 🚀 Batch Processing Guide
## Multi-Format Bank Statement Processor

---

## 📖 Table of Contents
1. [What is Batch Processing?](#what-is-batch-processing)
2. [How It Works](#how-it-works)
3. [Setting Up Batch Processing](#setting-up-batch-processing)
4. [Understanding Batch Size](#understanding-batch-size)
5. [Output Options](#output-options)
6. [Step-by-Step Instructions](#step-by-step-instructions)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## 🎯 What is Batch Processing?

Batch processing allows you to process multiple PDF bank statements simultaneously, automatically detecting their format (OCBC, DBS, etc.) and extracting transactions in organized, manageable chunks.

### **Key Benefits:**
- ✅ **Efficient Processing** - Handle hundreds of files at once
- ✅ **Automatic Format Detection** - No need to specify bank type
- ✅ **Organized Output** - Separate files for each batch
- ✅ **Progress Tracking** - Monitor processing status
- ✅ **Memory Management** - Prevent system overload

---

## ⚙️ How It Works

### **The Process Flow:**
1. **File Selection** → Choose which PDFs to process
2. **Format Detection** → System automatically identifies bank type
3. **Batch Grouping** → Files organized into batches based on size
4. **Processing** → Each batch processed with appropriate processor
5. **Output Generation** → Excel files created for each batch
6. **Summary Report** → Complete overview of all processing

### **Automatic Bank Detection:**
- **OCBC Bank** → Detected by "OCBC Bank", "STATEMENT OF ACCOUNT"
- **DBS Bank** → Detected by "DBS Bank Ltd", "Account Statement"
- **Future Banks** → Easily added with new processor classes

---

## 🛠️ Setting Up Batch Processing

### **Prerequisites:**
- PDF files placed in the `data/` directory
- Web interface accessible (Docker container running)
- Files selected for processing

### **Required Settings:**
- **Batch Size** - Number of files per batch
- **Output Filename** - Base name for output files
- **Output Folder** - Where to save results
- **Output Options** - Which files to generate

---

## 📊 Understanding Batch Size

### **What Batch Size Means:**
- **Batch Size ≠ Total Files** (Common misconception!)
- **Batch Size = Files processed per batch**
- **Total Batches = Total Files ÷ Batch Size**

### **Examples:**

#### **Small Dataset (2 PDFs):**
```
📁 Input: 2 PDF files
⚙️ Batch Size: 2
📊 Result: 1 batch (2 ÷ 2 = 1)
```

#### **Medium Dataset (50 PDFs):**
```
📁 Input: 50 PDF files
⚙️ Batch Size: 10
📊 Result: 5 batches (50 ÷ 10 = 5)
```

#### **Large Dataset (500 PDFs):**
```
📁 Input: 500 PDF files
⚙️ Batch Size: 50
📊 Result: 10 batches (500 ÷ 50 = 10)
```

### **Recommended Batch Sizes:**

| File Count | Recommended Batch Size | Reasoning |
|------------|----------------------|-----------|
| **1-10 files** | **2-5** | Quick processing, minimal memory |
| **10-100 files** | **10-25** | Balanced speed and memory usage |
| **100-1000 files** | **25-50** | Efficient for large datasets |
| **1000+ files** | **50-100** | Maximum efficiency, monitor memory |

---

## 📁 Output Options

### **Available Output Types:**

#### **1. Create Consolidated Master File** ✅
- **What it does:** Combines ALL transactions from ALL files into one Excel file
- **Use case:** When you need everything in a single view
- **File naming:** `{filename}_Consolidated.xlsx`

#### **2. Create Individual Batch Files** ✅
- **What it does:** Creates separate Excel files for each batch
- **Use case:** When you want to process batches separately
- **File naming:** `{filename}_Batch_1.xlsx`, `{filename}_Batch_2.xlsx`, etc.

#### **3. Create Summary Report** ✅
- **What it does:** Generates comprehensive processing summary
- **Use case:** When you need overview and statistics
- **File naming:** `{filename}_Summary.xlsx`

### **Summary Report Contents:**
- **Processing Summary** - Total files, transactions, batches
- **Bank Summary** - Breakdown by bank type
- **File Details** - Status of each processed file

---

## 📋 Step-by-Step Instructions

### **Step 1: Access Batch Processing**
1. Open the web interface
2. Navigate to **"Processing"** page
3. Scroll to **"Batch Processing"** section

### **Step 2: Select Files**
1. Go to **"File Operations"** page
2. Use checkboxes to select PDF files
3. Note the **"Files Selected"** count

### **Step 3: Configure Batch Settings**
1. **Batch Size:** Set based on your file count (see recommendations above)
2. **Output Filename:** Choose a descriptive name (e.g., "September2025_Statements")
3. **Output Folder:** Select where to save results
4. **Output Options:** Check desired output types

### **Step 4: Start Processing**
1. Click **"Start Batch Processing"** button
2. Confirm the processing details
3. Monitor progress in the status section

### **Step 5: Review Results**
1. Check the output folder for generated files
2. Review the summary report for processing statistics
3. Verify transaction counts and bank detection accuracy

---

## 🧪 Examples

### **Example 1: Small Dataset (2 PDFs)**

#### **Setup:**
- **Files:** `ocbc_statement.pdf`, `dbs_statement.pdf`
- **Batch Size:** 2
- **Output Filename:** "Test_Processing"

#### **Processing:**
```
🔄 Processing 2 files...
├── ocbc_statement.pdf → OCBC Bank processor ✅
└── dbs_statement.pdf → DBS Bank processor ✅
```

#### **Output:**
```
📁 output/
├── Test_Processing_Batch_1.xlsx (both files)
├── Test_Processing_Consolidated.xlsx (all transactions)
└── Test_Processing_Summary.xlsx (processing summary)
```

### **Example 2: Large Dataset (100 PDFs)**

#### **Setup:**
- **Files:** 100 PDF statements
- **Batch Size:** 25
- **Output Filename:** "Q3_2025_Statements"

#### **Processing:**
```
🔄 Processing 100 files in batches of 25...
├── Batch 1: Files 1-25 (OCBC: 15, DBS: 10)
├── Batch 2: Files 26-50 (OCBC: 12, DBS: 13)
├── Batch 3: Files 51-75 (OCBC: 18, DBS: 7)
└── Batch 4: Files 76-100 (OCBC: 20, DBS: 5)
```

#### **Output:**
```
📁 output/
├── Q3_2025_Statements_Batch_1.xlsx (25 files)
├── Q3_2025_Statements_Batch_2.xlsx (25 files)
├── Q3_2025_Statements_Batch_3.xlsx (25 files)
├── Q3_2025_Statements_Batch_4.xlsx (25 files)
├── Q3_2025_Statements_Consolidated.xlsx (all 100 files)
└── Q3_2025_Statements_Summary.xlsx (complete summary)
```

---

## 🔧 Troubleshooting

### **Common Issues and Solutions:**

#### **Issue: "No files selected for processing"**
- **Cause:** No PDF files checked in file selection
- **Solution:** Go to File Operations page and select files

#### **Issue: "Batch size must be greater than 0"**
- **Cause:** Invalid batch size setting
- **Solution:** Set batch size to 1 or higher

#### **Issue: "No valid PDF files found"**
- **Cause:** Selected files aren't PDFs or don't exist
- **Solution:** Verify file types and locations

#### **Issue: Processing fails with error**
- **Cause:** Unsupported bank format or corrupted PDF
- **Solution:** Check PDF format and try with smaller batch size

#### **Issue: Memory errors with large batches**
- **Cause:** Batch size too large for system
- **Solution:** Reduce batch size and retry

### **Debug Information:**
- Check container logs: `docker logs bankstatementextraction-bank-processor-1`
- Verify file permissions and locations
- Test with single file first, then expand to batches

---

## 💡 Best Practices

### **Performance Optimization:**
1. **Start Small** - Begin with batch size 10-25 for testing
2. **Monitor Memory** - Watch system resources during processing
3. **Use Appropriate Batch Sizes** - Follow the recommendations table above
4. **Test with Sample Files** - Verify format detection before large batches

### **File Organization:**
1. **Consistent Naming** - Use descriptive filenames for easy identification
2. **Organized Input** - Keep PDFs in dedicated folders by date/period
3. **Backup Originals** - Always keep original PDFs as backup

### **Output Management:**
1. **Descriptive Names** - Use meaningful output filenames
2. **Organized Folders** - Structure output directories logically
3. **Version Control** - Include dates in output filenames
4. **Archive Old Results** - Move completed batches to archive folders

### **Quality Assurance:**
1. **Verify Transaction Counts** - Check that totals match expectations
2. **Review Bank Detection** - Ensure correct processor was used
3. **Sample Validation** - Spot-check transactions from each batch
4. **Summary Review** - Always review the summary report

---

## 🎯 Quick Reference

### **Batch Size Calculator:**
```
Batch Size = Desired files per batch
Total Batches = Total Files ÷ Batch Size
```

### **Output File Naming:**
```
{OutputFilename}_Batch_{BatchNumber}.xlsx
{OutputFilename}_Consolidated.xlsx
{OutputFilename}_Summary.xlsx
```

### **Recommended Settings by File Count:**
- **1-10 files:** Batch size 2-5
- **10-100 files:** Batch size 10-25  
- **100+ files:** Batch size 25-50

### **Key Commands:**
- **Start Processing:** Click "Start Batch Processing"
- **Check Status:** Monitor progress in status section
- **View Results:** Check output folder for generated files

---

## 📞 Support

### **Getting Help:**
1. **Check Logs** - Review container logs for error details
2. **Test Single Files** - Verify individual file processing works
3. **Reduce Batch Size** - Try smaller batches if issues occur
4. **Verify File Formats** - Ensure PDFs are valid bank statements

### **System Requirements:**
- Docker container running
- Sufficient disk space for output files
- Adequate memory for batch processing
- Valid PDF files in data directory

---

*This guide covers the complete batch processing workflow for the Multi-Format Bank Statement Processor. For additional support or feature requests, refer to the main documentation or contact the development team.*

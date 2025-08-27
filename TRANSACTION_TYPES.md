# Transaction Types Documentation
# OCBC Bank vs DBS Bank Statement Analysis

## 🏦 **OCBC Bank Transaction Types**

### **Deposits (Money Coming IN):**
- **PAYMENT /TRANSFER OTHR** - Incoming transfers from other accounts
- **GIRO PAYMENT** - Automated incoming payments
- **FAST TRANSFER OTHR** - Fast incoming transfers
- **TRANSFER** - General incoming transfers
- **CASH REBATE** - Credit card rebates
- **ALLW** - Allowance payments
- **BEXP** - Business expense reimbursements

### **Withdrawals (Money Going OUT):**
- **DEBIT PURCHASE** - Card purchases
- **GIRO PAYMENT** - Automated outgoing payments
- **FAST TRANSFER OTHR** - Fast outgoing transfers
- **CHARGES** - Bank fees and charges
- **CCY CONVERSION FEE** - Currency conversion fees
- **TRANSFER** - Outgoing transfers

### **Mixed/Complex:**
- **PAYMENT /TRANSFER SUPP** - Supplier payments (can be both)

---

## 🏦 **DBS Bank Transaction Types**

### **Deposits (Money Coming IN):**
- **REMITTANCE TRANSFER OF FUNDS RTF** - Incoming remittances
- **IBG GIRO** - Interbank incoming payments
- **FAST PAYMENT** (incoming) - Incoming fast transfers
- **TRANSFER** - General incoming transfers
- **CASH TRANSACTION** - Cash deposits

### **Withdrawals (Money Going OUT):**
- **FAST PAYMENT** (outgoing) - Outgoing fast transfers
- **GIRO PAYMENT** - Automated outgoing payments
- **SERVICE CHARGE** - Bank fees
- **INTERBANK GIRO IBG** - Outgoing interbank payments

### **Mixed/Complex:**
- **FAST PAYMENT** - Can be either incoming or outgoing depending on context
- **REMITTANCE TRANSFER OF FUNDS RTF** - Can be either incoming or outgoing depending on context

---

## 🔍 **Transaction Type Detection Rules**

### **OCBC Bank Rules:**
1. **Deposits**: Look for keywords like "PAYMENT /TRANSFER OTHR", "GIRO PAYMENT", "FAST TRANSFER OTHR"
2. **Withdrawals**: Look for keywords like "DEBIT PURCHASE", "CHARGES", "CCY CONVERSION FEE"
3. **Mixed**: Look for keywords like "PAYMENT /TRANSFER SUPP"

### **DBS Bank Rules:**
1. **Deposits**: Look for keywords like "REMITTANCE TRANSFER OF FUNDS RTF", "IBG GIRO"
2. **Withdrawals**: Look for keywords like "FAST PAYMENT", "GIRO PAYMENT", "SERVICE CHARGE"
3. **Mixed**: Look for keywords like "FAST PAYMENT" and analyze context

---

## 📊 **Amount Field Assignment**

### **OCBC Bank:**
- **Deposits**: Amount goes to `deposit` field, `withdrawal` = empty
- **Withdrawals**: Amount goes to `withdrawal` field, `deposit` = empty

### **DBS Bank:**
- **Deposits**: Amount goes to `deposit` field, `withdrawal` = empty
- **Withdrawals**: Amount goes to `withdrawal` field, `deposit` = empty

---

## 🎯 **Implementation Notes**

### **Current Issues:**
1. **DBS processor** treats ALL transactions as withdrawals ❌
2. **OCBC processor** has better logic but could be improved
3. **Transaction type detection** needs to be more sophisticated

### **Required Fixes:**
1. **DBS processor**: Implement proper deposit/withdrawal detection
2. **Both processors**: Use consistent transaction type keywords
3. **Amount assignment**: Ensure proper field mapping based on transaction type

---

## 📝 **Example Transactions**

### **OCBC Examples:**
```
01 JUN - 650.47 02 JUN PAYMENT /TRANSFER OTHR  S$ MUHAMMAD... (DEPOSIT)
01 JUN - 863.85 02 JUN PAYMENT /TRANSFER SUPP ADYEN... (MIXED)
01 JUN - 767.69 02 JUN DEBIT PURCHASE... (WITHDRAWAL)
```

### **DBS Examples:**
```
01-Sep-22 580.00 REMITTANCE TRANSFER OF FUNDS RTF (DEPOSIT)
273.92 01-Sep-22 FAST PAYMENT PH13765... (WITHDRAWAL)
0.50 01-Sep-22 SERVICE CHARGE... (WITHDRAWAL)
```

---

## 🔧 **Next Steps**

1. **Update DBS processor** to use this transaction type logic
2. **Standardize OCBC processor** to match these rules
3. **Test with real statements** to ensure accuracy
4. **Update merchant categorization** to work with proper transaction types

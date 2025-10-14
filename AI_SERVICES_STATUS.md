but# AI Services Usage Summary

## Current Status Report

### ❌ AI Embedding Model
- **Status**: DOWN (due to training)
- **Endpoint**: `https://ai-poc.corp.ia/embedding/v1`
- **Usage in System**: **NONE** ✅
- **Impact**: **NO IMPACT** - This service is defined but never called

### ❌ Docling Service
- **Status**: **DOWN - CONFIRMED BY LOGS** (404 + 502 errors)
- **Endpoint**: `https://ai-poc.corp.ia/docling`
- **Usage in System**: **YES** - Used for PDF text extraction
- **Impact**: **HIGH** - Critical for AI analysis with attachments
- **Error Pattern**:
  - First PDF: `404 Not Found` on all endpoints
  - Subsequent PDFs: `502 Bad Gateway` (service crashes after first attempt)

### ✅ LLM API
- **Status**: WORKING
- **Endpoint**: `https://ai-poc.corp.ia/vllm/v1`
- **Model**: Qwen3-235B-A22B-GPTQ-Int4
- **Usage**: Email analysis, comprehensive analysis
- **Impact**: **CRITICAL** - Main AI service

---

## Email Attachment Processing

### **Your email attachments use DOCLING, NOT embedding!** ✅

### How it works:

1. **User clicks "AI Analysis" button**
   ```
   Button Click → Frontend
   ```

2. **Frontend calls backend API**
   ```javascript
   fetch('/ai/comprehensive-analyze/' + emailId, {
     method: 'POST'
   })
   ```

3. **Backend retrieves email + attachments**
   ```python
   email = Email.query.get_or_404(email_id)
   attachments = Attachment.query.filter_by(email_id=email_id).all()
   ```

4. **Backend calls Docling for each PDF**
   ```python
   # From intelligence_ai.py lines 53-60
   doc_result = self.process_attachment_with_docling(
       file_data=attachment.file_data,
       file_path=attachment.filepath,
       filename=attachment.filename
   )
   ```

5. **Docling extracts text from PDF**
   ```python
   # From intelligence_ai.py lines 780-856
   def process_attachment_with_docling(self, file_data, file_path, filename):
       # Tries multiple endpoints:
       # - https://ai-poc.corp.ia/docling/convert
       # - https://ai-poc.corp.ia/docling/api/convert
       # - https://ai-poc.corp.ia/docling/v1/convert
       # - https://ai-poc.corp.ia/docling/api/v1/convert
       
       response = self.session.post(endpoint, files={'file': (filename, file_data)})
       return {
           'text_content': result.get('text', ''),
           'success': True
       }
   ```

6. **Extracted text sent to LLM for analysis**
   ```python
   # Email body + PDF text combined
   analysis = intelligence_ai.analyze_allegation_email_comprehensive(
       email_data=email_data,
       attachments=attachments  # Contains extracted text from Docling
   )
   ```

7. **LLM returns structured analysis**
   ```json
   {
     "alleged_persons": [...],
     "allegation_type": "Cold calling",
     "allegation_summary": "...",
     "detailed_reasoning": "..."
   }
   ```

---

## Current Bypass Status

### ✅ PDF Processing is Currently DISABLED (CORRECT DECISION!)

**File**: `intelligence_ai.py` lines 34-42

```python
skip_pdf_processing = True  # ✅ KEEP THIS ENABLED!

if skip_pdf_processing:
    print("⚠️ PDF processing temporarily disabled")
    attachment_content = "PDF attachments available but not processed..."
else:
    # Call Docling to extract PDF text
    doc_result = self.process_attachment_with_docling(...)
```

**Reason**: Docling is **STILL DOWN** - returning 404/502 errors

**Current Situation**: 
- AI team said: "Docling should be fine" ❌ **WRONG**
- Your logs show: **404 + 502 errors still occurring** ✅ **CONFIRMED**
- Your bypass is working correctly ✅ **KEEP IT ENABLED**

**Latest Error Evidence** (from your logs):
```
Docling endpoint https://ai-poc.corp.ia/docling/convert returned status 404
Docling endpoint https://ai-poc.corp.ia/docling/api/convert returned status 404
Docling endpoint https://ai-poc.corp.ia/docling/v1/convert returned status 404
Docling endpoint https://ai-poc.corp.ia/docling/api/v1/convert returned status 404
[AI COMPREHENSIVE] ❌ Failed to extract from 投訴信.pdf: Unknown error

# After first PDF, service crashes and returns 502:
Docling endpoint https://ai-poc.corp.ia/docling/convert returned status 502
Docling endpoint https://ai-poc.corp.ia/docling/api/convert returned status 502
Docling endpoint https://ai-poc.corp.ia/docling/v1/convert returned status 502
```

---

## Action Required

### ❌ **DO NOT Re-enable PDF Processing Yet**

Docling is **STILL DOWN** despite what AI team said. Keep the bypass enabled!

#### Step 1: Contact AI Team Again (URGENT)

**Send them this evidence:**

```
Subject: Docling Service STILL DOWN - 404/502 Errors Confirmed

Hi AI Team,

We were told "Docling should be fine", but our logs show it's STILL DOWN:

Error Pattern:
- First PDF: 404 Not Found on ALL endpoints:
  * https://ai-poc.corp.ia/docling/convert
  * https://ai-poc.corp.ia/docling/api/convert
  * https://ai-poc.corp.ia/docling/v1/convert
  * https://ai-poc.corp.ia/docling/api/v1/convert

- Subsequent PDFs: 502 Bad Gateway (service crashes)

Test Files:
- 投訴信.pdf (112KB) → 404
- 關於富衛保險公司的來港人才對相關區域人員潘志豪的控訴.pdf (1MB) → 502
- Editable_Complaint_Form_TC_202501(1).pdf (747KB) → 502
- Editable_Complaint_Form_TC_202502(2).pdf (669KB) → 502

Questions:
1. Is Docling service actually running?
2. What is the correct endpoint URL?
3. Are there file size limits causing 502 errors?
4. When will service be restored?

Our system is currently bypassing PDF processing to maintain functionality.
```

#### Step 2: Keep Current Bypass Enabled

**DO NOT CHANGE THIS:**
```python
# intelligence_ai.py line 36
skip_pdf_processing = True  # ✅ KEEP THIS - Docling is down!
```

#### Step 3: Monitor Your System

Your AI analysis is **still working** - just without PDF content:
- ✅ Email body analysis works
- ✅ Alleged person detection works (from email text)
- ✅ Allegation summaries work
- ❌ PDF content not analyzed (but system doesn't crash)

```bash
docker-compose logs -f intelligence-app | grep -E "(Docling|PDF|COMPREHENSIVE)"
```

**Expected output when working:**
```
[AI COMPREHENSIVE] Processing 2 attachments
[AI COMPREHENSIVE] Attachment: complaint.pdf, has_data: True
[AI COMPREHENSIVE] Calling Docling for: complaint.pdf
[AI COMPREHENSIVE] ✅ Successfully extracted 2543 chars from complaint.pdf
```

**Bad output (if still broken):**
```
Docling endpoint https://ai-poc.corp.ia/docling/convert returned status 502
Docling endpoint https://ai-poc.corp.ia/docling/api/convert returned status 404
Docling API: All endpoints failed, using fallback text extraction
```

---

## Service Comparison

| Service | Endpoint | Used For | Status | Impact if Down |
|---------|----------|----------|--------|----------------|
| **Docling** | `https://ai-poc.corp.ia/docling` | PDF text extraction from email attachments | ❌ **DOWN (404/502)** | High - No PDF analysis (but system still works) |
| **LLM (vLLM)** | `https://ai-poc.corp.ia/vllm/v1` | Email analysis, allegation detection | ✅ Working | Critical - No AI analysis |
| **Embedding** | `https://ai-poc.corp.ia/embedding/v1` | Vector embeddings for semantic search | ❌ Down (training) | **NONE - Not used!** |

---

## Why Embedding is Not Used

The embedding API is **defined but never called** in your code:

```python
# intelligence_ai.py line 17
self.embedding_api = "https://ai-poc.corp.ia/embedding/v1"  # Defined

# But there's NO code like:
# self.session.post(self.embedding_api, ...)  # Never called!
```

**Embedding would be used for:**
- Semantic search (finding similar emails)
- Vector database queries
- Similarity matching

**Your system uses:**
- Direct text extraction (Docling)
- Direct LLM analysis (no embeddings needed)

---

## Recommendation

### ❌ **KEEP PDF bypass enabled - Docling is STILL DOWN!**

1. **DO NOT change flag**: Keep `skip_pdf_processing = True`
2. **Contact AI team**: Send them the error evidence above
3. **Wait for confirmation**: Don't re-enable until they fix the service
4. **Your system is working**: AI analysis continues with email body only

### What's Working Right Now:
- ✅ Email body analysis (LLM working)
- ✅ Alleged person detection from email text
- ✅ Allegation type classification
- ✅ Allegation summaries
- ✅ AI comprehensive analysis (without PDF content)
- ✅ Fast response times (no 30+ second delays)

### What's NOT Working:
- ❌ PDF text extraction (Docling down)
- ❌ PDF content in AI analysis
- ❌ Evidence from PDF complaint forms

### When to Re-enable PDF Processing:
**Only after AI team confirms:**
1. Docling service is running
2. Correct endpoint is available
3. You test manually and see: `✅ Successfully extracted X chars from filename.pdf`
4. NO 404 or 502 errors in logs

---

## Code Location Reference

### PDF Processing Code:
- **Main logic**: `intelligence_ai.py` lines 28-68
- **Docling function**: `intelligence_ai.py` lines 780-856
- **Called from**: 
  - `analyze_allegation_email_comprehensive()` line 53
  - `ai_summarize_email()` line 362

### Embedding Code:
- **Definition**: `intelligence_ai.py` line 17
- **Usage**: **NONE** (not called anywhere)

### LLM Code:
- **Chat completion**: `intelligence_ai.py` lines 90-180
- **Model**: Qwen3-235B-A22B-GPTQ-Int4

---

## Summary

### ❓ Your Question:
> "Is our attachment of email using Docling or Embedding?"

### ✅ Answer:
**Your email attachments use DOCLING exclusively.**

- Embedding API is defined but **never used**
- Docling is used for **all PDF text extraction**
- Embedding being down has **ZERO impact** on your system
- Docling is **STILL DOWN** (404/502 errors confirmed)

### 🔴 Current Reality:
**AI Team was WRONG** - Docling is **NOT working**!

**Your logs prove it:**
```
❌ 404 Not Found - First PDF (service not running or wrong endpoint)
❌ 502 Bad Gateway - Subsequent PDFs (service crashes after first attempt)
```

### ✅ Your Bypass is Working Perfectly:
- System continues to function
- AI analysis works with email body only
- No 30+ second delays
- No crashes or errors

### 🎯 Next Step:
**Contact AI team** with the error evidence and **keep bypass enabled** until they actually fix Docling!

**DO NOT re-enable PDF processing** until you see this in logs:
```
✅ Successfully extracted 2543 chars from filename.pdf
```

"""
AI Integration Module for Intelligence Platform
Uses company's internal AI services for automated email analysis
"""
import requests
import json
import re
from typing import Dict, List, Optional
import urllib3

# Disable SSL warnings for internal corporate services
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IntelligenceAI:
    # Model configuration
    LLM_MODEL = "hosted_vllm/Qwen3-235B-A22B-GPTQ-Int4"
    
    def __init__(self):
        self.llm_api = "https://ai-poc.corp.ia/vllm/v1"
        self.embedding_api = "https://ai-poc.corp.ia/embedding/v1"
        self.docling_api = "https://ai-poc.corp.ia/docling/v1alpha/convert/source"
        
        # Configure session for internal corporate network
        self.session = requests.Session()
        self.session.verify = False  # Skip SSL verification for internal services
        self.session.timeout = 120  # 2 minutes for other APIs
        
        # ✅ CRITICAL FIX: Extended timeouts for large PDF processing
        self.docling_timeout_base = 600  # 10 minutes base timeout for Docling
        self.large_file_threshold_mb = 10  # Files >10MB use async processing
        self.max_sync_file_size_mb = 50  # Maximum size for synchronous processing
        
        # ✅ CRITICAL FIX: Configurable attachment text limits (was hardcoded to 2,000 chars!)
        import os
        self.attachment_text_limit = int(os.environ.get('ATTACHMENT_TEXT_LIMIT', '15000'))  # 15K per attachment
        self.total_attachment_limit = int(os.environ.get('TOTAL_ATTACHMENT_LIMIT', '50000'))  # 50K total
        self.prompt_attachment_limit = int(os.environ.get('PROMPT_ATTACHMENT_LIMIT', '15000'))  # 15K in prompt
        
    def _calculate_dynamic_timeout(self, file_size_mb: float) -> int:
        """Calculate appropriate timeout based on file size (1 minute per MB, minimum 2 minutes)"""
        return max(120, int(file_size_mb * 60))
    
    def _optimize_pdf_for_processing(self, pdf_content: bytes, filename: str) -> bytes:
        """Optimize PDF to reduce processing time and payload size"""
        try:
            import io
            
            # If file is already small, return as-is
            file_size_mb = len(pdf_content) / (1024 * 1024)
            if file_size_mb <= 5:
                return pdf_content
            
            print(f"[PDF OPTIMIZE] Attempting to optimize {filename} ({file_size_mb:.1f} MB)")
            
            # Try to optimize using PyPDF2 if available
            try:
                from PyPDF2 import PdfReader, PdfWriter
                
                reader = PdfReader(io.BytesIO(pdf_content))
                page_count = len(reader.pages)
                
                # If PDF has too many pages, limit to first 100 for processing
                if page_count > 100:
                    print(f"[PDF OPTIMIZE] Limiting {filename} from {page_count} to 100 pages")
                    writer = PdfWriter()
                    for i in range(min(100, page_count)):
                        writer.add_page(reader.pages[i])
                    
                    output = io.BytesIO()
                    writer.write(output)
                    optimized_content = output.getvalue()
                    
                    new_size_mb = len(optimized_content) / (1024 * 1024)
                    print(f"[PDF OPTIMIZE] Reduced {filename} from {file_size_mb:.1f} MB to {new_size_mb:.1f} MB")
                    return optimized_content
                    
            except ImportError:
                print(f"[PDF OPTIMIZE] PyPDF2 not available, using original file")
            except Exception as e:
                print(f"[PDF OPTIMIZE] Optimization failed for {filename}: {e}")
            
            # Return original if optimization fails
            return pdf_content
            
        except Exception as e:
            print(f"[PDF OPTIMIZE] Error optimizing {filename}: {e}")
            return pdf_content
    
    def _extract_text_fallback(self, pdf_content: bytes, filename: str) -> Dict:
        """Fallback text extraction using PyPDF2 or pdfplumber when Docling fails"""
        try:
            import io
            
            # Try PyPDF2 first (more reliable and faster)
            try:
                from PyPDF2 import PdfReader
                
                pdf_file = io.BytesIO(pdf_content)
                reader = PdfReader(pdf_file)
                
                text = ""
                page_count = len(reader.pages)
                max_pages = min(50, page_count)  # Limit to first 50 pages for quick processing
                
                print(f"[FALLBACK] Extracting text from first {max_pages} pages of {filename} using PyPDF2")
                
                for page_num in range(max_pages):
                    try:
                        page_text = reader.pages[page_num].extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        print(f"[FALLBACK] Failed to extract page {page_num + 1}: {e}")
                        text += f"\n--- Page {page_num + 1} [EXTRACTION FAILED] ---\n"
                
                if text.strip():
                    print(f"[FALLBACK] ✅ Successfully extracted {len(text)} chars using PyPDF2")
                    return {
                        'success': True,
                        'text_content': text[:50000],  # Limit to 50K chars
                        'method': 'PyPDF2_fallback',
                        'pages_processed': max_pages,
                        'note': f'Fallback extraction from first {max_pages}/{page_count} pages'
                    }
                else:
                    raise Exception("No text extracted from PDF")
                    
            except ImportError:
                print(f"[FALLBACK] PyPDF2 not installed, trying pdfplumber...")
                
                # Fallback to pdfplumber
                import pdfplumber
                
                pdf_file = io.BytesIO(pdf_content)
                text = ""
                
                with pdfplumber.open(pdf_file) as pdf:
                    page_count = len(pdf.pages)
                    max_pages = min(20, page_count)  # Even more conservative with pdfplumber
                    
                    print(f"[FALLBACK] Processing first {max_pages} pages using pdfplumber")
                    
                    for page_num in range(max_pages):
                        try:
                            page_text = pdf.pages[page_num].extract_text()
                            if page_text:
                                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                        except Exception as e:
                            print(f"[FALLBACK] Failed to extract page {page_num + 1}: {e}")
                
                if text.strip():
                    print(f"[FALLBACK] ✅ Successfully extracted {len(text)} chars using pdfplumber")
                    return {
                        'success': True,
                        'text_content': text[:30000],  # Smaller limit for pdfplumber
                        'method': 'pdfplumber_fallback',
                        'pages_processed': max_pages,
                        'note': f'Fallback extraction from first {max_pages}/{page_count} pages'
                    }
                else:
                    raise Exception("No text extracted from PDF")
                    
        except ImportError as e:
            error_msg = f"PDF extraction libraries not installed: {e}"
            print(f"[FALLBACK] ❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text_content': '[FALLBACK_FAILED: Install PyPDF2 or pdfplumber for fallback extraction]',
                'method': 'none_available'
            }
        except Exception as e:
            error_msg = f"Fallback extraction failed: {str(e)}"
            print(f"[FALLBACK] ❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text_content': f'[FALLBACK_FAILED: {error_msg}]',
                'method': 'error'
            }
        
    def analyze_allegation_email_comprehensive(self, email_data: Dict, attachments: List[Dict] = None) -> Dict:
        """
        Comprehensive analysis including email content and attachments
        Extracts multiple alleged persons, agent numbers, and provides detailed reasoning
        """
        # ✅ CRITICAL FIX: Validate email-attachment alignment
        email_id = email_data.get('email_id', 'unknown')
        validation_info = email_data.get('validation_info', {})
        
        print(f"[AI COMPREHENSIVE] ============================================")
        print(f"[AI COMPREHENSIVE] Starting analysis for Email ID: {email_id}")
        print(f"[AI COMPREHENSIVE] Sender: {validation_info.get('sender', 'N/A')}")
        print(f"[AI COMPREHENSIVE] Subject: {validation_info.get('subject', 'N/A')[:60]}...")
        print(f"[AI COMPREHENSIVE] Expected attachments: {validation_info.get('attachment_count', 0)}")
        print(f"[AI COMPREHENSIVE] ============================================")
        
        # ✅ Validate attachment count matches
        expected_count = validation_info.get('attachment_count', 0)
        actual_count = len(attachments) if attachments else 0
        
        if expected_count != actual_count:
            print(f"[AI COMPREHENSIVE] 🚨 WARNING: Attachment count mismatch!")
            print(f"[AI COMPREHENSIVE]    Expected: {expected_count} attachments")
            print(f"[AI COMPREHENSIVE]    Received: {actual_count} attachments")
            print(f"[AI COMPREHENSIVE]    This may indicate attachment misalignment!")
        
        # ✅ Validate attachment filenames match
        expected_filenames = set(validation_info.get('attachment_filenames', []))
        actual_filenames = set([att.get('filename', '') for att in attachments]) if attachments else set()
        
        if expected_filenames != actual_filenames:
            print(f"[AI COMPREHENSIVE] 🚨 WARNING: Attachment filenames don't match!")
            print(f"[AI COMPREHENSIVE]    Expected: {expected_filenames}")
            print(f"[AI COMPREHENSIVE]    Received: {actual_filenames}")
            print(f"[AI COMPREHENSIVE]    This may indicate attachments from wrong email!")
            
            # Log the mismatch for debugging
            missing = expected_filenames - actual_filenames
            extra = actual_filenames - expected_filenames
            if missing:
                print(f"[AI COMPREHENSIVE]    Missing attachments: {missing}")
            if extra:
                print(f"[AI COMPREHENSIVE]    Unexpected attachments: {extra}")
        
        # ✅ Validate each attachment has correct email_id
        if attachments:
            for att in attachments:
                att_email_id = att.get('email_id', 'unknown')
                att_id = att.get('attachment_id', 'unknown')
                filename = att.get('filename', 'unknown')
                
                if att_email_id != email_id:
                    print(f"[AI COMPREHENSIVE] 🚨 CRITICAL: Attachment {att_id} ({filename}) belongs to email {att_email_id}, not {email_id}!")
                    print(f"[AI COMPREHENSIVE]    Skipping this attachment to prevent wrong analysis!")
                    continue  # Skip this attachment
                else:
                    print(f"[AI COMPREHENSIVE] ✅ Attachment {att_id} ({filename}) validated for email {email_id}")
        
        # First, process all attachments to extract text content
        attachment_content = ""
        if attachments:
            print(f"[AI COMPREHENSIVE] Processing {len(attachments)} attachments")
            
            # ✅ UPDATED: PDF processing enabled with Docling API (supports up to 100MB)
            # Using proper JSON format with base64-encoded content - no fallback methods needed!
            for attachment in attachments:
                    filename = attachment.get('filename', 'Unknown')
                    file_data = attachment.get('file_data')  # ✅ Binary data from database (ONLY source)
                    att_email_id = attachment.get('email_id', 'unknown')
                    att_id = attachment.get('attachment_id', 'unknown')
                    
                    # ✅ CRITICAL: Skip attachments that don't belong to this email
                    if att_email_id != email_id:
                        print(f"[AI COMPREHENSIVE] 🚨 Skipping attachment {att_id} ({filename}) - belongs to email {att_email_id}, not {email_id}")
                        continue
                    
                    # ✅ BINARY VALIDATION: Ensure binary data exists
                    if not file_data:
                        print(f"[AI COMPREHENSIVE] 🚨 Skipping attachment {att_id} ({filename}) - NO binary data in database!")
                        print(f"[AI COMPREHENSIVE]    This indicates incomplete upload or database corruption")
                        continue
                    
                    file_size_kb = len(file_data) / 1024
                    file_size_mb = len(file_data) / (1024 * 1024)
                    print(f"[AI COMPREHENSIVE] Processing binary attachment: {filename} ({file_size_kb:.1f} KB) for email {email_id}")
                    
                    # Process PDF binary data with Docling (now supports up to 100MB!)
                    if filename.lower().endswith('.pdf'):
                        print(f"[AI COMPREHENSIVE] Processing PDF with Docling: {filename} ({file_size_mb:.1f} MB)")
                        
                        # ✅ ENHANCED: Use Docling with timeout handling and fallback
                        doc_result = self.process_attachment_with_docling(
                            file_data=file_data,  # ✅ Pass binary data directly
                            filename=filename
                        )
                        
                        if doc_result.get('success'):
                            extracted_text = doc_result.get('text_content', '')
                            method_used = doc_result.get('method', 'unknown')
                            note = doc_result.get('note', '')
                            
                            # ✅ FIX: Clean up the extracted text - remove ONLY markdown image syntax with base64 data
                            import re
                            # Remove markdown image syntax: ![alt](data:image/...)
                            clean_text = re.sub(r'!\[Image\]\(data:image/[^)]+\)', '[IMAGE]', extracted_text)
                            # Remove inline base64 images ONLY if they're in markdown image format
                            clean_text = re.sub(r'!\[[^\]]*\]\(data:image/[^;]+;base64,[A-Za-z0-9+/=]+\)', '[IMAGE]', clean_text)
                            
                            # ⚠️ CRITICAL: Log BEFORE and AFTER to verify we're not removing too much
                            chars_before = len(extracted_text)
                            chars_after = len(clean_text)
                            chars_removed = chars_before - chars_after
                            
                            if chars_removed > chars_before * 0.5:  # If we removed more than 50%
                                print(f"[AI COMPREHENSIVE] ⚠️ WARNING: Image cleaning removed {chars_removed:,} chars ({chars_removed/chars_before*100:.1f}%) from {filename}")
                                print(f"[AI COMPREHENSIVE] ⚠️ This may indicate aggressive regex matching - using original text instead")
                                clean_text = extracted_text  # Use original to preserve content
                            
                            # Indicate extraction method in output
                            method_tag = f"[{method_used.upper()}]"
                            if note:
                                method_tag += f" ({note})"
                            
                            print(f"[AI COMPREHENSIVE] ✅ {method_used} extracted {len(clean_text)} chars from {filename} (cleaned from {chars_before} chars)")
                            
                            # ✅ Add extracted text to attachment content (no truncation - use full content)
                            attachment_content += f"\n\n--- {filename} (Email {email_id}, Attachment {att_id}) {method_tag} ---\n"
                            attachment_content += clean_text
                            
                            print(f"[AI COMPREHENSIVE] Added {len(clean_text)} chars to attachment content (total now: {len(attachment_content)} chars)")
                        else:
                            error_msg = doc_result.get('error', 'Unknown error')
                            method_used = doc_result.get('method', 'unknown')
                            extracted_partial = doc_result.get('text_content', '')
                            
                            print(f"[AI COMPREHENSIVE] ⚠️ {method_used} extraction issue for {filename}: {error_msg}")
                            
                            # Even if "failed", there might be partial content from fallback methods
                            if extracted_partial and len(extracted_partial) > 50:
                                print(f"[AI COMPREHENSIVE] ℹ️ Using partial content ({len(extracted_partial)} chars) from {filename}")
                                attachment_content += f"\n\n--- {filename} (Email {email_id}, Attachment {att_id}) [PARTIAL: {error_msg}] ---\n"
                                attachment_content += extracted_partial
                            else:
                                attachment_content += f"\n\n--- {filename} (Email {email_id}, Attachment {att_id}) [FAILED: {error_msg}] ---\n"
                    else:
                        print(f"[AI COMPREHENSIVE] ⚠️ Skipping non-PDF file: {filename} (AI can only process PDFs)")
                        attachment_content += f"\n\n--- {filename} (Non-PDF - skipped) ---\n"
        else:
            print(f"[AI COMPREHENSIVE] No attachments provided")
        
        # Create comprehensive analysis prompt
        prompt = self._create_comprehensive_analysis_prompt(email_data, attachment_content)
        
        # ✅ DEBUG: Log what we're sending to AI to verify email-attachment alignment
        print(f"[AI COMPREHENSIVE] 📋 SENDING TO AI FOR ANALYSIS:")
        print(f"[AI COMPREHENSIVE]    Email ID: {email_id}")
        print(f"[AI COMPREHENSIVE]    Email Subject: {email_data.get('subject', 'N/A')[:80]}")
        print(f"[AI COMPREHENSIVE]    Email Body Length: {len(email_data.get('body', ''))} chars")
        print(f"[AI COMPREHENSIVE]    Attachment Content Length: {len(attachment_content)} chars")
        if attachment_content:
            # Show first 300 chars of attachment to verify it matches this email
            first_chars = attachment_content[:300].replace('\n', ' ')
            print(f"[AI COMPREHENSIVE]    Attachment Preview: {first_chars}...")
        
        try:
            # Call LLM for comprehensive analysis
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.LLM_MODEL,
                    "prompt": prompt,
                    "max_tokens": 3000,  # Increased to handle complex cases with multiple persons
                    "temperature": 0.3,  # Balanced for analytical tasks
                    "stop": ["</comprehensive_analysis>"]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('choices', [{}])[0].get('text', '')
                print(f"[DEBUG] Comprehensive LLM response: {analysis_text[:300]}...")
                parsed_result = self._parse_comprehensive_analysis(analysis_text)
                print(f"[DEBUG] Comprehensive parsed analysis: {parsed_result}")
                return parsed_result
            else:
                print(f"LLM API error: {response.status_code} - {response.text}")
                return self._get_default_comprehensive_analysis()
                
        except Exception as e:
            print(f"[ERROR] Error calling LLM API for comprehensive analysis: {e}")
            return self._get_default_comprehensive_analysis()

    def _create_comprehensive_analysis_prompt(self, email_data: Dict, attachment_content: str) -> str:
        """Create comprehensive analysis prompt for detailed investigation"""
        # ✅ CRITICAL LOGGING: Show how much attachment content we're including
        attachment_preview = attachment_content[:self.prompt_attachment_limit] if attachment_content else 'No attachments found'
        print(f"[PROMPT DEBUG] Email body length: {len(email_data.get('body', ''))}")
        print(f"[PROMPT DEBUG] Full attachment content length: {len(attachment_content)}")
        print(f"[PROMPT DEBUG] Attachment content included in prompt: {len(attachment_preview)} chars (limit: {self.prompt_attachment_limit})")
        print(f"[PROMPT DEBUG] Attachment text limit per PDF: {self.attachment_text_limit} chars")
        if attachment_content:
            print(f"[PROMPT DEBUG] First 200 chars of attachment: {attachment_content[:200]}...")
        
        # ✅ DEBUG: Show email body preview to verify alignment
        email_body_preview = (email_data.get('body', '')[:300] if email_data.get('body') else 'NO BODY')
        print(f"[PROMPT DEBUG] Email body preview: {email_body_preview}...")
        
        # ✅ Add email context for validation
        validation_info = email_data.get('validation_info', {})
        email_context = f"""
EMAIL CONTEXT (For Your Reference - Ensure Analysis Matches This Email):
- Email ID: {validation_info.get('email_id', 'N/A')}
- Sender: {validation_info.get('sender', 'N/A')}
- Subject: {validation_info.get('subject', 'N/A')}
- Attachment Count: {validation_info.get('attachment_count', 0)}
- Attachments: {', '.join(validation_info.get('attachment_filenames', [])) if validation_info.get('attachment_filenames') else 'None'}
"""
        
        return f"""
<comprehensive_analysis_task>
You are an expert AI helping insurance regulators analyze complaints. 

CRITICAL: Respond ONLY with valid JSON. No explanations, no reasoning, no additional text. Just pure JSON.

{email_context}

EMAIL FORWARDING INFO (Context only):
SUBJECT: {email_data.get('subject', 'N/A')}
SENDER: {email_data.get('sender', 'N/A')}
RECIPIENTS: {email_data.get('recipients', 'N/A')}
BODY: {email_data.get('body', 'N/A')[:3000]}...

ATTACHMENT CONTENT (CRITICAL - READ CAREFULLY):
{attachment_content[:self.prompt_attachment_limit] if attachment_content else 'No attachments found'}...

ANALYSIS INSTRUCTIONS:
**IMPORTANT**: The PDF attachment contains the main complaint details. Read it carefully and base your analysis primarily on the PDF content, not just the email forwarding text.

⚠️ CRITICAL: Ensure your analysis is based on the attachment content shown above. Do NOT mix up content from different emails.

🚨 **ABSOLUTELY PROHIBITED - DO NOT HALLUCINATE:**
- DO NOT make up names that are not explicitly written in the documents
- DO NOT guess or infer people's names from context
- DO NOT create fictional agent numbers, license numbers, or company names
- If you cannot find a specific piece of information in the text, LEAVE IT EMPTY ("")
- ONLY extract information that is EXPLICITLY STATED in the documents
- If a field asks for a name but no name appears in the documents, return empty strings for that person
- Example: If the document only mentions "AXA" without any person's name, return:
  {{"name_english": "", "name_chinese": "", "agent_company_broker": "AXA", "role": "Broker"}}

� **CRITICAL INSTRUCTION - PDF CONTENT PRIORITY:**
   - The EMAIL BODY often just says "forwarding" or references case numbers
   - The PDF ATTACHMENT contains the ACTUAL complaint details!
   - Base your analysis on the PDF ATTACHMENT content, NOT the email forwarding text
   - Ignore email body if it's just administrative forwarding - focus on PDF!

�🔍 **CHINESE FORM FIELD RECOGNITION** - Many documents are Chinese whistleblowing or investigation forms. Look for these specific field labels:
   - "受嫌人姓名" / "被告人" / "涉事人" / "被投訴人" = Alleged Person Name (THIS IS WHO IS ACCUSED!)
   - "相關機構" / "所屬機構" / "公司" / "所屬公司" = Company/Organization  
   - "工作部門" / "職位" / "職級" / "部門" = Department/Role/Position
   - "指控" / "投訴事項" / "違規行為" / "指責" = Allegation/Complaint Type
   - When you see these fields, the person named AFTER the field label is the alleged person, NOT the recipient!

📋 **DOCUMENT TYPE CLASSIFICATION** - Identify the document type:
   - If contains "whistleblowing" / "舉報" / "匿名投訴" / "檢舉" → Type: WHISTLEBLOWING (person in form is ACCUSED)
   - If contains "case reference" like MC/ENQ/XX/XX → Type: ADMINISTRATIVE (check if new case or forwarding)
   - If addressed TO a senior executive BUT they appear in "受嫌人姓名" field → They are ACCUSED, not recipient!
   - If document says "關於 [name]" or "有關 [name]" → [name] is likely the alleged person

👔 **EXECUTIVE ROLE CLASSIFICATION** - Correctly identify roles:
   - "Chief" / "Director" / "Officer" / "首席" / "總監" / "主管" → Role: "Executive" (NOT Agent/Broker)
   - "Agent" / "代理" / "營業代表" → Role: "Agent"
   - "Broker" / "經紀" / "保險經紀" → Role: "Broker"
   - "Manager" / "經理" → Role: "Manager"
   - Senior titles (Chief Operating Officer, Chief Executive Officer, etc.) are "Executive" roles

💰 **BRIBERY & CORRUPTION DETECTION** - Recognize these serious allegations:
   - "賄賂" / "貪污" / "回佣" / "kickback" / "bribery" / "corruption" → Allegation Type: "Breach of duty" or "Professional misconduct"
   - "利益衝突" / "conflict of interest" → Allegation Type: "Breach of duty"
   - "機密資訊牟利" / "using confidential info for profit" → Allegation Type: "Breach of duty"
   - "濫用職權" / "abuse of power" → Allegation Type: "Professional misconduct"
   - These are SERIOUS allegations - extract ALL details from PDF!

YOUR TASKS:

1. **IDENTIFY ALLEGED SUBJECTS FROM PDF** - Look in the PDF content for who is being complained about:
   - ⚠️ CRITICAL: Check for Chinese form fields first (受嫌人姓名, 被投訴人, etc.)
   - If document is whistleblowing/complaint form, extract name from "受嫌人姓名" field
   - Extract BOTH English name AND Chinese name ONLY if EXPLICITLY STATED in the documents
   - Extract agent number, license number, registration number ONLY if EXPLICITLY MENTIONED
   - Extract company/broker name (保險公司名稱, 相關機構) ONLY if EXPLICITLY MENTIONED
   - Extract role/position from "工作部門" or "職位" field if present
   - If multiple people are EXPLICITLY accused, create separate entries for each person
   - If NO person is named, return empty strings for name fields but include the company if mentioned
   - Example with person: "LEUNG SHEUNG MAN EMERSON 梁尚文, Prudential Hong Kong Limited"
   - Example without person: {{"name_english": "", "name_chinese": "", "agent_company_broker": "AXA", "role": "Broker"}}
   - Example from Chinese form: If you see "受嫌人姓名: Joe Lui" → {{"name_english": "Joe Lui", "name_chinese": "", "role": "Executive"}}

2. **IDENTIFY ALLEGATION TYPE FROM PDF** - Based on PDF content, choose ONE specific category:
   - Cross-border selling (跨境保險招攬)
   - Unlicensed practice (無牌經營)
   - Misleading promotion (誤導銷售)
   - Unauthorized advice (未經授權提供意見)
   - Illegal commission (非法佣金)
   - Policy churning (不當替換保單)
   - Cold calling (未經同意推銷)
   - Pyramid scheme (傳銷)
   - Fraudulent claims (欺詐索償)
   - **Breach of duty (違反責任) - USE THIS for bribery, corruption, misuse of confidential info, conflict of interest**
   - Money laundering (洗錢)
   - Identity theft (身份盜竊)
   - Regulatory violation (違反規例)
   - Consumer complaint (消費者投訴)
   - **Professional misconduct (專業失當) - USE THIS for abuse of power, improper conduct by executives**
   - Other

3. **WRITE ALLEGATION SUMMARY BASED ON PDF** - Write a clear, concise summary (2-4 sentences in English) focusing on what the PDF attachment reveals:
   - ⚠️ CRITICAL: Summarize the PDF ATTACHMENT content, NOT the email forwarding text!
   - What specific allegations are made in the PDF document?
   - Who is being complained about according to the PDF?
   - What evidence or details are provided in the PDF?
   - Include specific names, dates, amounts, or case references from the PDF
   - For bribery/corruption cases, mention the specific misconduct alleged
   - Keep it factual and precise for regulators to quickly understand

IMPORTANT: 
- agent_company_broker should be the company name (e.g., "Prudential Hong Kong Limited", "AIA", "Manulife")
- role should be "Agent" or "Broker" based on context
- Output ONLY valid JSON, nothing else

Required JSON format (output this EXACTLY):
{{
    "alleged_persons": [
        {{
            "name_english": "LEUNG SHEUNG MAN EMERSON",
            "name_chinese": "梁尚文",
            "agent_number": "",
            "license_number": "",
            "agent_company_broker": "Prudential Hong Kong Limited",
            "role": "Agent"
        }}
    ],
    "allegation_type": "Cold calling",
    "allegation_summary": "The complainant alleges that the agent sent unsolicited mass marketing emails to government employees without consent. The complainant questions how personal data was obtained and requests investigation into data protection violations. Evidence includes email screenshots."
}}
</comprehensive_analysis_task>

<comprehensive_analysis>
"""
    
    def _create_analysis_prompt(self, email_data: Dict) -> str:
        """Create prompt for LLM to analyze insurance allegation emails"""
        return f"""
<analysis_task>
You are an AI assistant helping insurance regulators analyze complaint emails. 
Extract key information from the following email:

SUBJECT: {email_data.get('subject', 'N/A')}
SENDER: {email_data.get('sender', 'N/A')}
RECIPIENTS: {email_data.get('recipients', 'N/A')}
BODY: {email_data.get('body', 'N/A')[:2000]}...

Please analyze this email and provide:

1. ALLEGED_SUBJECT: Who is being accused/complained about? (person, company, agent name)
2. ALLEGATION_TYPE: What type of misconduct? (fraud, unlicensed activity, misselling, etc.)
3. ALLEGATION_SUMMARY: Brief 2-3 sentence summary of the complaint
4. SOURCE_RELIABILITY: Rate 1-5 (1=unreliable, 5=highly reliable) based on:
   - Specific details provided
   - Coherent narrative
   - Evidence mentioned
5. CONTENT_VALIDITY: Rate 1-5 (1=invalid, 5=valid) based on:
   - Severity of allegations
   - Regulatory relevance
   - Actionable information
6. PRIORITY_LEVEL: HIGH/MEDIUM/LOW based on potential regulatory impact
7. KEYWORDS: Key terms for searching similar cases

Format your response as JSON:
{{
    "alleged_subject": "...",
    "allegation_type": "...",
    "allegation_summary": "...",
    "source_reliability": 3,
    "content_validity": 4,
    "priority_level": "MEDIUM",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "confidence_score": 0.85
}}
</analysis_task>

<analysis>
"""

    def _parse_analysis_result(self, analysis_text: str) -> Dict:
        """Parse LLM response into structured data"""
        try:
            print(f"[DEBUG] Parsing analysis text: {analysis_text}")
            # Try to extract JSON from the response
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = analysis_text[start:end]
                print(f"[DEBUG] Extracted JSON: {json_str}")
                result = json.loads(json_str)
                
                # Validate and clean the result
                parsed_result = {
                    'alleged_subject': result.get('alleged_subject', '')[:255],  # DB limit
                    'allegation_type': result.get('allegation_type', '')[:255],
                    'allegation_summary': result.get('allegation_summary', '')[:1000],
                    'source_reliability': min(max(int(result.get('source_reliability', 3)), 1), 5),
                    'content_validity': min(max(int(result.get('content_validity', 3)), 1), 5),
                    'priority_level': result.get('priority_level', 'MEDIUM'),
                    'keywords': result.get('keywords', [])[:10],  # Limit keywords
                    'confidence_score': float(result.get('confidence_score', 0.5)),
                    'ai_analysis_completed': True
                }
                print(f"[DEBUG] Successfully parsed result: {parsed_result}")
                return parsed_result
            else:
                print(f"[ERROR] No valid JSON found in response")
        except Exception as e:
            print(f"[ERROR] Error parsing LLM response: {e}")
            print(f"[DEBUG] Analysis text was: {analysis_text}")
            
        return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict:
        """Return default analysis when AI fails"""
        print(f"[DEBUG] Returning default analysis - AI analysis failed")
        return {
            'alleged_subject': 'AI_ANALYSIS_FAILED',
            'allegation_type': 'REVIEW_REQUIRED',
            'allegation_summary': 'AI analysis failed - manual review required. Check logs for details.',
            'source_reliability': 3,
            'content_validity': 3,
            'priority_level': 'MEDIUM',
            'keywords': ['ai_failed', 'manual_review'],
            'confidence_score': 0.0,
            'ai_analysis_completed': False
        }
    
    def _parse_comprehensive_analysis(self, analysis_text: str) -> Dict:
        """Parse comprehensive LLM response into structured data"""
        try:
            print(f"[DEBUG] Parsing comprehensive analysis: {analysis_text[:500]}...")
            
            # ✅ IMPROVED: Find JSON even if LLM adds thinking text before/after
            # Look for first { and last } to extract JSON block
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = analysis_text[start:end]
                
                # ✅ NEW: Try to clean up any text inside the JSON that's not valid
                # Sometimes LLM adds comments or text inside the JSON structure
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] First JSON parse failed: {e}. Trying to extract valid JSON...")
                    # Try to find a valid JSON object by looking for "alleged_persons" key
                    import re
                    # Find JSON that contains our expected keys
                    pattern = r'\{[^{}]*"alleged_persons"[^{}]*\[[^\[\]]*\][^{}]*"allegation_type"[^{}]*"allegation_summary"[^{}]*\}'
                    match = re.search(pattern, analysis_text, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        result = json.loads(json_str)
                    else:
                        raise ValueError("Could not find valid JSON structure with required keys")
                
                print(f"[DEBUG] Extracted comprehensive JSON: {json_str[:300]}...")
                
                # Parse alleged persons with proper validation
                alleged_persons = []
                for person in result.get('alleged_persons', []):
                    alleged_persons.append({
                        'name_english': person.get('name_english', '')[:255],
                        'name_chinese': person.get('name_chinese', '')[:255],
                        'agent_number': person.get('agent_number', '')[:50],
                        'license_number': person.get('license_number', '')[:50],
                        'company': person.get('company', '')[:255],
                        'role': person.get('role', '')[:100]
                    })
                
                comprehensive_result = {
                    'alleged_persons': alleged_persons,
                    'allegation_type': result.get('allegation_type', '')[:255],
                    'allegation_summary': result.get('allegation_summary', '')[:2000],
                    'ai_analysis_completed': True,
                    'analysis_type': 'comprehensive',
                    # Set to None - let humans manually rate if needed
                    'source_reliability': None,
                    'content_validity': None
                }
                print(f"[DEBUG] Successfully parsed comprehensive result with {len(alleged_persons)} alleged persons")
                return comprehensive_result
            else:
                print(f"[ERROR] No valid JSON found in comprehensive response")
        except Exception as e:
            print(f"[ERROR] Error parsing comprehensive LLM response: {e}")
            
        return self._get_default_comprehensive_analysis()
    
    def _get_default_comprehensive_analysis(self) -> Dict:
        """Return default comprehensive analysis when AI fails"""
        return {
            'alleged_persons': [],
            'allegation_type': 'ANALYSIS_FAILED',
            'allegation_summary': 'Comprehensive AI analysis failed - manual review required',
            'source_reliability': None,
            'content_validity': None,
            'ai_analysis_completed': False,
            'analysis_type': 'comprehensive'
        }
    
    def ai_summarize_email(self, email_data: Dict, attachments: List[Dict] = None) -> Dict:
        """
        Use AI to analyze email including PDF attachments: summary, allegation nature, and alleged person
        Now reads PDF attachments just like analyze_allegation_email_comprehensive()
        """
        try:
            # Process PDF attachments to extract text content (simplified Docling-only approach)
            attachment_content = ""
            if attachments:
                for attachment in attachments:
                    # Only process PDF files
                    filename = attachment.get('filename', '').lower()
                    file_data = attachment.get('file_data')  # Binary data from database
                    
                    # ✅ ENHANCED: Use Docling with timeout handling and fallback
                    if filename.endswith('.pdf') and file_data:
                        print(f"[AI SUMMARIZE] Processing PDF attachment: {filename} ({len(file_data)/1024:.1f} KB)")
                        doc_result = self.process_attachment_with_docling(
                            file_data=file_data,
                            filename=attachment.get('filename', 'document.pdf')
                        )
                        if doc_result.get('success'):
                            method_used = doc_result.get('method', 'docling_api')
                            note = doc_result.get('note', '')
                            extracted_text = doc_result.get('text_content', '')
                            
                            method_indicator = f" [{method_used}]"
                            if note:
                                method_indicator += f" ({note})"
                            
                            # ✅ CRITICAL FIX: Use configurable limit instead of hardcoded 2,000 chars
                            text_to_use = extracted_text[:self.attachment_text_limit]  # Now 15K instead of 2K!
                            
                            attachment_content += f"\n\n--- PDF: {attachment.get('filename', 'Unknown')}{method_indicator} ---\n"
                            attachment_content += text_to_use
                            
                            print(f"[AI SUMMARIZE] Successfully extracted {len(extracted_text)} chars via {method_used}")
                            print(f"[AI SUMMARIZE] Using {len(text_to_use)} chars for AI analysis (limit: {self.attachment_text_limit})")
                        else:
                            method_used = doc_result.get('method', 'unknown')
                            error_msg = doc_result.get('error', 'Unknown error')
                            partial_content = doc_result.get('text_content', '')
                            
                            # Use partial content if available
                            if partial_content and len(partial_content) > 50:
                                # ✅ CRITICAL FIX: Use more partial content instead of limiting to 1,000 chars
                                partial_text_to_use = partial_content[:self.attachment_text_limit // 2]  # Half limit for partial
                                attachment_content += f"\n\n--- PDF: {attachment.get('filename', 'Unknown')} [PARTIAL: {method_used}] ---\n"
                                attachment_content += partial_text_to_use
                                print(f"[AI SUMMARIZE] Using partial content from {filename}: {len(partial_content)} total, {len(partial_text_to_use)} used")
                            else:
                                attachment_content += f"\n\n--- PDF: {attachment.get('filename', 'Unknown')} [FAILED] ---\n"
                                print(f"[AI SUMMARIZE] Failed to extract content from PDF: {filename} ({error_msg})")
            
            # Enhanced prompt for comprehensive analysis focusing on EMAIL BODY + ATTACHMENTS
            email_body = email_data.get('body', '')
            
            # Clean and prepare email body for analysis
            if email_body:
                # Remove HTML tags for cleaner analysis
                import re
                clean_body = re.sub(r'<[^>]+>', ' ', email_body)
                clean_body = re.sub(r'\s+', ' ', clean_body).strip()
                # Use first 3000 characters to avoid token limits
                clean_body = clean_body[:3000] if len(clean_body) > 3000 else clean_body
            else:
                clean_body = "No email body content available"
            
            prompt = f"""You are analyzing an email for a professional investigation report. Focus on the EMAIL BODY CONTENT and PDF ATTACHMENTS to understand what this email is really about.

EMAIL DETAILS:
Subject: {email_data.get('subject', 'N/A')}
From: {email_data.get('sender', 'N/A')}
To: {email_data.get('recipients', 'N/A')}

EMAIL BODY CONTENT:
{clean_body}

PDF ATTACHMENT CONTENT:
{attachment_content if attachment_content else 'No PDF attachments'}

INSTRUCTIONS:
1. READ THE EMAIL BODY AND PDF ATTACHMENTS CAREFULLY - focus on what the actual content says
2. Determine what type of issue/complaint/inquiry this email is about based on the content
3. Identify who is being complained about or investigated based on the content
4. Create a professional summary based on what you read

Respond in JSON format:
{{
    "email_summary": "Professional 2-3 sentence summary based on email body and PDF content",
    "allegation_nature": "Specific allegation type (e.g., Cross-border Insurance Solicitation, Unlicensed Practice, Mis-selling, Fraud, Consumer Complaint, Inquiry, Investigation Request)",
    "alleged_person": "Name/company being complained about based on the content",
    "email_type": "complaint/inquiry/response/follow-up/investigation",
    "confidence": "High/Medium/Low confidence in analysis"
}}

Analysis:"""
            
            # ✅ CRITICAL LOGGING: Show total content lengths before sending to AI
            print(f"[AI SUMMARIZE] Analyzing email + {len(attachments) if attachments else 0} attachments for email {email_data.get('id', 'unknown')}...")
            print(f"[AI SUMMARIZE] Email body: {len(email_body)} chars")
            print(f"[AI SUMMARIZE] Total attachment content: {len(attachment_content)} chars") 
            print(f"[AI SUMMARIZE] Attachment text limit per PDF: {self.attachment_text_limit} chars")
            if attachment_content:
                print(f"[AI SUMMARIZE] First 200 chars of attachments: {attachment_content[:200]}...")
            
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.LLM_MODEL,
                    "prompt": prompt,
                    "max_tokens": 1500,  # Increased for comprehensive summaries
                    "temperature": 0.3,  # Balanced for analysis
                    "stop": ["</ai_summary>"]
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_content = result.get('choices', [{}])[0].get('text', '')
                
                print(f"[AI SUMMARIZE] AI response received for body analysis: {ai_content[:300]}...")
                
                # Parse AI response
                try:
                    # Extract JSON from response
                    start_idx = ai_content.find('{')
                    end_idx = ai_content.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = ai_content[start_idx:end_idx]
                        parsed_result = json.loads(json_str)
                        
                        # Validate that we got meaningful content based on body analysis
                        summary = parsed_result.get('email_summary', '')
                        if len(summary) > 20:  # Ensure we got a real summary
                            print(f"[AI SUMMARIZE] Successfully analyzed email body - Summary: {summary[:100]}...")
                            return {
                                'success': True,
                                'email_summary': summary,
                                'allegation_nature': parsed_result.get('allegation_nature', 'Unknown'),
                                'alleged_person': parsed_result.get('alleged_person', email_data.get('alleged_subject', 'Unknown')),
                                'investigation_points': parsed_result.get('investigation_points', []),
                                'email_type': parsed_result.get('email_type', 'unknown'),
                                'confidence': parsed_result.get('confidence', 'Medium')
                            }
                        else:
                            print(f"[AI SUMMARIZE] AI response too short, using fallback")
                            
                except json.JSONDecodeError as e:
                    print(f"[AI SUMMARIZE] JSON parsing error in body analysis: {e}")
                    print(f"[AI SUMMARIZE] Raw response: {ai_content}")
                    
            else:
                print(f"[AI SUMMARIZE] API call failed with status: {response.status_code}")
                print(f"[AI SUMMARIZE] Response: {response.text}")
                
        except Exception as e:
            print(f"[AI SUMMARIZE] Error analyzing email body: {e}")
            import traceback
            traceback.print_exc()
            
        # Enhanced fallback summary based on email body when AI fails
        email_body = email_data.get('body', '')
        if email_body:
            # Try to extract meaningful content from email body for fallback
            import re
            clean_body = re.sub(r'<[^>]+>', ' ', email_body)
            clean_body = re.sub(r'\s+', ' ', clean_body).strip()
            
            # Extract first meaningful sentence from body
            sentences = clean_body.split('.')[:2]  # First 2 sentences
            body_preview = '. '.join(sentences).strip()[:150]
            if len(body_preview) > 20:
                fallback_summary = f"Email content: {body_preview}..."
            else:
                fallback_summary = f"Email from {email_data.get('sender', 'Unknown')} with subject: {email_data.get('subject', 'No subject')[:50]}..."
        else:
            fallback_summary = f"Email from {email_data.get('sender', 'Unknown')} with subject: {email_data.get('subject', 'No subject')[:50]}..."
        
        return {
            'success': False,
            'email_summary': fallback_summary,
            'allegation_nature': email_data.get('alleged_nature', 'General Inquiry'),
            'alleged_person': email_data.get('alleged_subject', 'Unknown'),
            'investigation_points': ['Manual review required - AI analysis failed'],
            'email_type': 'unknown',
            'confidence': 'Low'
        }
    
    def ai_group_emails_for_export(self, emails: List[Dict]) -> Dict:
        """
        Use company LLM to intelligently group emails for export
        Returns grouped emails with AI-determined relationships
        """
        try:
            print(f"[AI GROUPING] Processing {len(emails)} emails for intelligent grouping")
            
            # Prepare email data for AI analysis
            email_summaries = []
            for email in emails:
                summary = {
                    'id': email.get('id'),
                    'subject': email.get('subject', '')[:200],
                    'sender': email.get('sender', ''),
                    'recipients': email.get('recipients', ''),
                    'body_preview': email.get('body', '')[:500],
                    'received': str(email.get('received', '')),
                    'alleged_subject': email.get('alleged_subject', ''),
                    'alleged_nature': email.get('alleged_nature', '')
                }
                email_summaries.append(summary)
            
            # Create AI grouping prompt
            prompt = self._create_ai_grouping_prompt(email_summaries)
            
            # Call LLM for intelligent grouping
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.LLM_MODEL,
                    "prompt": prompt,
                    "max_tokens": 6000,  # Large enough for grouping many emails
                    "temperature": 0.15,  # Lower for factual extraction tasks
                    "stop": ["</ai_grouping>"]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                grouping_text = result.get('choices', [{}])[0].get('text', '')
                print(f"[AI GROUPING] LLM response: {grouping_text[:300]}...")
                
                parsed_groups = self._parse_ai_grouping_result(grouping_text)
                if parsed_groups.get('ai_grouping_success'):
                    print(f"[AI GROUPING] Successfully grouped emails into {len(parsed_groups.get('email_groups', []))} groups")
                    return parsed_groups
                else:
                    print(f"[AI GROUPING] AI grouping failed, using fallback")
                    return self._fallback_grouping(emails)
            else:
                print(f"[AI GROUPING] API error: {response.status_code} - {response.text}")
                return self._fallback_grouping(emails)
                
        except Exception as e:
            print(f"[ERROR] Error in AI email grouping: {e}")
            return self._fallback_grouping(emails)

    def _create_ai_grouping_prompt(self, email_summaries: List[Dict]) -> str:
        """Create ultra-strict title-based grouping prompt for LLM"""
        # Process all emails for strict title-based grouping
        print(f"[AI GROUPING] Processing {len(email_summaries)} emails with ULTRA-STRICT title matching")
        
        emails_text = ""
        for i, email in enumerate(email_summaries):
            # Show full subject for precise matching
            subject_full = email['subject']
            sender_short = email['sender'][:30]
            
            emails_text += f"""
EMAIL_{i+1}:
ID: {email['id']}
Subject: "{subject_full}"
Sender: {sender_short}
---"""

        return f"""
<ai_grouping_task>
You are an AI for STRICT email title grouping. Group emails ONLY if they have IDENTICAL core subjects after removing prefixes.

EMAILS TO GROUP:
{emails_text}

**RULES:**
1. Remove prefixes: "Re:", "FW:", "Fwd:", "Forward:", "Reply:", "回复:", "转发:", "轉發:"
2. Group ONLY if core subjects are IDENTICAL (case-insensitive)
3. Different subjects = Different groups (even if same person/topic)

**Examples:**
✓ SAME: "請發出1月對賬單" + "Re: 請發出1月對賬單" = Group together
✗ DIFFERENT: "Billy Ng complaint" + "Billy Ng inquiry" = Separate groups

**Output JSON:**
{{
    "email_groups": [
        {{
            "group_id": "EXACT_001",
            "group_name": "Email Title: [core subject]",
            "email_ids": [list of IDs],
            "core_subject": "[subject after removing prefixes]"
        }}
    ],
    "ungrouped_emails": [IDs with unique subjects],
    "grouping_summary": {{
        "total_emails": {len(email_summaries)},
        "total_groups": 0,
        "ungrouped_count": 0
    }}
}}
</ai_grouping_task>

<ai_grouping>
"""

    def _parse_ai_grouping_result(self, grouping_text: str) -> Dict:
        """Parse AI grouping response into structured data"""
        try:
            print(f"[AI GROUPING] Parsing AI grouping result, text length: {len(grouping_text)}")
            
            # Find JSON block with better handling
            start = grouping_text.find('{')
            
            # Find matching closing brace
            brace_count = 0
            end_pos = -1
            
            if start >= 0:
                for i, char in enumerate(grouping_text[start:], start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
            
            if start >= 0 and end_pos > start:
                json_str = grouping_text[start:end_pos]
                print(f"[AI GROUPING] Extracted JSON block: {len(json_str)} chars")
                
                try:
                    result = json.loads(json_str)
                    print(f"[AI GROUPING] Successfully parsed JSON")
                    
                    # Validate and structure the grouping result
                    email_groups = []
                    for group in result.get('email_groups', []):
                        email_groups.append({
                            'group_id': group.get('group_id', f'GROUP_{len(email_groups)+1:03d}'),
                            'group_name': group.get('group_name', 'Unnamed Group'),
                            'group_type': group.get('group_type', 'unknown'),
                            'description': group.get('description', ''),
                            'email_ids': group.get('email_ids', []),
                            'main_alleged_subject': group.get('main_alleged_subject', ''),
                            'allegation_type': group.get('allegation_type', ''),
                            'group_priority': group.get('group_priority', 'MEDIUM'),
                            'participants': group.get('participants', []),
                            'date_range': group.get('date_range', ''),
                            'reasoning': group.get('reasoning', '')
                        })
                    
                    return {
                        'email_groups': email_groups,
                        'ungrouped_emails': result.get('ungrouped_emails', []),
                        'grouping_summary': result.get('grouping_summary', {}),
                        'ai_grouping_success': True
                    }
                    
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON decode error: {e}")
                    print(f"[DEBUG] Problematic JSON: {json_str[:500]}...")
                    return self._get_default_grouping_result()
            else:
                print("[ERROR] No valid JSON found in AI grouping response")
                return self._get_default_grouping_result()
                
        except Exception as e:
            print(f"[ERROR] Error parsing AI grouping response: {e}")
            return self._get_default_grouping_result()
    
    def _get_default_grouping_result(self) -> Dict:
        """Return default grouping result when parsing fails"""
        return {
            'email_groups': [],
            'ungrouped_emails': [],
            'grouping_summary': {
                'total_emails': 0,
                'total_groups': 0,
                'ungrouped_count': 0,
                'main_group_types': []
            },
            'ai_grouping_success': False
        }

    def _fallback_grouping(self, emails: List[Dict]) -> Dict:
        """Simplified fallback grouping - STRICT title-based threading only"""
        import re
        
        def clean_subject(subject):
            """Clean subject for strict title matching"""
            if not subject:
                return ""
            clean = subject.lower().strip()
            # Remove prefixes iteratively
            prefixes = ['re:', 'fw:', 'fwd:', 'forward:', 'reply:', '回复:', '回复：', '转发:', '转发：', '轉發:', '轉發：']
            changed = True
            while changed:
                changed = False
                for prefix in prefixes:
                    if clean.startswith(prefix):
                        clean = clean[len(prefix):].strip().lstrip(':').strip()
                        changed = True
                        break
                # Remove email tags like [EXTERNAL]
                if clean.startswith('[') and ']' in clean:
                    clean = clean[clean.find(']')+1:].strip()
                    changed = True
            return re.sub(r'\s+', ' ', clean).strip()
        
        # Group by exact core subject
        title_groups = {}
        ungrouped = []
        
        for email in emails:
            email_id = email.get('id')
            subject = email.get('subject', '')
            core_subject = clean_subject(subject)
            
            # Skip if subject too short
            if len(core_subject) < 2:
                ungrouped.append(email_id)
                continue
            
            # Group by core subject
            if core_subject not in title_groups:
                title_groups[core_subject] = {'email_ids': [], 'has_replies': False}
            
            title_groups[core_subject]['email_ids'].append(email_id)
            # Check for reply patterns
            if any(p in subject.lower() for p in ['re:', 'fw:', 'fwd:', 'reply', '回复', '转发', '轉發']):
                title_groups[core_subject]['has_replies'] = True
        
        # Create groups only for multiple emails or reply threads
        email_groups = []
        group_counter = 1
        
        for core_subject, data in title_groups.items():
            email_count = len(data['email_ids'])
            if email_count > 1 or data['has_replies']:
                email_groups.append({
                    'group_id': f'EXACT_{group_counter:03d}',
                    'group_name': f'Email Thread: {core_subject[:60]}' if data['has_replies'] else f'Same Title: {core_subject[:60]}',
                    'group_type': 'exact_reply_thread' if data['has_replies'] else 'exact_title_match',
                    'email_ids': data['email_ids'],
                    'core_subject': core_subject
                })
                group_counter += 1
            else:
                ungrouped.extend(data['email_ids'])
        
        return {
            'email_groups': email_groups,
            'ungrouped_emails': ungrouped,
            'grouping_summary': {
                'total_emails': len(emails),
                'total_groups': len(email_groups),
                'ungrouped_count': len(ungrouped),
                'grouping_method': 'ultra_strict_title_only'
            },
            'ai_grouping_success': False,
            'fallback_method': 'ultra_strict_title_matching'
        }

    # ✅ OBSOLETE METHODS: No longer needed with Docling 100MB support
    # The following methods were used when Docling had a 10MB limit
    # Now kept for reference but not used in production
    
    def extract_pdf_images_to_vlm(self, file_data: bytes, filename: str, max_pages: int = 5) -> Dict:
        """
        Extract PDF pages as images and send to VLM for OCR and text extraction
        
        This method is for large scanned PDFs that:
        1. Cannot use Docling (>10MB size limit)
        2. Have no text layer (PyPDF2 extraction fails)
        
        Uses pdf2image to convert pages to images, then VLM (Qwen3-VL) reads them with OCR.
        
        Args:
            file_data: Binary PDF data from database
            filename: Original filename for logging
            max_pages: Maximum pages to process (default 5 to avoid timeout)
            
        Returns:
            Dict with 'success', 'text_content', 'method', 'error'
        """
        import io
        import base64
        
        try:
            from pdf2image import convert_from_bytes
            
            print(f"[VLM OCR] Converting PDF to images: {filename} (max {max_pages} pages)")
            print(f"[VLM OCR] ⚠️ Warning: Processing {max_pages} pages may take several minutes...")
            
            # Convert PDF to images (limit to first N pages to avoid timeout)
            # Use lower DPI to reduce memory usage
            images = convert_from_bytes(
                file_data, 
                first_page=1, 
                last_page=max_pages, 
                dpi=120,  # Lower DPI to reduce memory/processing time
                fmt='jpeg',
                jpegopt={'quality': 75}
            )
            
            if not images:
                raise Exception("No images extracted from PDF")
            
            print(f"[VLM OCR] Extracted {len(images)} images from {filename}")
            
            # Process each page with VLM
            extracted_text = ""
            success_count = 0
            
            for page_num, image in enumerate(images, 1):
                print(f"[VLM OCR] Processing page {page_num}/{len(images)}...")
                
                try:
                    # Convert image to base64
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='JPEG', quality=75)
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                    
                    # Check image size (skip if >5MB base64)
                    if len(img_base64) > 5 * 1024 * 1024:
                        print(f"[VLM OCR] ⚠️ Page {page_num} image too large, skipping...")
                        extracted_text += f"\n--- Page {page_num} [IMAGE TOO LARGE] ---\n"
                        continue
                    
                    # Send to VLM for OCR
                    page_text = self._ocr_image_with_vlm(img_base64, filename, page_num)
                    
                    if page_text:
                        extracted_text += f"\n--- Page {page_num} ---\n{page_text}\n"
                        success_count += 1
                    else:
                        extracted_text += f"\n--- Page {page_num} [OCR FAILED] ---\n"
                        
                except Exception as page_error:
                    print(f"[VLM OCR] ❌ Page {page_num} processing error: {page_error}")
                    extracted_text += f"\n--- Page {page_num} [ERROR: {str(page_error)}] ---\n"
            
            if extracted_text.strip() and success_count > 0:
                print(f"[VLM OCR] ✅ Successfully extracted text from {success_count}/{len(images)} pages")
                return {
                    'success': True,
                    'text_content': extracted_text,
                    'method': 'VLM_OCR',
                    'pages_processed': len(images),
                    'pages_success': success_count
                }
            else:
                raise Exception(f"No text extracted from any page (0/{len(images)} successful)")
                
        except ImportError:
            error_msg = "pdf2image not installed. Install with: pip install pdf2image && apt-get install poppler-utils"
            print(f"[VLM OCR] ❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text_content': ''
            }
        except Exception as e:
            error_msg = f"VLM OCR extraction failed: {str(e)}"
            print(f"[VLM OCR] ❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text_content': ''
            }
    
    def _ocr_image_with_vlm(self, image_base64: str, filename: str, page_num: int) -> str:
        """
        Use VLM (Qwen3-VL) to perform OCR on a single PDF page image
        
        NOTE: This assumes the VLM API supports vision/image input.
        If the API doesn't support images parameter, this will fail gracefully.
        You may need to adjust the API format based on your VLM deployment.
        
        Args:
            image_base64: Base64 encoded JPEG image
            filename: PDF filename for logging
            page_num: Page number for logging
            
        Returns:
            Extracted text from the image
        """
        try:
            prompt = """You are an OCR system. Read the document image and extract all text exactly as shown.

CRITICAL RULES:
1. Output ONLY the text from the document - no thinking, no explanations
2. Do NOT say "I cannot see" or "based on the image"
3. Do NOT add any commentary or analysis
4. Copy the text character-by-character from the image
5. Preserve original formatting, line breaks, and structure

START EXTRACTING NOW:"""
            
            # VLM API call with image
            # NOTE: Adjust this format if your VLM API uses different parameter names
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.LLM_MODEL,
                    "prompt": prompt,
                    "images": [f"data:image/jpeg;base64,{image_base64}"],  # May need adjustment based on API
                    "max_tokens": 4000,
                    "temperature": 0.0,  # Zero temperature for pure OCR extraction
                    "top_p": 0.9,
                    "stop": ["CRITICAL RULES", "You are an OCR", "I cannot see", "Based on"]  # Stop if model starts meta-commentary
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('choices', [{}])[0].get('text', '').strip()
                
                # ✅ CRITICAL: Clean up VLM "thinking" text if present
                # Remove common VLM meta-commentary patterns
                thinking_patterns = [
                    "We are given an image",
                    "I cannot see the image",
                    "Based on the image",
                    "Since I cannot see",
                    "Let me extract",
                    "I must rely on",
                    "The image shows",
                    "Do not omit any text"
                ]
                
                # If text starts with thinking pattern, try to extract just the OCR content
                for pattern in thinking_patterns:
                    if pattern.lower() in text.lower()[:200]:  # Check first 200 chars
                        print(f"[VLM OCR] ⚠️ Page {page_num}: Detected thinking text, cleaning...")
                        # Try to find where actual content starts (usually after first paragraph)
                        lines = text.split('\n')
                        clean_lines = []
                        found_content = False
                        for line in lines:
                            # Skip lines with thinking patterns
                            if any(p.lower() in line.lower() for p in thinking_patterns):
                                continue
                            # Start collecting after we see actual content indicators
                            if line.strip() and (len(line) > 20 or found_content):
                                found_content = True
                                clean_lines.append(line)
                        
                        if clean_lines:
                            text = '\n'.join(clean_lines)
                            print(f"[VLM OCR] ✅ Cleaned thinking text, extracted {len(text)} chars")
                        break
                
                print(f"[VLM OCR] Page {page_num}: Extracted {len(text)} chars")
                return text
            else:
                error_detail = response.text[:200] if response.text else 'No details'
                print(f"[VLM OCR] ❌ Page {page_num} failed: Status {response.status_code} - {error_detail}")
                return ""
                
        except Exception as e:
            print(f"[VLM OCR] ❌ Page {page_num} error: {e}")
            return ""
    
    def extract_pdf_locally(self, file_data: bytes, filename: str) -> Dict:
        """
        Extract text from PDF using local Python library (for large files that exceed Docling API limits)
        
        This is a fallback method for PDFs >10MB that would fail with Docling's nginx limit.
        Uses PyPDF2 for simple text extraction without API calls.
        
        Args:
            file_data: Binary PDF data from database
            filename: Original filename for logging
            
        Returns:
            Dict with 'success', 'text_content', 'error'
        """
        import io
        
        try:
            # Try PyPDF2 first (more reliable)
            try:
                import PyPDF2
                
                pdf_file = io.BytesIO(file_data)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text = ""
                page_count = len(pdf_reader.pages)
                print(f"[LOCAL EXTRACT] Processing {page_count} pages from {filename}")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num} ---\n{page_text}"
                    except Exception as e:
                        print(f"[LOCAL EXTRACT] ⚠️ Failed to extract page {page_num}: {e}")
                        text += f"\n--- Page {page_num} [EXTRACTION FAILED] ---\n"
                
                if text.strip():
                    print(f"[LOCAL EXTRACT] ✅ Successfully extracted {len(text)} chars using PyPDF2")
                    return {
                        'success': True,
                        'text_content': text,
                        'method': 'PyPDF2',
                        'page_count': page_count
                    }
                else:
                    raise Exception("No text extracted from PDF")
                    
            except ImportError:
                print(f"[LOCAL EXTRACT] ⚠️ PyPDF2 not installed, trying pdfplumber...")
                
                # Fallback to pdfplumber
                import pdfplumber
                
                pdf_file = io.BytesIO(file_data)
                text = ""
                
                with pdfplumber.open(pdf_file) as pdf:
                    page_count = len(pdf.pages)
                    print(f"[LOCAL EXTRACT] Processing {page_count} pages from {filename}")
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- Page {page_num} ---\n{page_text}"
                        except Exception as e:
                            print(f"[LOCAL EXTRACT] ⚠️ Failed to extract page {page_num}: {e}")
                
                if text.strip():
                    print(f"[LOCAL EXTRACT] ✅ Successfully extracted {len(text)} chars using pdfplumber")
                    return {
                        'success': True,
                        'text_content': text,
                        'method': 'pdfplumber',
                        'page_count': page_count
                    }
                else:
                    raise Exception("No text extracted from PDF")
                    
        except ImportError as e:
            error_msg = f"PDF extraction libraries not installed: {e}. Install with: pip install PyPDF2 pdfplumber"
            print(f"[LOCAL EXTRACT] ❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text_content': ''
            }
        except Exception as e:
            error_msg = f"Local PDF extraction failed: {str(e)}"
            print(f"[LOCAL EXTRACT] ❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text_content': ''
            }

    def process_attachment_with_docling(self, file_data: bytes = None, filename: str = "document.pdf") -> Dict:
        """
        Use Docling to extract text from PDF attachments with enhanced timeout handling and fallback
        
        MAJOR IMPROVEMENTS:
        - Dynamic timeout based on file size (1 minute per MB, minimum 2 minutes)
        - PDF optimization for large files (>5MB)
        - Automatic fallback to PyPDF2/pdfplumber on timeout
        - Retry logic with exponential backoff
        - Better error handling and reporting
        
        Args:
            file_data: Binary PDF data from database (REQUIRED)
            filename: Original filename for the PDF
            
        Returns:
            Dict with 'success', 'text_content', 'metadata', 'error'
        """
        import base64
        
        try:
            # ✅ BINARY DATA VALIDATION
            if not file_data:
                error_msg = 'No binary data provided - attachment may be corrupted or not uploaded correctly'
                print(f"[DOCLING] ❌ {error_msg}")
                return {
                    'success': False, 
                    'error': error_msg,
                    'text_content': 'PDF binary data missing - manual document review required'
                }
            
            # ✅ FILE SIZE ANALYSIS AND OPTIMIZATION
            original_size_mb = len(file_data) / (1024 * 1024)
            print(f"[DOCLING] Processing PDF: {filename} ({original_size_mb:.1f} MB)")
            
            # Check if file exceeds reasonable processing limits
            if original_size_mb > self.max_sync_file_size_mb:
                print(f"[DOCLING] ⚠️ File {filename} ({original_size_mb:.1f} MB) exceeds sync limit ({self.max_sync_file_size_mb} MB)")
                print(f"[DOCLING] Attempting fallback extraction for immediate analysis...")
                fallback_result = self._extract_text_fallback(file_data, filename)
                fallback_result['note'] = f'Large file ({original_size_mb:.1f} MB) - fallback extraction used'
                return fallback_result
            
            # ✅ PDF OPTIMIZATION FOR LARGE FILES
            if original_size_mb > 5:
                print(f"[DOCLING] File >5MB, attempting optimization...")
                optimized_content = self._optimize_pdf_for_processing(file_data, filename)
                optimized_size_mb = len(optimized_content) / (1024 * 1024)
                
                if len(optimized_content) < len(file_data):
                    print(f"[DOCLING] Optimization reduced size from {original_size_mb:.1f} MB to {optimized_size_mb:.1f} MB")
                    pdf_content = optimized_content
                    file_size_mb = optimized_size_mb
                else:
                    pdf_content = file_data
                    file_size_mb = original_size_mb
            else:
                pdf_content = file_data
                file_size_mb = original_size_mb
            
            # ✅ DYNAMIC TIMEOUT CALCULATION
            dynamic_timeout = self._calculate_dynamic_timeout(file_size_mb)
            print(f"[DOCLING] Using dynamic timeout: {dynamic_timeout}s for {file_size_mb:.1f} MB file")
            
            # ✅ DOCLING API CALL WITH RETRY LOGIC
            return self._call_docling_with_retry(pdf_content, filename, dynamic_timeout, max_retries=3)
            
        except Exception as e:
            error_msg = f"Unexpected error in PDF processing: {str(e)}"
            print(f"[DOCLING] ❌ {error_msg}")
            
            # Try fallback extraction even on unexpected errors
            print(f"[DOCLING] Attempting emergency fallback extraction...")
            try:
                fallback_result = self._extract_text_fallback(file_data, filename)
                fallback_result['note'] = f'Emergency fallback after error: {error_msg}'
                return fallback_result
            except Exception as fallback_error:
                print(f"[DOCLING] ❌ Emergency fallback also failed: {fallback_error}")
                return {
                    'success': False, 
                    'error': f"{error_msg} (fallback also failed)",
                    'text_content': f'[COMPLETE_FAILURE: {error_msg}]'
                }

    def _call_docling_with_retry(self, pdf_content: bytes, filename: str, timeout: int, max_retries: int = 3) -> Dict:
        """Call Docling API with retry logic and automatic fallback on timeout"""
        import base64
        import time
        
        # Prepare request data
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        request_data = {
            'file_sources': [
                {
                    'filename': filename,
                    'base64_string': pdf_base64
                }
            ],
            'options': {
                'to_formats': ['text'],  # Extract as plain text
                'do_ocr': True,              # ✅ Enable OCR for scanned PDFs (correct key)
                'force_full_page_ocr': True, # ✅ Force OCR on all pages, even with embedded text
                'ocr_options': {             # ✅ Configure OCR engine and languages
                    'engine': 'tesseract',   # Use Tesseract OCR engine
                    'lang': 'eng+chi_tra'    # Support English + Traditional Chinese
                },
                'do_table_structure': True,  # Extract table structure
                'include_images': False,     # Don't need images for text analysis
                'abort_on_error': False      # Continue processing even if errors
            }
        }
        
        file_size_mb = len(pdf_content) / (1024 * 1024)
        endpoint = self.docling_api
        
        print(f"[DOCLING] API Call - File: {filename} ({file_size_mb:.1f} MB), Timeout: {timeout}s, Max retries: {max_retries}")
        
        for attempt in range(max_retries + 1):  # 0, 1, 2 for max_retries=2
            try:
                if attempt > 0:
                    wait_time = (2 ** (attempt - 1)) * 5  # 5s, 10s
                    print(f"[DOCLING] Retry attempt {attempt}/{max_retries} after {wait_time}s wait...")
                    time.sleep(wait_time)
                
                print(f"[DOCLING] Calling API (attempt {attempt + 1}/{max_retries + 1})...")
                response = self.session.post(
                    endpoint,
                    headers={'Content-Type': 'application/json'},
                    json=request_data,
                    timeout=timeout
                )
                
                print(f"[DOCLING] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract text content from Docling response
                    document_data = result.get('document', {})
                    
                    # Try to get text from different possible response formats
                    text_content = ""
                    if isinstance(document_data, str):
                        text_content = document_data
                    elif isinstance(document_data, dict):
                        # Try common text fields in order of preference
                        text_content = (
                            document_data.get('text_content', '') or
                            document_data.get('markdown', '') or
                            document_data.get('text', '') or
                            document_data.get('content', '') or
                            str(document_data)
                        )
                    
                    # ✅ CHECK FOR EMPTY OCR RESULT - Use VLM fallback for image-only PDFs
                    if not text_content or len(text_content) < 50:
                        print(f"[DOCLING] ⚠️ OCR returned empty/minimal content ({len(text_content)} chars)")
                        print(f"[DOCLING] This might be a pure-image PDF - trying VLM OCR fallback...")
                        
                        # Try VLM-based image OCR as fallback for scanned PDFs
                        try:
                            vlm_result = self.extract_pdf_images_to_vlm(pdf_content, filename, max_pages=5)
                            if vlm_result.get('success') and len(vlm_result.get('text_content', '')) > 50:
                                print(f"[DOCLING] ✅ VLM OCR extracted {len(vlm_result['text_content'])} chars from image-based PDF")
                                vlm_result['method'] = 'docling_failed_vlm_ocr_fallback'
                                vlm_result['note'] = 'Docling OCR returned empty, used VLM image OCR'
                                return vlm_result
                        except Exception as vlm_error:
                            print(f"[DOCLING] ⚠️ VLM OCR fallback also failed: {vlm_error}")
                        
                        # If VLM also failed and this is last attempt, use standard fallback
                        if attempt == max_retries:
                            print(f"[DOCLING] Last attempt + VLM failed, trying PyPDF2 fallback...")
                            break
                        continue
                    
                    # If we got good content, return it
                    if text_content and len(text_content) > 50:
                        print(f"[DOCLING] ✅ Successfully extracted {len(text_content)} characters from {filename}")
                        return {
                            'text_content': text_content,
                            'metadata': {
                                'processing_time': result.get('processing_time', 0),
                                'status': result.get('status', 'success'),
                                'filename': filename,
                                'attempt': attempt + 1,
                                'timeout_used': timeout
                            },
                            'success': True,
                            'method': 'docling_api'
                        }
                    else:
                        print(f"[DOCLING] ⚠️ Empty or minimal content extracted, may need retry")
                        if attempt == max_retries:  # Last attempt
                            print(f"[DOCLING] Last attempt returned minimal content, trying fallback...")
                            break
                        continue
                        
                elif response.status_code in [502, 503, 504]:  # Server errors - retry
                    print(f"[DOCLING] Server error {response.status_code}, will retry...")
                    if attempt == max_retries:
                        break
                    continue
                    
                else:  # Client errors - don't retry
                    error_msg = f"Status {response.status_code}: {response.text[:200]}"
                    print(f"[DOCLING] ❌ Client error (no retry): {error_msg}")
                    break
                
            except requests.exceptions.ReadTimeout:
                print(f"[DOCLING] ❌ Timeout after {timeout}s (attempt {attempt + 1}/{max_retries + 1})")
                if attempt == max_retries:
                    print(f"[DOCLING] All retries exhausted due to timeout, trying fallback extraction...")
                    break
                continue
                
            except requests.exceptions.ConnectionError as e:
                print(f"[DOCLING] ❌ Connection error (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    break
                continue
                
            except Exception as e:
                print(f"[DOCLING] ❌ Unexpected error (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    break
                continue
        
        # All retries failed - try fallback extraction
        print(f"[DOCLING] All API attempts failed, trying fallback extraction...")
        try:
            fallback_result = self._extract_text_fallback(pdf_content, filename)
            if fallback_result.get('success'):
                fallback_result['note'] = f'Docling API failed after {max_retries + 1} attempts - fallback successful'
                fallback_result['method'] = 'fallback_after_docling_failure'
                print(f"[DOCLING] ✅ Fallback extraction successful")
                return fallback_result
            else:
                print(f"[DOCLING] ❌ Fallback extraction also failed")
                return {
                    'success': False,
                    'error': f'Both Docling API and fallback extraction failed for {filename}',
                    'text_content': f'[EXTRACTION_FAILED: File may be corrupted, scanned without text layer, or too complex]',
                    'method': 'all_methods_failed'
                }
                
        except Exception as fallback_error:
            print(f"[DOCLING] ❌ Fallback extraction error: {fallback_error}")
            return {
                'success': False,
                'error': f'Complete processing failure for {filename}: {fallback_error}',
                'text_content': '[COMPLETE_FAILURE: Unable to extract any text from PDF]',
                'method': 'complete_failure'
            }

# Global AI instance
intelligence_ai = IntelligenceAI()



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
    def __init__(self):
        self.llm_api = "https://ai-poc.corp.ia/vllm/v1"
        self.embedding_api = "https://ai-poc.corp.ia/embedding/v1"
        self.docling_api = "https://ai-poc.corp.ia/docling"
        
        # Configure session for internal corporate network
        self.session = requests.Session()
        self.session.verify = False  # Skip SSL verification for internal services
        self.session.timeout = 60  # Increase timeout for AI processing
        
    def analyze_allegation_email_comprehensive(self, email_data: Dict, attachments: List[Dict] = None) -> Dict:
        """
        Comprehensive analysis including email content and attachments
        Extracts multiple alleged persons, agent numbers, and provides detailed reasoning
        """
        # First, process all attachments to extract text content
        attachment_content = ""
        if attachments:
            print(f"[AI COMPREHENSIVE] Processing {len(attachments)} attachments")
            
            # ✅ UPDATED: PDF processing enabled with correct Docling v1alpha API
            # Using proper JSON format with base64-encoded content
            skip_pdf_processing = False  # Now using correct endpoint and format!
            
            if skip_pdf_processing:
                print(f"[AI COMPREHENSIVE] ⚠️ PDF processing temporarily disabled (Docling service unavailable)")
                print(f"[AI COMPREHENSIVE] Will analyze email body only")
                attachment_content = "PDF attachments available but not processed due to Docling service issues. Analysis based on email content only."
            else:
                for attachment in attachments:
                    filename = attachment.get('filename', 'Unknown')
                    file_data = attachment.get('file_data')  # Binary data from database
                    filepath = attachment.get('filepath')     # Legacy filepath
                    
                    print(f"[AI COMPREHENSIVE] Attachment: {filename}, has_data: {file_data is not None}, filepath: {filepath}")
                    
                    if file_data or filepath:
                        print(f"[AI COMPREHENSIVE] Calling Docling for: {filename}")
                        doc_result = self.process_attachment_with_docling(
                            file_data=file_data,
                            file_path=filepath,
                            filename=filename
                        )
                        if doc_result.get('success'):
                            extracted_text = doc_result.get('text_content', '')
                            
                            # Clean up the extracted text - remove base64 image data
                            import re
                            # Remove base64 image data that's not useful for analysis
                            clean_text = re.sub(r'!\[Image\]\(data:image/[^)]+\)', '[IMAGE]', extracted_text)
                            # Remove long base64 strings
                            clean_text = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]{100,}', '[BASE64_IMAGE]', clean_text)
                            
                            print(f"[AI COMPREHENSIVE] ✅ Successfully extracted {len(extracted_text)} chars from {filename} (cleaned: {len(clean_text)} chars)")
                            attachment_content += f"\n\n--- {filename} ---\n"
                            attachment_content += clean_text
                        else:
                            print(f"[AI COMPREHENSIVE] ❌ Failed to extract from {filename}: {doc_result.get('error', 'Unknown error')}")
                    else:
                        print(f"[AI COMPREHENSIVE] ⚠️ No file_data or filepath provided for {filename}")
        else:
            print(f"[AI COMPREHENSIVE] No attachments provided")
        
        # Create comprehensive analysis prompt
        prompt = self._create_comprehensive_analysis_prompt(email_data, attachment_content)
        
        try:
            # Call LLM for comprehensive analysis
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "hosted_vllm/Qwen3-235B-A22B-GPTQ-Int4",
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
        # Debug: Show how much attachment content we're including
        attachment_preview = attachment_content[:15000] if attachment_content else 'No attachments found'
        print(f"[PROMPT DEBUG] Email body length: {len(email_data.get('body', ''))}")
        print(f"[PROMPT DEBUG] Full attachment content length: {len(attachment_content)}")
        print(f"[PROMPT DEBUG] Attachment content included in prompt: {len(attachment_preview)} chars")
        if attachment_content:
            print(f"[PROMPT DEBUG] First 200 chars of attachment: {attachment_content[:200]}...")
        
        return f"""
<comprehensive_analysis_task>
You are an expert AI helping insurance regulators analyze complaints. 

CRITICAL: Respond ONLY with valid JSON. No explanations, no reasoning, no additional text. Just pure JSON.

EMAIL FORWARDING INFO (Context only):
SUBJECT: {email_data.get('subject', 'N/A')}
SENDER: {email_data.get('sender', 'N/A')}
RECIPIENTS: {email_data.get('recipients', 'N/A')}
BODY: {email_data.get('body', 'N/A')[:3000]}...

ATTACHMENT CONTENT (CRITICAL - READ CAREFULLY):
{attachment_content[:15000] if attachment_content else 'No attachments found'}...

ANALYSIS INSTRUCTIONS:
**IMPORTANT**: The PDF attachment contains the main complaint details. Read it carefully and base your analysis primarily on the PDF content, not just the email forwarding text.

YOUR TASKS:

1. **IDENTIFY ALLEGED SUBJECTS FROM PDF** - Look in the PDF content for who is being complained about:
   - Extract BOTH English name AND Chinese name (if available) 
   - Extract agent number, license number, registration number (if mentioned)
   - Extract company/broker name (保險公司名稱) (if mentioned)
   - If multiple people are accused, create separate entries for each person
   - Example: "LEUNG SHEUNG MAN EMERSON 梁尚文, Prudential Hong Kong Limited"

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
   - Breach of duty (違反責任)
   - Money laundering (洗錢)
   - Identity theft (身份盜竊)
   - Regulatory violation (違反規例)
   - Consumer complaint (消費者投訴)
   - Professional misconduct (專業失當)
   - Other

3. **WRITE ALLEGATION SUMMARY BASED ON PDF** - Write a clear, concise summary (2-4 sentences in English) focusing on what the PDF attachment reveals:
   - What specific allegations are made in the PDF document?
   - Who is being complained about according to the PDF?
   - What evidence or details are provided in the PDF?
   - Include specific names, dates, amounts, or case references from the PDF
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
            # Process PDF attachments to extract text content (SAME AS COMPREHENSIVE FUNCTION)
            attachment_content = ""
            if attachments:
                for attachment in attachments:
                    # Only process PDF files
                    filename = attachment.get('filename', '').lower()
                    file_data = attachment.get('file_data')  # Binary data from database
                    filepath = attachment.get('filepath')     # Legacy filepath
                    
                    if filename.endswith('.pdf') and (file_data or filepath):
                        print(f"[AI SUMMARIZE] Processing PDF attachment: {filename}")
                        doc_result = self.process_attachment_with_docling(
                            file_data=file_data,
                            file_path=filepath,
                            filename=attachment.get('filename', 'document.pdf')
                        )
                        if doc_result.get('success'):
                            attachment_content += f"\n\n--- PDF: {attachment.get('filename', 'Unknown')} ---\n"
                            attachment_content += doc_result.get('text_content', '')[:2000]  # Limit per PDF
                            print(f"[AI SUMMARIZE] Successfully extracted {len(doc_result.get('text_content', ''))} chars from PDF")
                        else:
                            print(f"[AI SUMMARIZE] Failed to extract content from PDF: {filename}")
            
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
            
            print(f"[AI SUMMARIZE] Analyzing email + {len(attachments) if attachments else 0} attachments for email {email_data.get('id', 'unknown')}...")
            print(f"[AI SUMMARIZE] Email body: {len(email_body)} chars, Attachments: {len(attachment_content)} chars")
            
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "hosted_vllm/Qwen3-235B-A22B-GPTQ-Int4",
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
                    "model": "hosted_vllm/Qwen3-235B-A22B-GPTQ-Int4",
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

    def process_attachment_with_docling(self, file_data: bytes = None, file_path: str = None, filename: str = "document.pdf") -> Dict:
        """
        Use Docling to extract text from email attachments using the correct v1alpha API
        
        Args:
            file_data: Binary data from database (preferred)
            file_path: Legacy filepath for migration support
            filename: Original filename for the file upload
        """
        import base64
        
        try:
            # Get file content - support both binary data and filepath
            if file_data:
                pdf_content = file_data
            elif file_path:
                with open(file_path, 'rb') as f:
                    pdf_content = f.read()
            else:
                return {'success': False, 'error': 'No file_data or file_path provided'}
            
            # Base64 encode the PDF content (required by Docling v1alpha API)
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Create the correct JSON request format
            request_data = {
                'file_sources': [
                    {
                        'filename': filename,
                        'base64_string': pdf_base64
                    }
                ],
                'options': {
                    'to_formats': ['text'],  # Extract as plain text
                    'do_ocr': True,         # Enable OCR for scanned PDFs
                    'force_ocr': False,     # Don't replace existing text
                    'do_table_structure': True,  # Extract table structure
                    'include_images': False,     # Don't need images for text analysis
                    'abort_on_error': False      # Continue processing even if errors
                }
            }
            
            # Use the correct Docling v1alpha endpoint
            endpoint = f"{self.docling_api}/v1alpha/convert/source"
            
            print(f"[DOCLING] Calling {endpoint} for file: {filename}")
            
            try:
                response = self.session.post(
                    endpoint,
                    headers={'Content-Type': 'application/json'},
                    json=request_data,
                    timeout=60  # Longer timeout for PDF processing
                )
                
                print(f"[DOCLING] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Debug: Log the Docling response structure
                    print(f"[DOCLING DEBUG] Response keys: {list(result.keys())}")
                    print(f"[DOCLING DEBUG] Response structure: {str(result)[:500]}...")
                    
                    # Extract text content from Docling response
                    document_data = result.get('document', {})
                    
                    # Debug: Check document structure
                    if isinstance(document_data, dict):
                        print(f"[DOCLING DEBUG] Document keys: {list(document_data.keys())}")
                        if 'text_content' in document_data:
                            print(f"[DOCLING DEBUG] Found text_content field with {len(document_data['text_content'])} chars")
                        if 'markdown' in document_data:
                            print(f"[DOCLING DEBUG] Found markdown field with {len(document_data['markdown'])} chars")
                    
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
                    
                    print(f"[DOCLING] ✅ Successfully extracted {len(text_content)} characters from {filename}")
                    print(f"[DOCLING DEBUG] First 300 chars of extracted text: {text_content[:300]}...")
                    
                    return {
                        'text_content': text_content,
                        'metadata': {
                            'processing_time': result.get('processing_time', 0),
                            'status': result.get('status', 'success'),
                            'filename': filename
                        },
                        'success': True,
                        'endpoint_used': endpoint
                    }
                else:
                    error_msg = f"Status {response.status_code}: {response.text[:200]}"
                    print(f"[DOCLING] ❌ {error_msg}")
                    
                    return {
                        'text_content': f'Docling processing failed ({response.status_code}) - manual document review required',
                        'metadata': {'error': error_msg, 'filename': filename},
                        'success': False,
                        'endpoint_used': endpoint
                    }
                    
            except (requests.RequestException, json.JSONDecodeError) as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"[DOCLING] ❌ Request failed: {error_msg}")
                
                return {
                    'text_content': 'Docling service unavailable - manual document review required',
                    'metadata': {'error': error_msg, 'filename': filename},
                    'success': False,
                    'endpoint_used': endpoint
                }
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[DOCLING] ❌ {error_msg}")
            return {
                'success': False, 
                'error': error_msg,
                'text_content': 'PDF processing failed - manual document review required'
            }

# Global AI instance
intelligence_ai = IntelligenceAI()

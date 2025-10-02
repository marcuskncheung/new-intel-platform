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
            for attachment in attachments:
                if attachment.get('filepath'):
                    doc_result = self.process_attachment_with_docling(attachment['filepath'])
                    if doc_result.get('success'):
                        attachment_content += f"\n\n--- {attachment.get('filename', 'Unknown')} ---\n"
                        attachment_content += doc_result.get('text_content', '')
        
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
                    "max_tokens": 2000,  # Increased for comprehensive analysis
                    "temperature": 0.1,
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
        return f"""
<comprehensive_analysis_task>
You are an expert AI assistant helping insurance regulators investigate complaints. You must analyze ALL available content including email and attachments to provide a comprehensive verdict.

EMAIL CONTENT:
SUBJECT: {email_data.get('subject', 'N/A')}
SENDER: {email_data.get('sender', 'N/A')}
RECIPIENTS: {email_data.get('recipients', 'N/A')}
BODY: {email_data.get('body', 'N/A')[:3000]}...

ATTACHMENT CONTENT:
{attachment_content[:2000] if attachment_content else 'No attachments found'}...

ANALYSIS REQUIREMENTS:

1. ALLEGED_PERSONS: Extract ALL individuals/entities being complained about
   - Search for names in both English AND Chinese characters
   - Include agent numbers, license numbers if mentioned
   - If multiple persons, create separate entries

2. DETAILED_REASONING: Provide comprehensive analysis reasoning
   - What evidence supports the allegations?
   - What regulatory violations are suggested?
   - Cross-reference email and attachment content

3. AGENT_LICENSE_NUMBERS: Extract any license/agent numbers mentioned
   - Format: agent number, license number, registration number
   - Link to specific alleged persons

4. REGULATORY_IMPACT: Assess severity and regulatory significance
   - Consumer harm potential
   - Market conduct issues
   - Licensing violations

5. INVESTIGATION_PRIORITY: Rate urgency and resource allocation
   - HIGH: Serious violations, consumer harm, systemic issues
   - MEDIUM: Standard complaints requiring investigation
   - LOW: Minor issues or insufficient evidence

6. EVIDENCE_QUALITY: Assess the strength of evidence provided
   - Documentation quality
   - Witness statements
   - Financial impact

Format response as JSON:
{{
    "alleged_persons": [
        {{
            "name_english": "...",
            "name_chinese": "...",
            "agent_number": "...",
            "license_number": "...",
            "company": "...",
            "role": "agent/broker/company"
        }}
    ],
    "allegation_type": "...",
    "allegation_summary": "...",
    "detailed_reasoning": "Comprehensive analysis of evidence and regulatory implications...",
    "evidence_quality": "STRONG/MODERATE/WEAK",
    "investigation_priority": "HIGH/MEDIUM/LOW",
    "regulatory_impact": "...",
    "recommended_actions": ["action1", "action2", "action3"],
    "source_reliability": 4,
    "content_validity": 4,
    "confidence_score": 0.85,
    "attachment_analysis": "Summary of key findings from attachments",
    "consumer_harm_level": "HIGH/MEDIUM/LOW/NONE"
}}
</comprehensive_analysis_task>

<comprehensive_analysis>
"""
        """
        Analyze an email to extract alleged subjects and allegation details
        """
        prompt = self._create_analysis_prompt(email_data)
        
        try:
            # Call LLM for analysis using configured session
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "hosted_vllm/Qwen3-235B-A22B-GPTQ-Int4",
                    "prompt": prompt,
                    "max_tokens": 2000,  # Increased for better summaries
                    "temperature": 0.1,
                    "stop": ["</analysis>"]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('choices', [{}])[0].get('text', '')
                print(f"[DEBUG] LLM response: {analysis_text[:200]}...")
                parsed_result = self._parse_analysis_result(analysis_text)
                print(f"[DEBUG] Parsed analysis: {parsed_result}")
                return parsed_result
            else:
                print(f"LLM API error: {response.status_code} - {response.text}")
                return self._get_default_analysis()
                
        except Exception as e:
            print(f"[ERROR] Error calling LLM API: {e}")
            print(f"[DEBUG] Email data: {email_data}")
            return self._get_default_analysis()
    
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
            print(f"[DEBUG] Parsing comprehensive analysis: {analysis_text}")
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = analysis_text[start:end]
                print(f"[DEBUG] Extracted comprehensive JSON: {json_str}")
                result = json.loads(json_str)
                
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
                    'allegation_summary': result.get('allegation_summary', '')[:1000],
                    'detailed_reasoning': result.get('detailed_reasoning', '')[:5000],
                    'evidence_quality': result.get('evidence_quality', 'MODERATE'),
                    'investigation_priority': result.get('investigation_priority', 'MEDIUM'),
                    'regulatory_impact': result.get('regulatory_impact', '')[:1000],
                    'recommended_actions': result.get('recommended_actions', [])[:10],
                    'source_reliability': min(max(int(result.get('source_reliability', 3)), 1), 5),
                    'content_validity': min(max(int(result.get('content_validity', 3)), 1), 5),
                    'confidence_score': float(result.get('confidence_score', 0.5)),
                    'attachment_analysis': result.get('attachment_analysis', '')[:1000],
                    'consumer_harm_level': result.get('consumer_harm_level', 'LOW'),
                    'ai_analysis_completed': True,
                    'analysis_type': 'comprehensive'
                }
                print(f"[DEBUG] Successfully parsed comprehensive result")
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
            'detailed_reasoning': 'AI analysis could not be completed. Please review email and attachments manually.',
            'evidence_quality': 'UNKNOWN',
            'investigation_priority': 'MEDIUM',
            'regulatory_impact': 'Requires manual assessment',
            'recommended_actions': ['manual_review', 'verify_allegations'],
            'source_reliability': 3,
            'content_validity': 3,
            'confidence_score': 0.0,
            'attachment_analysis': 'Not available',
            'consumer_harm_level': 'UNKNOWN',
            'ai_analysis_completed': False,
            'analysis_type': 'comprehensive'
        }
    
    def find_similar_cases(self, email_text: str, limit: int = 5) -> List[Dict]:
        """
        Use embedding model to find similar cases
        """
        try:
            # Get embedding for current email using configured session
            response = self.session.post(
                f"{self.embedding_api}/embeddings",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "hosted_vllm/Dmeta",
                    "input": email_text[:1000]  # Limit text length
                }
            )
            
            if response.status_code == 200:
                embedding = response.json().get('data', [{}])[0].get('embedding', [])
                # Here you would compare with stored embeddings in your database
                # For now, return empty list
                return []
            else:
                print(f"Embedding API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error calling embedding API: {e}")
            return []
    
    def ai_summarize_email(self, email_data: Dict) -> Dict:
        """
        Use AI to comprehensively analyze email: summary, allegation nature, and alleged person
        """
        try:
            # Enhanced prompt for comprehensive analysis focusing on EMAIL BODY
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
            
            prompt = f"""You are analyzing an email for a professional investigation report. Focus on the EMAIL BODY CONTENT to understand what this email is really about.

EMAIL DETAILS:
Subject: {email_data.get('subject', 'N/A')}
From: {email_data.get('sender', 'N/A')}
To: {email_data.get('recipients', 'N/A')}

IMPORTANT - ANALYZE THIS EMAIL BODY CONTENT:
{clean_body}

INSTRUCTIONS:
1. READ THE EMAIL BODY CAREFULLY - ignore the subject line, focus on what the email content actually says
2. Determine what type of issue/complaint/inquiry this email is about based on the BODY content
3. Identify who is being complained about or investigated based on the BODY content
4. Create a professional summary based on what you read in the EMAIL BODY

Respond in JSON format:
{{
    "email_summary": "Professional 2-3 sentence summary based on EMAIL BODY content (not subject line)",
    "allegation_nature": "Specific allegation type based on EMAIL BODY (e.g., Cross-border Insurance Solicitation, Unlicensed Practice, Mis-selling, Fraud, Consumer Complaint, Inquiry, Investigation Request)",
    "alleged_person": "Name/company being complained about based on EMAIL BODY content",
    "email_type": "complaint/inquiry/response/follow-up/investigation",
    "confidence": "High/Medium/Low confidence in analysis"
}}

Analysis:"""
            
            print(f"[AI SUMMARIZE] Analyzing email body content for email {email_data.get('id', 'unknown')}...")
            print(f"[AI SUMMARIZE] Email body length: {len(email_body)} chars, clean body: {len(clean_body)} chars")
            
            response = self.session.post(
                f"{self.llm_api}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "hosted_vllm/Qwen3-235B-A22B-GPTQ-Int4",
                    "prompt": prompt,
                    "max_tokens": 1000,  # Increased for comprehensive body analysis
                    "temperature": 0.2,
                    "stop": ["Analysis:", "\n\n---"]
                },
                timeout=60  # Increased timeout for body analysis
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
                    "max_tokens": 6000,  # Increased for processing more emails
                    "temperature": 0.1,
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
You are an AI assistant for ULTRA-STRICT email title grouping. You MUST follow these rules EXACTLY.

EMAILS TO GROUP:
{emails_text}

**ULTRA-STRICT TITLE GROUPING RULES:**
1. **EXACT TITLE MATCH ONLY**: Group emails ONLY if they have the SAME core subject
2. **REMOVE PREFIXES**: Strip "Re:", "FW:", "Fwd:", "Forward:", "Reply:", "回复:", "转发:", "轉發:" etc.
3. **CORE SUBJECT MUST BE IDENTICAL**: After removing prefixes, the remaining text must be nearly identical
4. **NO CONTENT MIXING**: NEVER group different subjects even if they mention same person/topic
5. **NO ASSUMPTIONS**: If subjects look different, they ARE different - do NOT group them

**CRITICAL EXAMPLES:**
- "請發出1月對賬單" + "Re: 請發出1月對賬單" + "FW: 轉發：Re: 請發出1月對賬單" = SAME GROUP (same core: "請發出1月對賬單")
- "転介人举报" + "請發出1月對賬單" = DIFFERENT GROUPS (completely different subjects)
- "Billy Ng complaint" + "Billy Ng inquiry" = DIFFERENT GROUPS (different words: complaint vs inquiry)
- "Insurance case #123" + "Insurance case #456" = DIFFERENT GROUPS (different case numbers)

**WHAT SUBJECTS ARE THE SAME:**
✓ "Subject" + "Re: Subject" + "FW: Subject" = SAME
✓ "Title" + "Reply: Title" + "Forward: Title" = SAME  
✓ "问题" + "Re: 问题" + "转发: 问题" = SAME

**WHAT SUBJECTS ARE DIFFERENT:**
✗ "Subject A" + "Subject B" = DIFFERENT
✗ "问题1" + "问题2" = DIFFERENT
✗ "Billy complaint" + "Billy inquiry" = DIFFERENT
✗ "Case #1" + "Case #2" = DIFFERENT

**MANDATORY OUTPUT**: Return ONLY this exact JSON format:
{{
    "email_groups": [
        {{
            "group_id": "EXACT_001",
            "group_name": "Email Title: [EXACT CORE SUBJECT]",
            "group_type": "exact_title_match", 
            "email_ids": [list of IDs with same core subject],
            "core_subject": "[core subject after removing Re:/FW: prefixes]",
            "reasoning": "EXACT title match after removing prefixes"
        }}
    ],
    "ungrouped_emails": [IDs of emails with unique subjects],
    "grouping_summary": {{
        "total_emails": {len(email_summaries)},
        "total_groups": "number of groups created",
        "ungrouped_count": "number of unique emails",
        "grouping_method": "ultra_strict_title_only"
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
        """Enhanced fallback grouping - STRICT title-based threading only"""
        print("[AI GROUPING] Using strict title-based fallback grouping method")
        
        def clean_subject_for_ultra_strict_grouping(subject):
            """Clean subject for ULTRA-STRICT title matching - only group identical core subjects"""
            if not subject:
                return ""
            
            # Convert to lowercase for comparison
            clean = subject.lower().strip()
            
            # Remove common prefixes but be very careful about variations
            prefixes_to_remove = [
                're:', 'fw:', 'fwd:', 'forward:', 'reply:', 'ref:', 'r:', 'f:',
                '回复:', '回复：', '转发:', '转发：', '轉發:', '轉發：',
                'reply:', 'forward:', 'fwd:'
            ]
            
            # Keep removing prefixes until none are found
            original_clean = ""
            while clean != original_clean:
                original_clean = clean
                for prefix in prefixes_to_remove:
                    if clean.startswith(prefix):
                        clean = clean[len(prefix):].strip()
                        # Remove any leading colons or spaces
                        clean = clean.lstrip(':').strip()
                        break
                        
                # Remove email tags like [EXTERNAL], [Internal], etc.
                if clean.startswith('[') and ']' in clean:
                    tag_end = clean.find(']')
                    clean = clean[tag_end+1:].strip()
            
            # Normalize whitespace but preserve exact wording
            import re
            clean = re.sub(r'\s+', ' ', clean)
            return clean.strip()
        
        # Group ONLY by EXACT title matches - ultra strict
        title_groups = {}
        ungrouped = []
        
        print(f"[FALLBACK GROUPING] Using ULTRA-STRICT title matching for {len(emails)} emails")
        
        for email in emails:
            email_id = email.get('id')
            subject = email.get('subject', '')
            
            if not subject or len(subject.strip()) < 2:
                ungrouped.append(email_id)
                print(f"[FALLBACK] Email {email_id}: No subject or too short - ungrouped")
                continue
            
            # Get the core subject (without Re:/FW: prefixes)
            core_subject = clean_subject_for_ultra_strict_grouping(subject)
            
            if len(core_subject) < 2:  # Too short to be meaningful
                ungrouped.append(email_id)
                print(f"[FALLBACK] Email {email_id}: Core subject too short '{core_subject}' - ungrouped")
                continue
            
            # Debug logging
            print(f"[FALLBACK] Email {email_id}: '{subject}' -> core: '{core_subject}'")
            
            # Group by exact core subject match
            if core_subject not in title_groups:
                title_groups[core_subject] = {
                    'email_ids': [],
                    'original_subjects': [],
                    'has_replies': False
                }
            
            title_groups[core_subject]['email_ids'].append(email_id)
            title_groups[core_subject]['original_subjects'].append(subject)
            
            # Check if this is a reply/forward
            original_lower = subject.lower()
            if any(prefix in original_lower for prefix in ['re:', 'fw:', 'fwd:', 'reply', '回复', '转发', '轉發']):
                title_groups[core_subject]['has_replies'] = True
        
        # Convert to AI grouping format - only create groups with multiple emails OR clear reply chains
        email_groups = []
        group_counter = 1
        
        print(f"[FALLBACK] Found {len(title_groups)} unique core subjects")
        
        for core_subject, group_data in title_groups.items():
            email_count = len(group_data['email_ids'])
            print(f"[FALLBACK] Core subject '{core_subject}': {email_count} emails, has_replies: {group_data['has_replies']}")
            
            # Only create a group if:
            # 1. Multiple emails with same core subject, OR
            # 2. Has reply/forward patterns (even if just 1 email)
            if email_count > 1 or group_data['has_replies']:
                
                # Determine group type
                if group_data['has_replies']:
                    group_type = 'exact_reply_thread'
                    group_name = f'Email Thread: {core_subject[:60]}'
                else:
                    group_type = 'exact_title_match'
                    group_name = f'Same Title: {core_subject[:60]}'
                
                email_groups.append({
                    'group_id': f'EXACT_{group_counter:03d}',
                    'group_name': group_name,
                    'group_type': group_type,
                    'email_ids': group_data['email_ids'],
                    'core_subject': core_subject,
                    'title_pattern': f'{email_count} emails with identical core title',
                    'reasoning': f'EXACT title match: "{core_subject}"',
                    'original_subjects': group_data['original_subjects'][:5]  # Show first 5 examples
                })
                group_counter += 1
                print(f"[FALLBACK] Created group {group_counter-1}: '{group_name}' with {email_count} emails")
            else:
                # Single emails with no reply patterns go to ungrouped
                ungrouped.extend(group_data['email_ids'])
                print(f"[FALLBACK] Single email with core '{core_subject}' -> ungrouped")
        
        print(f"[FALLBACK] Final result: {len(email_groups)} groups, {len(ungrouped)} ungrouped emails")
        
        return {
            'email_groups': email_groups,
            'ungrouped_emails': ungrouped,
            'grouping_summary': {
                'total_emails': len(emails),
                'total_groups': len(email_groups),
                'ungrouped_count': len(ungrouped),
                'main_group_types': ['exact_reply_thread', 'exact_title_match'],
                'grouping_method': 'ultra_strict_title_only'
            },
            'ai_grouping_success': False,
            'fallback_method': 'ultra_strict_title_matching'
        }

    def process_attachment_with_docling(self, file_path: str) -> Dict:
        """
        Use Docling to extract text from email attachments
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                # Try multiple possible endpoints for Docling
                endpoints_to_try = [
                    f"{self.docling_api}/convert",
                    f"{self.docling_api}/api/convert", 
                    f"{self.docling_api}/v1/convert",
                    "https://ai-poc.corp.ia/docling/api/v1/convert"
                ]
                
                for endpoint in endpoints_to_try:
                    try:
                        response = self.session.post(
                            endpoint,
                            files=files,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            return {
                                'text_content': result.get('text', ''),
                                'metadata': result.get('metadata', {}),
                                'success': True,
                                'endpoint_used': endpoint
                            }
                    except:
                        continue
                
                # If all endpoints fail, return graceful fallback
                print(f"Docling API: All endpoints failed, using fallback text extraction")
                return {
                    'text_content': 'Docling service unavailable - manual document review required',
                    'metadata': {'error': 'Service unavailable'},
                    'success': False,
                    'endpoint_used': 'fallback'
                }
                
        except Exception as e:
            print(f"Error calling Docling API: {e}")
            return {'success': False, 'error': str(e)}

# Global AI instance
intelligence_ai = IntelligenceAI()

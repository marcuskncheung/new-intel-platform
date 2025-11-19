"""
Automated Alleged Person Profile Management System

This module automatically:
1. Creates profiles when AI analysis or manual input identifies alleged persons
2. Assigns unique POI (Person of Interest) IDs like POI-001, POI-002
3. Links profiles to emails alleging them  
4. Prevents duplicates using smart name matching
5. Updates profiles with new information
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from sqlalchemy import func, or_, and_
import difflib

def normalize_name_for_matching(name: str) -> str:
    """
    Normalize name for duplicate detection
    
    Examples:
    - "LEUNG SHEUNG MAN EMERSON" -> "leung sheung man emerson"
    - "梁尚文" -> "梁尚文" 
    - "Mr. John DOE Jr." -> "john doe"
    """
    if not name or not name.strip():
        return ""
    
    # Remove common titles and suffixes
    name = re.sub(r'\b(mr|mrs|ms|dr|prof|sr|jr|iii|ii)\b\.?', '', name, flags=re.IGNORECASE)
    
    # Remove extra whitespace and convert to lowercase for English
    # Keep Chinese characters as-is for exact matching
    cleaned = re.sub(r'\s+', ' ', name.strip())
    
    # Only lowercase if it contains Latin characters
    if re.search(r'[a-zA-Z]', cleaned):
        cleaned = cleaned.lower()
    
    return cleaned

def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two names (0.0 to 1.0)
    
    Uses different strategies:
    - Exact match for Chinese names (very strict)
    - Fuzzy matching for English names
    - Handles name variations and common misspellings
    - Excludes company names from matching personal names
    """
    if not name1 or not name2:
        return 0.0
    
    # ✅ CRITICAL FIX: Check if either name is a company name
    company_indicators = [
        'limited', 'ltd', 'llc', 'inc', 'corp', 'corporation',
        'company', 'co', 'group', 'holdings', 'international',
        '有限公司', '公司', '集團', '控股', '國際', '投資',
        'consultant', 'consulting', 'services', 'advisory',
        'financial', 'insurance', 'wealth', 'asset'
    ]
    
    name1_lower = name1.lower()
    name2_lower = name2.lower()
    
    is_company1 = any(indicator in name1_lower for indicator in company_indicators)
    is_company2 = any(indicator in name2_lower for indicator in company_indicators)
    
    # If one is a company name and the other isn't, they can't match
    if is_company1 != is_company2:
        print(f"[NAME MATCHING] Rejecting match: '{name1}' vs '{name2}' - one is company, one is person")
        return 0.0
        
    norm1 = normalize_name_for_matching(name1)
    norm2 = normalize_name_for_matching(name2)
    
    # Exact match - perfect score
    if norm1 == norm2:
        return 1.0
    
    # Check if both are Chinese names (contain Chinese characters)
    is_chinese1 = bool(re.search(r'[\u4e00-\u9fff]', norm1))
    is_chinese2 = bool(re.search(r'[\u4e00-\u9fff]', norm2))
    
    # Extract Chinese characters from both names
    chinese_chars1 = re.sub(r'[^\u4e00-\u9fff]', '', norm1)
    chinese_chars2 = re.sub(r'[^\u4e00-\u9fff]', '', norm2)
    
    if chinese_chars1 and chinese_chars2:
        # For Chinese names, use stricter exact character matching
        # Chinese names are typically 2-4 characters, so high precision needed
        if chinese_chars1 == chinese_chars2:
            # Exact Chinese match (ignore English suffix like "Spero")
            # Examples: "曹越" == "曹越spero" → 0.95 (same person, different romanization)
            return 0.95
        
        # Check if one Chinese name contains the other (partial match)
        # Example: "曹越" in "曹越峰" → 0.85 (could be same person with incomplete name)
        if chinese_chars1 in chinese_chars2:
            # Shorter name is subset of longer name
            ratio = len(chinese_chars1) / len(chinese_chars2)
            return 0.85 * ratio  # Penalize if difference is large
        elif chinese_chars2 in chinese_chars1:
            ratio = len(chinese_chars2) / len(chinese_chars1)
            return 0.85 * ratio
        
        # Character-by-character comparison for Chinese
        common_chars = set(chinese_chars1) & set(chinese_chars2)
        if common_chars:
            char_similarity = len(common_chars) / max(len(set(chinese_chars1)), len(set(chinese_chars2)))
            return char_similarity * 0.7  # Penalize partial matches
        
        return 0.0  # Different Chinese names
    
    # Use difflib for fuzzy matching (English names)
    similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    # Boost similarity for partial name matches
    # e.g., "John Smith" vs "John William Smith"
    # e.g., "Cao Yue" vs "Cao Yue Spero" → Should be 0.95 (same person!)
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if words1 and words2:
        common_words = words1.intersection(words2)
        word_similarity = len(common_words) / max(len(words1), len(words2))
        
        # 🔧 ENHANCED: If one name is a complete subset of the other, it's likely the same person
        # Example: {"cao", "yue"} ⊆ {"cao", "yue", "spero"} → 0.95 match
        # ✅ CRITICAL FIX: Require at least 2 words AND longer name ≤ 2x shorter name
        # This prevents "LEUNG" matching "LEUNG TAI LIN" or "LEUNG SOMETHING COMPANY LIMITED"
        if words1.issubset(words2) or words2.issubset(words1):
            shorter_words = min(len(words1), len(words2))
            longer_words = max(len(words1), len(words2))
            
            # Require at least 2 words in shorter name (avoid single-word false matches)
            # AND longer name can't be more than 2x the shorter name (avoid company names)
            if shorter_words >= 2 and longer_words <= shorter_words * 2:
                # One name is completely contained in the other
                # Return high score (0.95) if ALL words from shorter name are in longer name
                return 0.95
            else:
                # Too few words or too much length difference - treat as partial match
                return word_similarity * 0.75
        
        # Combine character and word similarity
        similarity = max(similarity, word_similarity * 0.85)
    
    return similarity

def generate_next_poi_id(db, AllegedPersonProfile) -> str:
    """
    Generate next sequential POI ID (POI-001, POI-002, etc.)
    
    Args:
        db: SQLAlchemy database instance from Flask app
        AllegedPersonProfile: AllegedPersonProfile model class
        
    Queries existing profiles to find the highest number and increment.
    Uses db and models passed from Flask route handlers with active app context.
    """
    try:
        # Query database using passed db instance - already has active Flask app context
        highest_poi = db.session.query(AllegedPersonProfile.poi_id).filter(
            AllegedPersonProfile.poi_id.like('POI-%')
        ).order_by(AllegedPersonProfile.poi_id.desc()).first()
        
        if highest_poi:
            poi_id_str = highest_poi[0]
            try:
                number_part = int(poi_id_str.split('-')[1])
                next_number = number_part + 1
                return f"POI-{next_number:03d}"
            except (IndexError, ValueError):
                pass
        
        total_count = AllegedPersonProfile.query.count()
        next_number = total_count + 1
        return f"POI-{next_number:03d}"
    
    except Exception as e:
        print(f"[POI ID GENERATION] Error: {e}")
        # Fallback to timestamp-based ID
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        return f"POI-{timestamp}"

def find_matching_profile(db, AllegedPersonProfile, 
                         name_english: str, name_chinese: str,
                         agent_number: str = None, company: str = None,
                         similarity_threshold: float = 0.80) -> Optional[Dict]:
    """
    Find existing profile that matches the given person details
    
    Args:
        db: SQLAlchemy database instance from Flask app
        AllegedPersonProfile: AllegedPersonProfile model class
        name_english: English name to match
        name_chinese: Chinese name to match
        agent_number: Optional agent/license number
        company: Optional company name
        similarity_threshold: Minimum similarity score (0.0-1.0)
                             Lowered to 0.80 to catch variations like "Cao Yue" vs "Cao Yue Spero"
        similarity_threshold: Minimum similarity score (0.0-1.0)
        
    Returns:
        Dict with profile info if match found, None otherwise
        
    Matching criteria (in order of priority):
    1. Exact agent number match (if provided)
    2. High similarity English + Chinese names 
    3. High similarity on either English OR Chinese name
    4. Company + name partial match
    """
    
    try:
        # Use passed models - already has active Flask app context from route handler
        # 1. Try exact agent number match first (most reliable)
        if agent_number and agent_number.strip():
            # 🔧 FIX: Exclude MERGED profiles to prevent recreating after merge
            exact_match = AllegedPersonProfile.query.filter(
                AllegedPersonProfile.agent_number == agent_number.strip(),
                AllegedPersonProfile.status != 'MERGED'
            ).first()
            
            if exact_match:
                print(f"[PROFILE MATCHING] ✅ Found exact agent number match: {exact_match.poi_id}")
                return exact_match.to_dict()
        
        # 2. Try name similarity matching
        if name_english or name_chinese:
            print(f"[PROFILE MATCHING] Searching for name similarity: EN='{name_english}' CN='{name_chinese}'")
            
            # 🔧 FIX: Exclude MERGED profiles to prevent recreating merged POIs after refresh
            # Get all profiles that are NOT merged (ACTIVE, INACTIVE, etc. are fine)
            all_profiles = AllegedPersonProfile.query.filter(
                AllegedPersonProfile.status != 'MERGED'
            ).all()
            
            best_match = None
            best_similarity = 0.0
            
            for profile in all_profiles:
                # Calculate similarity for English names
                eng_similarity = 0.0
                if name_english and profile.name_english:
                    eng_similarity = calculate_name_similarity(name_english, profile.name_english)
                
                # Calculate similarity for Chinese names
                chi_similarity = 0.0
                if name_chinese and profile.name_chinese:
                    chi_similarity = calculate_name_similarity(name_chinese, profile.name_chinese)
                
                # STRATEGY: If BOTH names are provided and match, it's very likely the same person
                if name_english and name_chinese and profile.name_english and profile.name_chinese:
                    # Both English and Chinese names provided - check if they match
                    # 🔧 CRITICAL FIX: REQUIRE BOTH names to match for dual-name comparison
                    # Example: "Peter Chan (陈伟)" vs "Peter Chan (张明)" should NOT match
                    # English matches but Chinese different = DIFFERENT PEOPLE!
                    if eng_similarity >= 0.80 and chi_similarity >= 0.80:
                        # Both names match well - definitely same person!
                        overall_similarity = 1.0
                        print(f"[PROFILE MATCHING] 🎯 Strong dual-name match: {profile.poi_id} - EN:{eng_similarity:.3f} CN:{chi_similarity:.3f}")
                    elif eng_similarity >= 0.95 and chi_similarity >= 0.50:
                        # English is near-perfect match, Chinese is partial - could be name variation
                        # Example: "Cao Yue (曹越)" vs "Cao Yue Spero (曹越)" → 0.95 match
                        overall_similarity = 0.90
                        print(f"[PROFILE MATCHING] 🤔 Partial dual-name match: {profile.poi_id} - EN:{eng_similarity:.3f} CN:{chi_similarity:.3f}")
                    else:
                        # 🚨 CRITICAL: If BOTH names provided but one doesn't match → Different people!
                        # Don't use the higher score, use the LOWER score to prevent false matches
                        overall_similarity = min(eng_similarity, chi_similarity)
                        if overall_similarity < similarity_threshold:
                            print(f"[PROFILE MATCHING] ❌ Different people (dual-name mismatch): {profile.poi_id} - EN:{eng_similarity:.3f} CN:{chi_similarity:.3f}")
                else:
                    # Only one name provided or profile has only one name
                    # Use the higher similarity score
                    overall_similarity = max(eng_similarity, chi_similarity)
                
                # Boost score if company also matches (additional confidence)
                if company and profile.company:
                    company_similarity = calculate_name_similarity(company, profile.company)
                    if company_similarity > 0.8:
                        overall_similarity = min(1.0, overall_similarity + 0.05)
                        print(f"[PROFILE MATCHING] 🏢 Company match boost: {profile.company}")
                
                if overall_similarity > best_similarity and overall_similarity >= similarity_threshold:
                    best_similarity = overall_similarity
                    best_match = profile
            
            if best_match:
                # 🚨 CRITICAL: Verify license number compatibility before confirming match
                # If new data has a license number that conflicts with existing profile, they are DIFFERENT entities
                if agent_number and agent_number.strip() and best_match.agent_number:
                    if agent_number.strip() != best_match.agent_number:
                        print(f"[PROFILE MATCHING] ⚠️ License number CONFLICT detected!")
                        print(f"[PROFILE MATCHING] ❌ Cannot match - Existing POI-{best_match.id} has license '{best_match.agent_number}' but new data has '{agent_number}'")
                        print(f"[PROFILE MATCHING] → These are DIFFERENT companies/persons despite similar names")
                        return None
                
                print(f"[PROFILE MATCHING] ✅ Found similarity match: {best_match.poi_id} (similarity: {best_similarity:.3f})")
                return best_match.to_dict()
        
        print("[PROFILE MATCHING] No matching profiles found")
        return None
        
    except Exception as e:
        print(f"[PROFILE MATCHING] Error finding matching profile: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_or_update_alleged_person_profile(
    db, AllegedPersonProfile, EmailAllegedPersonLink,
    name_english: str,
    name_chinese: str = "",
    agent_number: str = "",
    license_number: str = "",
    company: str = "",
    role: str = "",
    email_id: int = None,
    source: str = "AI_ANALYSIS",
    update_mode: str = "merge"  # "merge", "overwrite", "skip_if_exists"
) -> Dict:
    """
    Create new alleged person profile or update existing one
    
    Args:
        db: SQLAlchemy database instance from Flask app
        AllegedPersonProfile: AllegedPersonProfile model class
        EmailAllegedPersonLink: EmailAllegedPersonLink model class
        name_english: English name of alleged person
        name_chinese: Chinese name of alleged person  
        agent_number: Agent/license number if available
        license_number: License number if different from agent number
        company: Company/broker name
        role: Agent, Broker, etc.
        email_id: ID of email that mentioned this person
        source: How this profile was created (AI_ANALYSIS, MANUAL_INPUT, IMPORT)
        update_mode: How to handle existing profiles
        
    Returns:
        Dict with profile info and creation/update status
    """
    
    print(f"[ALLEGED PERSON AUTOMATION] Processing: {name_english} | {name_chinese}")
    print(f"[ALLEGED PERSON AUTOMATION] Agent: {agent_number} | Company: {company}")
    
    try:
        # 1. Check for existing profile
        existing_profile = find_matching_profile(
            db, AllegedPersonProfile,
            name_english=name_english,
            name_chinese=name_chinese,
            agent_number=agent_number,
            company=company
        )
        
        if existing_profile:
            poi_id = existing_profile.get('poi_id')
            profile_id = existing_profile.get('id')
            
            print(f"[ALLEGED PERSON AUTOMATION] ✅ Found existing profile: {poi_id}")
            
            if update_mode == "skip_if_exists":
                return {
                    'success': True,
                    'action': 'skipped',
                    'poi_id': poi_id,
                    'profile_id': profile_id,
                    'message': f'Profile {poi_id} already exists, skipped'
                }
            
            # 🔄 UPDATE LOGIC: Different behavior based on update_mode
            updated_fields = []
            profile = db.session.query(AllegedPersonProfile).get(profile_id)
            
            if not profile:
                print(f"[ALLEGED PERSON AUTOMATION] ❌ Profile {profile_id} not found in database")
                return {
                    'success': False,
                    'action': 'error',
                    'message': f'Profile {poi_id} not found in database'
                }
            
            # OVERWRITE MODE: Update names even if they exist (for manual corrections)
            if update_mode == "overwrite":
                if name_english and name_english.strip() != profile.name_english:
                    old_name = profile.name_english
                    profile.name_english = name_english.strip()
                    updated_fields.append('name_english')
                    print(f"[ALLEGED PERSON AUTOMATION] 📝 Updated English name: '{old_name}' → '{name_english}'")
                
                if name_chinese and name_chinese.strip() != profile.name_chinese:
                    old_name = profile.name_chinese
                    profile.name_chinese = name_chinese.strip()
                    updated_fields.append('name_chinese')
                    print(f"[ALLEGED PERSON AUTOMATION] 📝 Updated Chinese name: '{old_name}' → '{name_chinese}'")
            
            # MERGE MODE: Only add missing fields (don't overwrite existing)
            else:
                if name_english and not profile.name_english:
                    profile.name_english = name_english.strip()
                    updated_fields.append('name_english')
                    print(f"[ALLEGED PERSON AUTOMATION] 📝 Added English name: {name_english}")
                
                if name_chinese and not profile.name_chinese:
                    profile.name_chinese = name_chinese.strip()
                    updated_fields.append('name_chinese')
                    print(f"[ALLEGED PERSON AUTOMATION] 📝 Added Chinese name: {name_chinese}")
            
            # Agent/License number updates (same for both modes)
            if agent_number and not profile.agent_number:
                profile.agent_number = agent_number.strip()
                updated_fields.append('agent_number')
                print(f"[ALLEGED PERSON AUTOMATION] 📝 Added agent number: {agent_number}")
            elif agent_number and profile.agent_number and agent_number.strip() != profile.agent_number:
                # Agent number conflict - log warning but don't override
                print(f"[ALLEGED PERSON AUTOMATION] ⚠️ Agent number mismatch: existing '{profile.agent_number}' vs new '{agent_number}'")
            
            if license_number and not profile.license_number:
                profile.license_number = license_number.strip()
                updated_fields.append('license_number')
                print(f"[ALLEGED PERSON AUTOMATION] 📝 Added license number: {license_number}")
            elif license_number and profile.license_number and license_number.strip() != profile.license_number:
                # License number provided but different - update it (could be renewal/correction)
                old_license = profile.license_number
                profile.license_number = license_number.strip()
                updated_fields.append('license_number')
                print(f"[ALLEGED PERSON AUTOMATION] 📝 Updated license number: {old_license} → {license_number}")
            
            if company and not profile.company:
                profile.company = company.strip()
                updated_fields.append('company')
                print(f"[ALLEGED PERSON AUTOMATION] 📝 Added company: {company}")
            
            if role and not profile.role:
                profile.role = role.strip()
                updated_fields.append('role')
                print(f"[ALLEGED PERSON AUTOMATION] 📝 Added role: {role}")
            
            # Update last mentioned date
            profile.last_mentioned_date = datetime.now(timezone.utc)
            updated_fields.append('last_mentioned_date')
            
            # Update normalized name if names changed
            if 'name_english' in updated_fields or 'name_chinese' in updated_fields:
                name_parts = []
                if profile.name_english:
                    name_parts.append(normalize_name_for_matching(profile.name_english))
                if profile.name_chinese:
                    name_parts.append(normalize_name_for_matching(profile.name_chinese))
                profile.name_normalized = ' | '.join(name_parts)
                updated_fields.append('name_normalized')
            
            # Link email if provided and not already linked
            if email_id:
                existing_link = db.session.query(EmailAllegedPersonLink).filter_by(
                    email_id=email_id,
                    alleged_person_id=profile_id
                ).first()
                
                if not existing_link:
                    link_created = link_email_to_profile(db, EmailAllegedPersonLink, AllegedPersonProfile,
                                                         email_id, poi_id, profile_id)
                    if link_created:
                        profile.email_count = (profile.email_count or 0) + 1
                        updated_fields.append('email_count')
                        print(f"[ALLEGED PERSON AUTOMATION] 🔗 Linked email {email_id} to profile {poi_id}")
            
            # Commit changes
            if updated_fields:
                db.session.commit()
                print(f"[ALLEGED PERSON AUTOMATION] ✅ Updated profile {poi_id}: {', '.join(updated_fields)}")
            else:
                print(f"[ALLEGED PERSON AUTOMATION] ℹ️ No new information to update for {poi_id}")
            
            return {
                'success': True,
                'action': 'updated',
                'poi_id': poi_id,
                'profile_id': profile_id,
                'updated_fields': updated_fields,
                'message': f'Updated existing profile {poi_id} ({len(updated_fields)} fields)'
            }
        
        else:
            # 2. Create new profile
            new_poi_id = generate_next_poi_id(db, AllegedPersonProfile)
            
            print(f"[ALLEGED PERSON AUTOMATION] 🆕 Creating new profile: {new_poi_id}")
            
            # Create normalized name for duplicate detection
            name_parts = []
            if name_english:
                name_parts.append(normalize_name_for_matching(name_english))
            if name_chinese:
                name_parts.append(normalize_name_for_matching(name_chinese))
            normalized_name = ' | '.join(name_parts)
            
            # Create new profile in database
            # Flask app context already active from route handler
            new_profile = AllegedPersonProfile(
                poi_id=new_poi_id,
                name_english=name_english.strip() if name_english else None,
                name_chinese=name_chinese.strip() if name_chinese else None,
                name_normalized=normalized_name,
                agent_number=agent_number.strip() if agent_number else None,
                license_number=license_number.strip() if license_number else None,
                company=company.strip() if company else None,
                role=role.strip() if role else None,
                created_by=source,
                email_count=0,
                first_mentioned_date=datetime.now(timezone.utc) if email_id else None,
                last_mentioned_date=datetime.now(timezone.utc) if email_id else None,
                status='ACTIVE'
            )
            
            db.session.add(new_profile)
            db.session.flush()  # Get the ID without committing
            
            # Create email link if email_id provided
            if email_id:
                link_created = link_email_to_profile(db, EmailAllegedPersonLink, AllegedPersonProfile, 
                                                     email_id, new_poi_id, new_profile.id)
                if link_created:
                    new_profile.email_count = 1
            
            db.session.commit()
            
            return {
                'success': True,
                'action': 'created',
                'poi_id': new_poi_id,
                'profile_id': new_profile.id,
                'profile': new_profile.to_dict(),
                'message': f'Created new profile {new_poi_id}'
            }
            
    except Exception as e:
        print(f"[ALLEGED PERSON AUTOMATION] ❌ Error: {e}")
        return {
            'success': False,
            'action': 'error',
            'error': str(e),
            'message': 'Failed to process alleged person profile'
        }

def process_ai_analysis_results(db, AllegedPersonProfile, EmailAllegedPersonLink, 
                               analysis_result: Dict, email_id: int) -> List[Dict]:
    """
    Process AI analysis results and auto-create/update alleged person profiles
    
    This is called after AI analysis completes to automatically create profiles
    for any alleged persons identified.
    
    Args:
        db: SQLAlchemy database instance from Flask app
        AllegedPersonProfile: AllegedPersonProfile model class
        EmailAllegedPersonLink: EmailAllegedPersonLink model class
        analysis_result: Result from IntelligenceAI.analyze_allegation_email_comprehensive()
        email_id: ID of the email that was analyzed
        
    Returns:
        List of profile creation/update results
    """
    
    results = []
    
    try:
        alleged_persons = analysis_result.get('alleged_persons', [])
        
        print(f"[ALLEGED PERSON AUTOMATION] Processing {len(alleged_persons)} alleged persons from email {email_id}")
        
        for person in alleged_persons:
            name_english = person.get('name_english', '').strip()
            name_chinese = person.get('name_chinese', '').strip()
            agent_number = person.get('agent_number', '').strip()
            license_number = person.get('license_number', '').strip()
            company = person.get('company', '').strip() or person.get('agent_company_broker', '').strip()
            role = person.get('role', '').strip()
            
            # Skip if no meaningful identifying information
            if not name_english and not name_chinese and not agent_number:
                print(f"[ALLEGED PERSON AUTOMATION] ⚠️ Skipping person with insufficient info: {person}")
                continue
            
            # Create or update profile
            result = create_or_update_alleged_person_profile(
                db, AllegedPersonProfile, EmailAllegedPersonLink,
                name_english=name_english,
                name_chinese=name_chinese,
                agent_number=agent_number,
                license_number=license_number,
                company=company,
                role=role,
                email_id=email_id,
                source="AI_ANALYSIS"
            )
            
            results.append(result)
            
            if result.get('success'):
                poi_id = result.get('poi_id')
                action = result.get('action')
                print(f"[ALLEGED PERSON AUTOMATION] ✅ {action.upper()}: {poi_id} for {name_english or name_chinese}")
            else:
                print(f"[ALLEGED PERSON AUTOMATION] ❌ Failed to process: {name_english or name_chinese}")
        
        return results
        
    except Exception as e:
        print(f"[ALLEGED PERSON AUTOMATION] ❌ Error processing AI results: {e}")
        return [{'success': False, 'error': str(e)}]

def process_manual_input(db, AllegedPersonProfile, EmailAllegedPersonLink,
                        email_id: int, alleged_subject_english: str, 
                        alleged_subject_chinese: str = "", 
                        additional_info: Dict = None,
                        update_mode: str = "overwrite") -> List[Dict]:
    """
    Process manual input of alleged person information
    
    This is called when users manually input alleged person details
    in email forms or edit pages.
    
    Args:
        db: SQLAlchemy database instance from Flask app
        AllegedPersonProfile: AllegedPersonProfile model class
        EmailAllegedPersonLink: EmailAllegedPersonLink model class
        email_id: ID of the email
        alleged_subject_english: Manually entered English names (comma-separated)
        alleged_subject_chinese: Manually entered Chinese names (comma-separated)
        additional_info: Dict with agent_number, company, etc. if available
        update_mode: "merge", "overwrite", or "skip_if_exists" - default "overwrite" for manual edits
        
    Returns:
        List of profile creation/update results
    """
    
    results = []
    additional_info = additional_info or {}
    
    try:
        # Parse comma-separated names
        english_names = [name.strip() for name in alleged_subject_english.split(',') if name.strip()] if alleged_subject_english else []
        chinese_names = [name.strip() for name in alleged_subject_chinese.split(',') if name.strip()] if alleged_subject_chinese else []
        
        # Create pairs of English/Chinese names
        name_pairs = []
        
        # If we have both English and Chinese names, try to pair them up
        if english_names and chinese_names:
            for i, eng_name in enumerate(english_names):
                chi_name = chinese_names[i] if i < len(chinese_names) else ""
                name_pairs.append((eng_name, chi_name))
            
            # If there are extra Chinese names, add them as separate entries
            for i in range(len(english_names), len(chinese_names)):
                name_pairs.append(("", chinese_names[i]))
        
        # If only English or only Chinese names
        elif english_names:
            for eng_name in english_names:
                name_pairs.append((eng_name, ""))
        elif chinese_names:
            for chi_name in chinese_names:
                name_pairs.append(("", chi_name))
        
        if not name_pairs:
            print(f"[ALLEGED PERSON AUTOMATION] ⚠️ No valid names found in manual input for email {email_id}")
            return []
        
        print(f"[ALLEGED PERSON AUTOMATION] Processing {len(name_pairs)} name pairs from manual input")
        
        for name_english, name_chinese in name_pairs:
            result = create_or_update_alleged_person_profile(
                db, AllegedPersonProfile, EmailAllegedPersonLink,
                name_english=name_english,
                name_chinese=name_chinese,
                agent_number=additional_info.get('agent_number', ''),
                license_number=additional_info.get('license_number', ''),
                company=additional_info.get('company', ''),
                role=additional_info.get('role', ''),
                email_id=email_id,
                source="MANUAL_INPUT",
                update_mode=update_mode  # Pass through update mode from parameter
            )
            
            results.append(result)
        
        return results
        
    except Exception as e:
        print(f"[ALLEGED PERSON AUTOMATION] ❌ Error processing manual input: {e}")
        return [{'success': False, 'error': str(e)}]

def link_email_to_profile(db, EmailAllegedPersonLink, AllegedPersonProfile,
                         email_id: int, poi_id: str, profile_id: int = None) -> bool:
    """
    Create a link between an email and an alleged person profile
    
    Args:
        db: SQLAlchemy database instance from Flask app
        EmailAllegedPersonLink: EmailAllegedPersonLink model class
        AllegedPersonProfile: AllegedPersonProfile model class
        email_id: ID of the email
        poi_id: POI ID (e.g., POI-001)
        profile_id: Optional profile database ID
        
    This maintains the many-to-many relationship so we can:
    - See all emails alleging a specific person
    - See all alleged persons mentioned in a specific email
    """
    
    try:
        # Use passed models - Flask app context already active from route handler
        # Get profile ID if not provided
        if not profile_id:
            profile = AllegedPersonProfile.query.filter_by(poi_id=poi_id, status='ACTIVE').first()
            if not profile:
                print(f"[EMAIL-PROFILE LINKING] ❌ Profile {poi_id} not found")
                return False
            profile_id = profile.id
        
        # Check if link already exists
        existing_link = EmailAllegedPersonLink.query.filter_by(
            email_id=email_id,
            alleged_person_id=profile_id
        ).first()
        
        if existing_link:
            print(f"[EMAIL-PROFILE LINKING] ℹ️ Link already exists: email {email_id} to profile {poi_id}")
            return True
        
        # Create new link in old table (POI v1.0 - for backward compatibility)
        new_link = EmailAllegedPersonLink(
            email_id=email_id,
            alleged_person_id=profile_id,
            created_by='AUTOMATION',
            confidence=0.95  # High confidence for direct creation
        )
        
        db.session.add(new_link)
        
        # 🆕 POI v2.0: Also create link in universal poi_intelligence_link table
        try:
            # Import POIIntelligenceLink model dynamically to avoid circular imports
            from app1_production import POIIntelligenceLink, Email
            
            # Check if universal link already exists
            existing_universal_link = db.session.query(POIIntelligenceLink).filter_by(
                poi_id=poi_id,  # ✅ Use string POI ID ("POI-037")
                source_type='EMAIL',
                source_id=email_id
            ).first()
            
            if not existing_universal_link:
                # Get email to extract case info
                email = Email.query.get(email_id)
                
                # Create universal link
                universal_link = POIIntelligenceLink(
                    poi_id=poi_id,  # ✅ Use string POI ID ("POI-037")
                    source_type='EMAIL',
                    source_id=email_id,
                    case_profile_id=email.caseprofile_id if email else None,  # ✅ Use correct column name
                    confidence_score=0.95,
                    extraction_method='AUTOMATION'
                )
                db.session.add(universal_link)
                print(f"[POI v2.0] ✅ Created universal link: email {email_id} to POI {poi_id}")
        except Exception as e:
            print(f"[POI v2.0] ⚠️ Could not create universal link (may not be available yet): {e}")
            # Don't fail if POI v2.0 table doesn't exist yet
        
        # Update profile counters
        profile = AllegedPersonProfile.query.get(profile_id)
        if profile:
            profile.email_count = EmailAllegedPersonLink.query.filter_by(
                alleged_person_id=profile_id
            ).count() + 1  # +1 for the new link
            
            # Update mention dates
            if not profile.first_mentioned_date:
                profile.first_mentioned_date = datetime.now(timezone.utc)
            profile.last_mentioned_date = datetime.now(timezone.utc)
        
        # Commit the link creation and profile updates
        db.session.commit()
        
        print(f"[EMAIL-PROFILE LINKING] ✅ Created link: email {email_id} to profile {poi_id}")
        return True
        
    except Exception as e:
        print(f"[EMAIL-PROFILE LINKING] ❌ Error linking email {email_id} to {poi_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_emails_for_poi(poi_id: str) -> List[Dict]:
    """
    Get all emails that mention a specific POI
    
    Used for the profile detail page to show related emails
    """
    
    try:
        # This would query the EmailAllegedPersonLink table
        # and return email details
        
        # For now, return empty list
        return []
        
    except Exception as e:
        print(f"[POI EMAIL QUERY] ❌ Error getting emails for {poi_id}: {e}")
        return []

def get_profile_statistics() -> Dict:
    """
    Get statistics about alleged person profiles
    
    Used for dashboard and reporting
    """
    
    try:
        # This would query the AllegedPersonProfile table
        # and return counts, recent activity, etc.
        
        return {
            'total_profiles': 0,
            'profiles_with_agent_numbers': 0,
            'profiles_created_today': 0,
            'profiles_created_this_week': 0,
            'most_recent_poi_id': 'POI-001'
        }
        
    except Exception as e:
        print(f"[PROFILE STATISTICS] ❌ Error getting statistics: {e}")
        return {}

# Test functions for development
if __name__ == "__main__":
    print("🧪 Testing Alleged Person Automation System")
    
    # Test name normalization
    test_names = [
        "LEUNG SHEUNG MAN EMERSON",
        "梁尚文", 
        "Mr. John DOE Jr.",
        "李明華 LEE MING WAH"
    ]
    
    print("\n📝 Name Normalization Tests:")
    for name in test_names:
        normalized = normalize_name_for_matching(name)
        print(f"   '{name}' → '{normalized}'")
    
    # Test similarity calculation
    print("\n🔍 Name Similarity Tests:")
    test_pairs = [
        ("John Smith", "John William Smith"),
        ("LEUNG SHEUNG MAN", "Leung Sheung Man Emerson"),
        ("李明華", "李明华"),
        ("ABC Insurance", "ABC Life Insurance")
    ]
    
    for name1, name2 in test_pairs:
        similarity = calculate_name_similarity(name1, name2)
        print(f"   '{name1}' vs '{name2}' = {similarity:.3f}")
    
    # Test POI ID generation
    print(f"\n🆔 Next POI ID: {generate_next_poi_id()}")
    
    # Test profile creation simulation
    print("\n🎯 Profile Creation Test:")
    result = create_or_update_alleged_person_profile(
        name_english="LEUNG SHEUNG MAN EMERSON",
        name_chinese="梁尚文",
        agent_number="AG123456",
        company="Prudential Hong Kong Limited",
        role="Agent",
        email_id=1,
        source="AI_ANALYSIS"
    )
    
    print(f"   Result: {result}")

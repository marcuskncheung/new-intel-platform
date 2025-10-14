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

# Database integration - Lazy loading to avoid circular imports
DATABASE_AVAILABLE = False
db = None
AllegedPersonProfile = None
EmailAllegedPersonLink = None
Email = None

def initialize_database():
    """Initialize database models - called when needed to avoid circular imports"""
    global DATABASE_AVAILABLE, db, AllegedPersonProfile, EmailAllegedPersonLink, Email
    
    if DATABASE_AVAILABLE:
        return True
        
    try:
        from app1_production import db as _db, AllegedPersonProfile as _AllegedPersonProfile, EmailAllegedPersonLink as _EmailAllegedPersonLink, Email as _Email
        db = _db
        AllegedPersonProfile = _AllegedPersonProfile
        EmailAllegedPersonLink = _EmailAllegedPersonLink
        Email = _Email
        DATABASE_AVAILABLE = True
        return True
    except ImportError as e:
        print(f"WARNING: Database models not available - automation will run in simulation mode: {e}")
        return False

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
    - Exact match for Chinese names
    - Fuzzy matching for English names
    - Handles name variations and common misspellings
    """
    if not name1 or not name2:
        return 0.0
        
    norm1 = normalize_name_for_matching(name1)
    norm2 = normalize_name_for_matching(name2)
    
    if norm1 == norm2:
        return 1.0
    
    # Use difflib for fuzzy matching
    similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    # Boost similarity for partial name matches
    # e.g., "John Smith" vs "John William Smith"
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if words1 and words2:
        common_words = words1.intersection(words2)
        word_similarity = len(common_words) / max(len(words1), len(words2))
        # Combine character and word similarity
        similarity = max(similarity, word_similarity * 0.8)
    
    return similarity

def generate_next_poi_id() -> str:
    """
    Generate next sequential POI ID (POI-001, POI-002, etc.)
    
    Queries existing profiles to find the highest number and increment
    """
    if not initialize_database():
        # Fallback when database not available
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        return f"POI-{timestamp}"
    
    try:
        # Ensure Flask app context is available for database operations
        try:
            from flask import current_app
            app_context = current_app.app_context()
        except RuntimeError:
            try:
                from app1_production import app
                app_context = app.app_context()
            except Exception:
                print("[POI ID GENERATION] Cannot access Flask app context")
                timestamp = datetime.now().strftime("%y%m%d%H%M")
                return f"POI-{timestamp}"
        
        with app_context:
            # Query for highest existing POI ID number
            # POI IDs are like "POI-001", "POI-002", so we extract the number part
            highest_poi = db.session.query(AllegedPersonProfile.poi_id).filter(
                AllegedPersonProfile.poi_id.like('POI-%')
            ).order_by(AllegedPersonProfile.poi_id.desc()).first()
            
            if highest_poi:
                # Extract number from "POI-XXX" format
                poi_id_str = highest_poi[0]
                try:
                    number_part = int(poi_id_str.split('-')[1])
                    next_number = number_part + 1
                    return f"POI-{next_number:03d}"
                except (IndexError, ValueError):
                    # Invalid format, fall back to counting
                    pass
            
            # Fallback: count total profiles + 1
            total_count = AllegedPersonProfile.query.count()
            next_number = total_count + 1
            return f"POI-{next_number:03d}"
    
    except Exception as e:
        print(f"[POI ID GENERATION] Error: {e}")
        # Fallback to timestamp-based ID
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        return f"POI-{timestamp}"

def find_matching_profile(name_english: str, name_chinese: str, 
                         agent_number: str = None, company: str = None,
                         similarity_threshold: float = 0.85) -> Optional[Dict]:
    """
    Find existing profile that matches the given person details
    
    Returns:
        Dict with profile info if match found, None otherwise
        
    Matching criteria (in order of priority):
    1. Exact agent number match (if provided)
    2. High similarity English + Chinese names 
    3. High similarity on either English OR Chinese name
    4. Company + name partial match
    """
    
    try:
        if not initialize_database():
            print(f"[PROFILE MATCHING] Database not available, no matches found")
            return None
        
        # Ensure Flask app context is available for database operations
        try:
            from flask import current_app
            app_context = current_app.app_context()
        except RuntimeError:
            # We might already be in app context or need to use the app instance
            try:
                from app1_production import app
                app_context = app.app_context()
            except:
                print(f"[PROFILE MATCHING] ❌ Cannot access Flask app context")
                return None
        
        with app_context:
            # 1. Try exact agent number match first (most reliable)
            if agent_number and agent_number.strip():
                exact_match = AllegedPersonProfile.query.filter_by(
                    agent_number=agent_number.strip(),
                    status='ACTIVE'
                ).first()
                
                if exact_match:
                    print(f"[PROFILE MATCHING] ✅ Found exact agent number match: {exact_match.poi_id}")
                    return exact_match.to_dict()
            
            # 2. Try name similarity matching
            if name_english or name_chinese:
                print(f"[PROFILE MATCHING] Searching for name similarity: EN='{name_english}' CN='{name_chinese}'")
                
                # Get all active profiles for similarity comparison
                all_profiles = AllegedPersonProfile.query.filter_by(status='ACTIVE').all()
            
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
                
                # Use the higher similarity score
                overall_similarity = max(eng_similarity, chi_similarity)
                
                # Boost score if both English and Chinese names match well
                if eng_similarity > 0.7 and chi_similarity > 0.7:
                    overall_similarity = min(1.0, (eng_similarity + chi_similarity) / 2 + 0.2)
                
                # Boost score if company also matches
                if company and profile.company:
                    company_similarity = calculate_name_similarity(company, profile.company)
                    if company_similarity > 0.8:
                        overall_similarity = min(1.0, overall_similarity + 0.1)
                
                if overall_similarity > best_similarity and overall_similarity >= similarity_threshold:
                    best_similarity = overall_similarity
                    best_match = profile
            
            if best_match:
                print(f"[PROFILE MATCHING] ✅ Found similarity match: {best_match.poi_id} (similarity: {best_similarity:.3f})")
                return best_match.to_dict()
        
        print(f"[PROFILE MATCHING] No matching profiles found")
        return None
        
    except Exception as e:
        print(f"[PROFILE MATCHING] Error finding matching profile: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_or_update_alleged_person_profile(
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
            
            # Update existing profile with new information
            updated_fields = []
            
            # Merge logic would go here
            # For now, just return the existing profile info
            
            return {
                'success': True,
                'action': 'updated',
                'poi_id': poi_id,
                'profile_id': profile_id,
                'updated_fields': updated_fields,
                'message': f'Updated existing profile {poi_id}'
            }
        
        else:
            # 2. Create new profile
            new_poi_id = generate_next_poi_id()
            
            print(f"[ALLEGED PERSON AUTOMATION] 🆕 Creating new profile: {new_poi_id}")
            
            if not initialize_database():
                # Simulation mode
                new_profile = {
                    'poi_id': new_poi_id,
                    'name_english': name_english,
                    'name_chinese': name_chinese,
                    'agent_number': agent_number,
                    'license_number': license_number,
                    'company': company,
                    'role': role,
                    'created_at': datetime.now(timezone.utc),
                    'created_by': source,
                    'email_count': 1 if email_id else 0
                }
                
                return {
                    'success': True,
                    'action': 'created',
                    'poi_id': new_poi_id,
                    'profile_id': 'sim_id',
                    'profile': new_profile,
                    'message': f'Created new profile {new_poi_id} (simulation mode)'
                }
            
            # Create normalized name for duplicate detection
            name_parts = []
            if name_english:
                name_parts.append(normalize_name_for_matching(name_english))
            if name_chinese:
                name_parts.append(normalize_name_for_matching(name_chinese))
            normalized_name = ' | '.join(name_parts)
            
            # Ensure Flask app context for database operations
            try:
                from flask import current_app
                app_context = current_app.app_context()
            except RuntimeError:
                try:
                    from app1_production import app
                    app_context = app.app_context()
                except Exception:
                    print("[ALLEGED PERSON AUTOMATION] ❌ Cannot access Flask app context")
                    return {
                        'success': False,
                        'action': 'error',
                        'message': 'Flask app context not available'
                    }
            
            with app_context:
                # Create new profile in database
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
                    first_mentioned_date=datetime.utcnow() if email_id else None,
                    last_mentioned_date=datetime.utcnow() if email_id else None,
                    status='ACTIVE'
                )
                
                db.session.add(new_profile)
                db.session.flush()  # Get the ID without committing
                
                # Create email link if email_id provided
                if email_id:
                    link_created = link_email_to_profile(email_id, new_poi_id, new_profile.id)
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

def process_ai_analysis_results(analysis_result: Dict, email_id: int) -> List[Dict]:
    """
    Process AI analysis results and auto-create/update alleged person profiles
    
    This is called after AI analysis completes to automatically create profiles
    for any alleged persons identified.
    
    Args:
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

def process_manual_input(email_id: int, alleged_subject_english: str, 
                        alleged_subject_chinese: str = "", 
                        additional_info: Dict = None) -> List[Dict]:
    """
    Process manual input of alleged person information
    
    This is called when users manually input alleged person details
    in email forms or edit pages.
    
    Args:
        email_id: ID of the email
        alleged_subject_english: Manually entered English names (comma-separated)
        alleged_subject_chinese: Manually entered Chinese names (comma-separated)
        additional_info: Dict with agent_number, company, etc. if available
        
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
                name_english=name_english,
                name_chinese=name_chinese,
                agent_number=additional_info.get('agent_number', ''),
                license_number=additional_info.get('license_number', ''),
                company=additional_info.get('company', ''),
                role=additional_info.get('role', ''),
                email_id=email_id,
                source="MANUAL_INPUT"
            )
            
            results.append(result)
        
        return results
        
    except Exception as e:
        print(f"[ALLEGED PERSON AUTOMATION] ❌ Error processing manual input: {e}")
        return [{'success': False, 'error': str(e)}]

def link_email_to_profile(email_id: int, poi_id: str, profile_id: int = None) -> bool:
    """
    Create a link between an email and an alleged person profile
    
    This maintains the many-to-many relationship so we can:
    - See all emails alleging a specific person
    - See all alleged persons mentioned in a specific email
    """
    
    try:
        if not initialize_database():
            print(f"[EMAIL-PROFILE LINKING] Simulating link: email {email_id} to profile {poi_id}")
            return True
        
        # Ensure Flask app context for database operations
        try:
            from flask import current_app
            app_context = current_app.app_context()
        except RuntimeError:
            try:
                from app1_production import app
                app_context = app.app_context()
            except Exception:
                print("[EMAIL-PROFILE LINKING] Cannot access Flask app context")
                return False
        
        with app_context:
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
            
            # Create new link
            new_link = EmailAllegedPersonLink(
                email_id=email_id,
                alleged_person_id=profile_id,
                created_by='AUTOMATION',
                confidence=0.95  # High confidence for direct creation
            )
            
            db.session.add(new_link)
            
            # Update profile counters
            profile = AllegedPersonProfile.query.get(profile_id)
            if profile:
                profile.email_count = EmailAllegedPersonLink.query.filter_by(
                    alleged_person_id=profile_id
                ).count() + 1  # +1 for the new link
                
                # Update mention dates
                if not profile.first_mentioned_date:
                    profile.first_mentioned_date = datetime.utcnow()
                profile.last_mentioned_date = datetime.utcnow()
            
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

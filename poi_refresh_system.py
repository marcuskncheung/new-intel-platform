"""
POI Profile Refresh/Update System

Purpose: Rescan all intelligence sources and update POI profiles with latest information
Date: 2025-01-17

Features:
1. Scan Email assessments for alleged persons
2. Scan WhatsApp entries for alleged persons
3. Scan Online Patrol entries for alleged persons  
4. Scan Surveillance targets
5. Update POI profiles with latest information
6. Create missing POI links
"""

def refresh_poi_from_all_sources(db, AllegedPersonProfile, EmailAllegedPersonLink, POIIntelligenceLink, Email, WhatsAppEntry, OnlinePatrolEntry, SurveillanceEntry, Target):
    """
    Rescan all intelligence sources and update POI profiles
    
    This function:
    - Finds all alleged persons across all sources
    - Creates/updates POI profiles
    - Creates universal links in poi_intelligence_link table
    - Updates statistics and counts
    """
    from alleged_person_automation import create_or_update_alleged_person_profile
    import re
    
    results = {
        'email': {'scanned': 0, 'profiles_created': 0, 'profiles_updated': 0, 'links_created': 0},
        'whatsapp': {'scanned': 0, 'profiles_created': 0, 'profiles_updated': 0, 'links_created': 0},
        'patrol': {'scanned': 0, 'profiles_created': 0, 'profiles_updated': 0, 'links_created': 0},
        'surveillance': {'scanned': 0, 'profiles_created': 0, 'profiles_updated': 0, 'links_created': 0}
    }
    
    print("[POI REFRESH] 🔄 Starting comprehensive POI profile refresh...")
    
    try:
        # ====================================================================
        # SCAN EMAILS
        # ====================================================================
        print("\n[1/4] Scanning Email assessments...")
        emails = db.session.query(Email).filter(
            (Email.alleged_subject_english.isnot(None)) | 
            (Email.alleged_subject_chinese.isnot(None))
        ).all()
        
        results['email']['scanned'] = len(emails)
        
        for email in emails:
            english_names = [n.strip() for n in (email.alleged_subject_english or '').split(',') if n.strip()]
            chinese_names = [n.strip() for n in (email.alleged_subject_chinese or '').split(',') if n.strip()]
            
            max_len = max(len(english_names), len(chinese_names))
            
            for i in range(max_len):
                eng_name = english_names[i] if i < len(english_names) else None
                chi_name = chinese_names[i] if i < len(chinese_names) else None
                
                if not eng_name and not chi_name:
                    continue
                
                result = create_or_update_alleged_person_profile(
                    db, AllegedPersonProfile, EmailAllegedPersonLink,
                    name_english=eng_name,
                    name_chinese=chi_name,
                    email_id=email.id,
                    source="EMAIL",
                    update_mode="merge"
                )
                
                if result.get('action') == 'created':
                    results['email']['profiles_created'] += 1
                elif result.get('action') == 'updated':
                    results['email']['profiles_updated'] += 1
                
                # Create universal link
                if result.get('poi_id'):
                    existing_link = db.session.query(POIIntelligenceLink).filter_by(
                        poi_id=result['poi_id'],
                        source_type='EMAIL',
                        source_id=email.id
                    ).first()
                    
                    if not existing_link:
                        new_link = POIIntelligenceLink(
                            poi_id=result['poi_id'],
                            source_type='EMAIL',
                            source_id=email.id,
                            case_profile_id=email.caseprofile_id,
                            confidence_score=0.95,
                            extraction_method='REFRESH'
                        )
                        db.session.add(new_link)
                        results['email']['links_created'] += 1
        
        db.session.commit()
        print(f"  ✅ Emails: {results['email']['scanned']} scanned, {results['email']['profiles_created']} created, {results['email']['profiles_updated']} updated, {results['email']['links_created']} links")
        
        # ====================================================================
        # SCAN WHATSAPP
        # ====================================================================
        print("\n[2/4] Scanning WhatsApp entries...")
        whatsapp_entries = db.session.query(WhatsAppEntry).filter(
            WhatsAppEntry.alleged_person.isnot(None)
        ).all()
        
        results['whatsapp']['scanned'] = len(whatsapp_entries)
        
        for entry in whatsapp_entries:
            alleged_persons = [p.strip() for p in (entry.alleged_person or '').split(',') if p.strip()]
            
            for person_name in alleged_persons:
                is_chinese = bool(re.search(r'[\u4e00-\u9fff]', person_name))
                
                result = create_or_update_alleged_person_profile(
                    db, AllegedPersonProfile, EmailAllegedPersonLink,
                    name_english=None if is_chinese else person_name,
                    name_chinese=person_name if is_chinese else None,
                    email_id=None,
                    source="WHATSAPP",
                    update_mode="merge"
                )
                
                if result.get('action') == 'created':
                    results['whatsapp']['profiles_created'] += 1
                elif result.get('action') == 'updated':
                    results['whatsapp']['profiles_updated'] += 1
                
                # Create universal link
                if result.get('poi_id'):
                    existing_link = db.session.query(POIIntelligenceLink).filter_by(
                        poi_id=result['poi_id'],
                        source_type='WHATSAPP',
                        source_id=entry.id
                    ).first()
                    
                    if not existing_link:
                        new_link = POIIntelligenceLink(
                            poi_id=result['poi_id'],
                            source_type='WHATSAPP',
                            source_id=entry.id,
                            case_profile_id=entry.caseprofile_id,
                            confidence_score=0.90,
                            extraction_method='REFRESH'
                        )
                        db.session.add(new_link)
                        results['whatsapp']['links_created'] += 1
        
        db.session.commit()
        print(f"  ✅ WhatsApp: {results['whatsapp']['scanned']} scanned, {results['whatsapp']['profiles_created']} created, {results['whatsapp']['profiles_updated']} updated, {results['whatsapp']['links_created']} links")
        
        # ====================================================================
        # SCAN PATROL
        # ====================================================================
        print("\n[3/4] Scanning Online Patrol entries...")
        patrol_entries = db.session.query(OnlinePatrolEntry).filter(
            OnlinePatrolEntry.alleged_person.isnot(None)
        ).all()
        
        results['patrol']['scanned'] = len(patrol_entries)
        
        for entry in patrol_entries:
            alleged_persons = [p.strip() for p in (entry.alleged_person or '').split(',') if p.strip()]
            
            for person_name in alleged_persons:
                is_chinese = bool(re.search(r'[\u4e00-\u9fff]', person_name))
                
                result = create_or_update_alleged_person_profile(
                    db, AllegedPersonProfile, EmailAllegedPersonLink,
                    name_english=None if is_chinese else person_name,
                    name_chinese=person_name if is_chinese else None,
                    email_id=None,
                    source="PATROL",
                    update_mode="merge"
                )
                
                if result.get('action') == 'created':
                    results['patrol']['profiles_created'] += 1
                elif result.get('action') == 'updated':
                    results['patrol']['profiles_updated'] += 1
                
                # Create universal link
                if result.get('poi_id'):
                    existing_link = db.session.query(POIIntelligenceLink).filter_by(
                        poi_id=result['poi_id'],
                        source_type='PATROL',
                        source_id=entry.id
                    ).first()
                    
                    if not existing_link:
                        new_link = POIIntelligenceLink(
                            poi_id=result['poi_id'],
                            source_type='PATROL',
                            source_id=entry.id,
                            case_profile_id=entry.caseprofile_id,
                            confidence_score=0.90,
                            extraction_method='REFRESH'
                        )
                        db.session.add(new_link)
                        results['patrol']['links_created'] += 1
        
        db.session.commit()
        print(f"  ✅ Patrol: {results['patrol']['scanned']} scanned, {results['patrol']['profiles_created']} created, {results['patrol']['profiles_updated']} updated, {results['patrol']['links_created']} links")
        
        # ====================================================================
        # SCAN SURVEILLANCE
        # ====================================================================
        print("\n[4/4] Scanning Surveillance targets...")
        targets = db.session.query(Target).all()
        
        results['surveillance']['scanned'] = len(targets)
        
        for target in targets:
            if not target.name:
                continue
            
            is_chinese = bool(re.search(r'[\u4e00-\u9fff]', target.name))
            
            # Prepare additional info
            additional_info = {}
            if target.license_number:
                additional_info['license_number'] = target.license_number
                additional_info['agent_number'] = target.license_number
            if target.license_type:
                additional_info['role'] = target.license_type
            
            result = create_or_update_alleged_person_profile(
                db, AllegedPersonProfile, EmailAllegedPersonLink,
                name_english=None if is_chinese else target.name,
                name_chinese=target.name if is_chinese else None,
                email_id=None,
                source="SURVEILLANCE",
                update_mode="merge",
                additional_info=additional_info
            )
            
            if result.get('action') == 'created':
                results['surveillance']['profiles_created'] += 1
            elif result.get('action') == 'updated':
                results['surveillance']['profiles_updated'] += 1
            
            # Create universal link
            if result.get('poi_id'):
                existing_link = db.session.query(POIIntelligenceLink).filter_by(
                    poi_id=result['poi_id'],
                    source_type='SURVEILLANCE',
                    source_id=target.surveillance_entry_id
                ).first()
                
                if not existing_link:
                    new_link = POIIntelligenceLink(
                        poi_id=result['poi_id'],
                        source_type='SURVEILLANCE',
                        source_id=target.surveillance_entry_id,
                        case_profile_id=None,
                        confidence_score=0.95,
                        extraction_method='REFRESH'
                    )
                    db.session.add(new_link)
                    results['surveillance']['links_created'] += 1
        
        db.session.commit()
        print(f"  ✅ Surveillance: {results['surveillance']['scanned']} scanned, {results['surveillance']['profiles_created']} created, {results['surveillance']['profiles_updated']} updated, {results['surveillance']['links_created']} links")
        
        # ====================================================================
        # SUMMARY
        # ====================================================================
        total_scanned = sum(r['scanned'] for r in results.values())
        total_created = sum(r['profiles_created'] for r in results.values())
        total_updated = sum(r['profiles_updated'] for r in results.values())
        total_links = sum(r['links_created'] for r in results.values())
        
        print("\n" + "=" * 80)
        print("✅ POI PROFILE REFRESH COMPLETED")
        print("=" * 80)
        print(f"Total Records Scanned: {total_scanned}")
        print(f"POI Profiles Created: {total_created}")
        print(f"POI Profiles Updated: {total_updated}")
        print(f"Universal Links Created: {total_links}")
        print("=" * 80)
        
        return {
            'success': True,
            'results': results,
            'summary': {
                'total_scanned': total_scanned,
                'total_created': total_created,
                'total_updated': total_updated,
                'total_links': total_links
            }
        }
        
    except Exception as e:
        print(f"\n❌ ERROR during POI refresh: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return {
            'success': False,
            'error': str(e),
            'results': results
        }

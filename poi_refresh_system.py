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
            # 🔄 CRITICAL FIX: Remove ALL old POI links for this email first
            # This ensures we sync with current assessment details, not stale data
            print(f"[POI REFRESH] 🧹 Syncing EMAIL-{email.id} with current assessment details")
            
            # Delete old POIIntelligenceLink entries
            old_universal_links = db.session.query(POIIntelligenceLink).filter_by(
                source_type='EMAIL',
                source_id=email.id
            ).all()
            for old_link in old_universal_links:
                print(f"[POI REFRESH] 🗑️ Removing old link: {old_link.poi_id} → EMAIL-{email.id}")
                db.session.delete(old_link)
            
            # Delete old EmailAllegedPersonLink entries (POI v1.0)
            old_email_links = db.session.query(EmailAllegedPersonLink).filter_by(
                email_id=email.id
            ).all()
            for old_link in old_email_links:
                profile = db.session.query(AllegedPersonProfile).get(old_link.alleged_person_id)
                poi_id = profile.poi_id if profile else "UNKNOWN"
                print(f"[POI REFRESH] 🗑️ Removing old legacy link: {poi_id} → EMAIL-{email.id}")
                db.session.delete(old_link)
            
            db.session.flush()  # Apply deletions before creating new links
            
            # Now create fresh links based on CURRENT assessment details
            english_names = [n.strip() for n in (email.alleged_subject_english or '').split(',') if n.strip()]
            chinese_names = [n.strip() for n in (email.alleged_subject_chinese or '').split(',') if n.strip()]
            
            max_len = max(len(english_names), len(chinese_names))
            
            for i in range(max_len):
                eng_name = english_names[i] if i < len(english_names) else None
                chi_name = chinese_names[i] if i < len(chinese_names) else None
                
                if not eng_name and not chi_name:
                    continue
                
                # 🔧 CRITICAL FIX: Don't pass email_id to avoid wrong linking!
                # The refresh should only create/find POI profiles, not link them.
                # Links are created separately via POIIntelligenceLink below.
                result = create_or_update_alleged_person_profile(
                    db, AllegedPersonProfile, EmailAllegedPersonLink,
                    name_english=eng_name,
                    name_chinese=chi_name,
                    email_id=None,  # ✅ DON'T link during refresh! Links created separately below
                    source="EMAIL",
                    update_mode="merge"  # Merge mode: only add missing fields, don't overwrite
                )
                
                if result.get('action') == 'created':
                    results['email']['profiles_created'] += 1
                elif result.get('action') == 'updated':
                    results['email']['profiles_updated'] += 1
                
                # 🔧 FIX: Create universal link ALWAYS (even if no case_profile_id)
                # This ensures POI profiles show their source in the dashboard
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
                            case_profile_id=email.caseprofile_id if email.caseprofile_id else None,
                            confidence_score=0.95,
                            extraction_method='REFRESH'
                        )
                        db.session.add(new_link)
                        results['email']['links_created'] += 1
                        print(f"[POI REFRESH] 🔗 Created source link: {result['poi_id']} ← EMAIL-{email.id}")
            
            # 🔧 FIX: Commit after processing EACH email to ensure POI profiles are visible
            # This prevents creating duplicate POIs when the same name appears in multiple emails
            db.session.commit()
            
            print(f"[POI REFRESH] ✅ EMAIL-{email.id} synced: {max_len} POI link(s) created based on current assessment")
        
        print(f"  ✅ Emails: {results['email']['scanned']} scanned, {results['email']['profiles_created']} created, {results['email']['profiles_updated']} updated, {results['email']['links_created']} links")
        
        # ====================================================================
        # SCAN WHATSAPP
        # ====================================================================
        print("\n[2/4] Scanning WhatsApp entries...")
        whatsapp_entries = db.session.query(WhatsAppEntry).filter(
            (WhatsAppEntry.alleged_subject_english.isnot(None)) | 
            (WhatsAppEntry.alleged_subject_chinese.isnot(None))
        ).all()
        
        results['whatsapp']['scanned'] = len(whatsapp_entries)
        
        for entry in whatsapp_entries:
            # 🔄 CRITICAL FIX: Remove ALL old POI links for this WhatsApp first
            print(f"[POI REFRESH] 🧹 Syncing WHATSAPP-{entry.id} with current assessment details")
            
            old_universal_links = db.session.query(POIIntelligenceLink).filter_by(
                source_type='WHATSAPP',
                source_id=entry.id
            ).all()
            for old_link in old_universal_links:
                print(f"[POI REFRESH] 🗑️ Removing old link: {old_link.poi_id} → WHATSAPP-{entry.id}")
                db.session.delete(old_link)
            
            db.session.flush()
            
            # Now create fresh links based on CURRENT assessment details
            english_names = [n.strip() for n in (entry.alleged_subject_english or '').split(',') if n.strip()]
            chinese_names = [n.strip() for n in (entry.alleged_subject_chinese or '').split(',') if n.strip()]
            
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
                    email_id=None,
                    source="WHATSAPP",
                    update_mode="merge"
                )
                
                if result.get('action') == 'created':
                    results['whatsapp']['profiles_created'] += 1
                elif result.get('action') == 'updated':
                    results['whatsapp']['profiles_updated'] += 1
                
                # 🔧 FIX: Create universal link ALWAYS (even if no case_profile_id)
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
                            case_profile_id=entry.caseprofile_id if entry.caseprofile_id else None,
                            confidence_score=0.90,
                            extraction_method='REFRESH'
                        )
                        db.session.add(new_link)
                        results['whatsapp']['links_created'] += 1
                        print(f"[POI REFRESH] 🔗 Created source link: {result['poi_id']} ← WHATSAPP-{entry.id}")
            
            # 🔧 FIX: Commit after processing EACH entry
            db.session.commit()
            
            print(f"[POI REFRESH] ✅ WHATSAPP-{entry.id} synced: {max_len} POI link(s) created")
        
        print(f"  ✅ WhatsApp: {results['whatsapp']['scanned']} scanned, {results['whatsapp']['profiles_created']} created, {results['whatsapp']['profiles_updated']} updated, {results['whatsapp']['links_created']} links")
        
        # ====================================================================
        # SCAN PATROL
        # ====================================================================
        print("\n[3/4] Scanning Online Patrol entries...")
        patrol_entries = db.session.query(OnlinePatrolEntry).filter(
            (OnlinePatrolEntry.alleged_subject_english.isnot(None)) | 
            (OnlinePatrolEntry.alleged_subject_chinese.isnot(None))
        ).all()
        
        results['patrol']['scanned'] = len(patrol_entries)
        
        for entry in patrol_entries:
            # 🔄 CRITICAL FIX: Remove ALL old POI links for this Patrol first
            print(f"[POI REFRESH] 🧹 Syncing PATROL-{entry.id} with current assessment details")
            
            old_universal_links = db.session.query(POIIntelligenceLink).filter_by(
                source_type='PATROL',
                source_id=entry.id
            ).all()
            for old_link in old_universal_links:
                print(f"[POI REFRESH] 🗑️ Removing old link: {old_link.poi_id} → PATROL-{entry.id}")
                db.session.delete(old_link)
            
            db.session.flush()
            
            # Now create fresh links based on CURRENT assessment details
            english_names = [n.strip() for n in (entry.alleged_subject_english or '').split(',') if n.strip()]
            chinese_names = [n.strip() for n in (entry.alleged_subject_chinese or '').split(',') if n.strip()]
            
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
                    email_id=None,
                    source="PATROL",
                    update_mode="merge"
                )
                
                if result.get('action') == 'created':
                    results['patrol']['profiles_created'] += 1
                elif result.get('action') == 'updated':
                    results['patrol']['profiles_updated'] += 1
                
                # 🔧 FIX: Create universal link ALWAYS (even if no case_profile_id)
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
                            case_profile_id=entry.caseprofile_id if entry.caseprofile_id else None,
                            confidence_score=0.90,
                            extraction_method='REFRESH'
                        )
                        db.session.add(new_link)
                        results['patrol']['links_created'] += 1
                        print(f"[POI REFRESH] 🔗 Created source link: {result['poi_id']} ← PATROL-{entry.id}")
            
            # 🔧 FIX: Commit after processing EACH entry
            db.session.commit()
            
            print(f"[POI REFRESH] ✅ PATROL-{entry.id} synced: {max_len} POI link(s) created")
        
        print(f"  ✅ Patrol: {results['patrol']['scanned']} scanned, {results['patrol']['profiles_created']} created, {results['patrol']['profiles_updated']} updated, {results['patrol']['links_created']} links")
        
        # ====================================================================
        # SCAN SURVEILLANCE
        # ====================================================================
        print("\n[4/4] Scanning Surveillance targets...")
        
        # Get all surveillance entries (not individual targets)
        surveillance_entries = db.session.query(SurveillanceEntry).all()
        results['surveillance']['scanned'] = len(surveillance_entries)
        
        for entry in surveillance_entries:
            # 🔄 CRITICAL FIX: Remove ALL old POI links for this Surveillance first
            print(f"[POI REFRESH] 🧹 Syncing SURVEILLANCE-{entry.id} with current targets")
            
            old_universal_links = db.session.query(POIIntelligenceLink).filter_by(
                source_type='SURVEILLANCE',
                source_id=entry.id
            ).all()
            for old_link in old_universal_links:
                print(f"[POI REFRESH] 🗑️ Removing old link: {old_link.poi_id} → SURVEILLANCE-{entry.id}")
                db.session.delete(old_link)
            
            db.session.flush()
            
            # Now create fresh links based on CURRENT targets
            targets = db.session.query(Target).filter_by(surveillance_id=entry.id).all()
            
            for target in targets:
                if not target.name or not target.name.strip():
                    continue
                
                # Detect if name is Chinese or English
                is_chinese = bool(re.search(r'[\u4e00-\u9fff]', target.name))
                
                # Extract license info
                license_num = target.license_number if target.license_number else ""
                license_type = target.license_type if target.license_type else ""
                
                result = create_or_update_alleged_person_profile(
                    db, AllegedPersonProfile, EmailAllegedPersonLink,
                    name_english=None if is_chinese else target.name.strip(),
                    name_chinese=target.name.strip() if is_chinese else None,
                    agent_number=license_num,
                    license_number=license_num,
                    role=license_type,
                    email_id=None,
                    source="SURVEILLANCE",
                    update_mode="merge"
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
                        source_id=entry.id
                    ).first()
                    
                    if not existing_link:
                        new_link = POIIntelligenceLink(
                            poi_id=result['poi_id'],
                            source_type='SURVEILLANCE',
                            source_id=entry.id,
                            case_profile_id=None,  # Surveillance doesn't have case_profile_id
                            confidence_score=0.95,
                            extraction_method='REFRESH'
                        )
                        db.session.add(new_link)
                        results['surveillance']['links_created'] += 1
                        print(f"[POI REFRESH] 🔗 Created source link: {result['poi_id']} ← SURVEILLANCE-{entry.id}")
            
            # 🔧 FIX: Commit after processing EACH entry
            db.session.commit()
            
            target_count = len(targets)
            print(f"[POI REFRESH] ✅ SURVEILLANCE-{entry.id} synced: {target_count} target(s) processed")
        
        print(f"  ✅ Surveillance: {results['surveillance']['scanned']} scanned, {results['surveillance']['profiles_created']} created, {results['surveillance']['profiles_updated']} updated")
        
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

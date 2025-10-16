#!/usr/bin/env python3
"""
🔍 DEBUG SCRIPT: Check Auto-Linking Status
This script will tell you EXACTLY what's in your database
"""

from app1_production import app, db, AllegedPersonProfile, EmailAllegedPersonLink, Email
from datetime import datetime

def check_auto_linking_status():
    with app.app_context():
        print("=" * 80)
        print("🔍 AUTO-LINKING DIAGNOSTIC REPORT")
        print("=" * 80)
        print()
        
        # 1. Check total profiles
        total_profiles = AllegedPersonProfile.query.filter_by(status='ACTIVE').count()
        print(f"📊 TOTAL PROFILES: {total_profiles}")
        print()
        
        # 2. Check total email links
        total_links = EmailAllegedPersonLink.query.count()
        print(f"📧 TOTAL EMAIL-PERSON LINKS: {total_links}")
        print()
        
        # 3. Break down by creation method
        ai_links = EmailAllegedPersonLink.query.filter(
            EmailAllegedPersonLink.created_by.in_(['AI', 'AI_ANALYSIS', 'System'])
        ).count()
        
        manual_input_links = EmailAllegedPersonLink.query.filter(
            EmailAllegedPersonLink.created_by == 'MANUAL_INPUT'
        ).count()
        
        manual_links = EmailAllegedPersonLink.query.filter(
            EmailAllegedPersonLink.created_by == 'Manual'
        ).count()
        
        other_links = total_links - ai_links - manual_input_links - manual_links
        
        print("📈 LINK BREAKDOWN BY SOURCE:")
        print(f"   🤖 AI Auto-linked (AI/AI_ANALYSIS/System): {ai_links}")
        print(f"   ✋ Manual Assessment Auto-linked (MANUAL_INPUT): {manual_input_links}")
        print(f"   🔗 Manual Button-linked (Manual): {manual_links}")
        print(f"   ❓ Other: {other_links}")
        print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   📊 TOTAL AUTO-LINKED: {ai_links + manual_input_links}")
        print(f"   👆 TOTAL MANUAL-LINKED: {manual_links}")
        print()
        
        # 4. Show recent profiles with their link counts
        print("👥 RECENT PROFILES (Last 10):")
        print("-" * 80)
        recent_profiles = AllegedPersonProfile.query.filter_by(
            status='ACTIVE'
        ).order_by(AllegedPersonProfile.created_at.desc()).limit(10).all()
        
        for profile in recent_profiles:
            link_count = EmailAllegedPersonLink.query.filter_by(
                alleged_person_id=profile.id
            ).count()
            
            auto_link_count = EmailAllegedPersonLink.query.filter(
                EmailAllegedPersonLink.alleged_person_id == profile.id,
                EmailAllegedPersonLink.created_by.in_(['AI', 'AI_ANALYSIS', 'MANUAL_INPUT', 'System'])
            ).count()
            
            manual_link_count = EmailAllegedPersonLink.query.filter(
                EmailAllegedPersonLink.alleged_person_id == profile.id,
                EmailAllegedPersonLink.created_by == 'Manual'
            ).count()
            
            name = profile.name_english or profile.name_chinese or "No Name"
            created_date = profile.created_at.strftime("%Y-%m-%d %H:%M") if profile.created_at else "Unknown"
            
            print(f"   {profile.poi_id}: {name}")
            print(f"      Created: {created_date} by {profile.created_by}")
            print(f"      Links: {link_count} total ({auto_link_count} auto, {manual_link_count} manual)")
            print()
        
        # 5. Check specific profile details
        if total_profiles > 0:
            print("=" * 80)
            print("🔍 DETAILED PROFILE ANALYSIS (First 3 profiles)")
            print("=" * 80)
            
            sample_profiles = AllegedPersonProfile.query.filter_by(
                status='ACTIVE'
            ).order_by(AllegedPersonProfile.created_at.desc()).limit(3).all()
            
            for profile in sample_profiles:
                print()
                print(f"📋 Profile: {profile.poi_id}")
                print(f"   Name (EN): {profile.name_english or 'N/A'}")
                print(f"   Name (CN): {profile.name_chinese or 'N/A'}")
                print(f"   Created: {profile.created_at.strftime('%Y-%m-%d %H:%M') if profile.created_at else 'N/A'}")
                print(f"   Created By: {profile.created_by}")
                print()
                
                # Get all links for this profile
                links = EmailAllegedPersonLink.query.filter_by(
                    alleged_person_id=profile.id
                ).all()
                
                if links:
                    print(f"   📧 {len(links)} Email Link(s):")
                    for link in links:
                        email = Email.query.get(link.email_id)
                        if email:
                            print(f"      • Email ID {email.id} (INT: {email.int_reference_number})")
                            print(f"        Subject: {email.subject[:60] if email.subject else 'No subject'}...")
                            print(f"        Linked by: {link.created_by}")
                            print(f"        Linked at: {link.created_at.strftime('%Y-%m-%d %H:%M') if link.created_at else 'N/A'}")
                else:
                    print(f"   ⚠️ NO EMAIL LINKS FOUND!")
                print()
        
        # 6. Final diagnosis
        print("=" * 80)
        print("💡 DIAGNOSIS:")
        print("=" * 80)
        
        if total_profiles == 0:
            print("❌ NO PROFILES FOUND!")
            print("   Solution: Run AI analysis or save manual assessment with alleged person names")
        elif total_links == 0:
            print("❌ PROFILES EXIST BUT NO EMAIL LINKS!")
            print("   This means automation is NOT creating the links")
            print("   Possible causes:")
            print("   1. Automation system not enabled (check ALLEGED_PERSON_AUTOMATION)")
            print("   2. process_ai_analysis_results() or process_manual_input() not being called")
            print("   3. Database commit error during automation")
        elif ai_links + manual_input_links == 0:
            print("⚠️ NO AUTO-LINKS FOUND (only manual links exist)")
            print(f"   You have {manual_links} manually-created links")
            print("   Auto-linking might not be working properly")
        else:
            print(f"✅ AUTO-LINKING IS WORKING!")
            print(f"   Found {ai_links + manual_input_links} auto-created email-person links")
            print()
            print("   If you don't see these in the UI:")
            print("   1. Check console logs when viewing a profile")
            print("   2. Verify template is using 'related_emails' variable")
            print("   3. Check browser console for JavaScript errors")
        
        print()
        print("=" * 80)

if __name__ == "__main__":
    try:
        check_auto_linking_status()
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

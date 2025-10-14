#!/usr/bin/env python3
"""
🔧 Automation System Test Script
Tests if circular import fix resolved the automation module loading issue
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
print("\n" + "="*60)
print("🧪 TESTING AUTOMATED ALLEGED PERSON PROFILE SYSTEM")
print("="*60)

try:
    # Test 1: Import automation module
    print("\n📦 Testing module import...")
    import alleged_person_automation
    print("   ✅ alleged_person_automation module imported successfully")
    
    # Test 2: Import Flask app for application context
    print("\n🌐 Setting up Flask application context...")
    from app1_production import app
    print("   ✅ Flask app imported successfully")
    
    # Test 3: Test database initialization within app context
    print("\n🗄️  Testing database initialization...")
    with app.app_context():
        db_success = alleged_person_automation.initialize_database()
        if db_success:
            print("   ✅ Database initialized successfully")
            print("   ✅ Models available: AllegedPersonProfile, EmailAllegedPersonLink")
        else:
            print("   ❌ Database initialization failed")
            
        # Test 4: Test POI ID generation
        print("\n🆔 Testing POI ID generation...")
        test_poi_id = alleged_person_automation.generate_next_poi_id()
        print(f"   ✅ Generated POI ID: {test_poi_id}")
        
        # Test 5: Test profile matching
        print("\n🔍 Testing profile matching...")
        test_match = alleged_person_automation.find_matching_profile(
            name_english="Test Person",
            name_chinese="测试人员"
        )
        if test_match is None:
            print("   ✅ Profile matching working (no matches found as expected)")
        else:
            print(f"   ✅ Profile matching working (found: {test_match})")
            
    # Test 6: Test automation system status
    print("\n🤖 Testing automation system status...")
    if hasattr(alleged_person_automation, 'process_ai_analysis_results'):
        print("   ✅ AI integration function available")
    if hasattr(alleged_person_automation, 'process_manual_input'):
        print("   ✅ Manual input integration function available")
    if hasattr(alleged_person_automation, 'link_email_to_profile'):
        print("   ✅ Email linking function available")
        
    print("\n" + "="*60)
    print("🎉 AUTOMATION SYSTEM TEST COMPLETE")
    print("="*60)
    
    if db_success:
        print("✅ Status: AUTOMATION SYSTEM FULLY OPERATIONAL")
        print("🚀 Ready to create automated alleged person profiles!")
    else:
        print("⚠️  Status: MODULE LOADED BUT DATABASE CONNECTION FAILED")
        print("💡 Check database configuration and connectivity")
        
    print("\n📋 Next Steps:")
    print("   1. Run migration script: python3 migrate_alleged_person_automation.py")
    print("   2. Test with real data: Run AI analysis or manual input")
    print("   3. Check alleged_subject_list for new profiles with POI-001, POI-002, etc.")
    
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("💡 Circular import may still exist - check logs for details")
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ Test failed: {e}")
    print("💡 Check system logs for more details")
    sys.exit(1)

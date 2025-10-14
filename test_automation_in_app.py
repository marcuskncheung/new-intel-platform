#!/usr/bin/env python3
"""
🧪 IN-APP AUTOMATION TEST
Test the automation system within the running Flask application context
"""

from app1_production import app
import alleged_person_automation

def test_automation_system():
    """Test automation system within Flask app context"""
    
    print("\n" + "="*60)
    print("🧪 TESTING AUTOMATION SYSTEM IN FLASK APP")
    print("="*60)
    
    with app.app_context():
        # Test 1: Database initialization
        print("\n🗄️  Testing database initialization...")
        db_success = alleged_person_automation.initialize_database()
        if db_success:
            print("   ✅ Database models loaded successfully")
        else:
            print("   ❌ Database initialization failed")
            return False
            
        # Test 2: POI ID generation
        print("\n🆔 Testing POI ID generation...")
        try:
            test_poi_id = alleged_person_automation.generate_next_poi_id()
            print(f"   ✅ Generated POI ID: {test_poi_id}")
        except Exception as e:
            print(f"   ❌ POI ID generation failed: {e}")
            return False
            
        # Test 3: Profile matching
        print("\n🔍 Testing profile matching...")
        try:
            test_match = alleged_person_automation.find_matching_profile(
                name_english="Test Person",
                name_chinese="测试人员"
            )
            if test_match is None:
                print("   ✅ Profile matching working (no matches found)")
            else:
                print(f"   ✅ Profile matching found: {test_match.get('poi_id', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Profile matching failed: {e}")
            return False
            
        # Test 4: Profile creation simulation
        print("\n🆕 Testing profile creation...")
        try:
            result = alleged_person_automation.create_or_update_alleged_person_profile(
                name_english="John Test Agent",
                name_chinese="测试代理员",
                agent_number="TEST123456",
                company="Test Insurance Company",
                role="Agent",
                source="SYSTEM_TEST"
            )
            
            if result.get('success'):
                poi_id = result.get('poi_id')
                action = result.get('action')
                print(f"   ✅ Profile {action}: {poi_id}")
            else:
                print(f"   ❌ Profile creation failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Profile creation failed: {e}")
            return False
            
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED - AUTOMATION SYSTEM OPERATIONAL!")
        print("="*60)
        
        return True

if __name__ == "__main__":
    test_automation_system()

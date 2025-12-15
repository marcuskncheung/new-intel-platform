#!/usr/bin/env python3
"""
Sync case_profile.alleged_person with source entries.

This fixes the issue where:
- Platform shows INT-006 with alleged person = "CHAN"
- But case_profile shows alleged_person = "MARY" (old value)

The script updates case_profile to match the current source entry data.
"""

import os
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://intel_user:intel_password@localhost:5432/intelligence_db')

def run_sync():
    """Sync case_profile alleged_person with source entries"""
    import psycopg2
    
    print("=" * 60)
    print("Syncing case_profile.alleged_person with source entries")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Track changes
        changes = []
        
        # Sync Email entries
        print("\n📧 Checking Email entries...")
        cursor.execute("""
            SELECT cp.id, cp.int_reference, cp.alleged_person as cp_person, 
                   e.alleged_person as source_person
            FROM case_profile cp
            JOIN email e ON cp.source_id = e.id
            WHERE cp.source_type = 'email'
            AND (cp.alleged_person IS DISTINCT FROM e.alleged_person)
        """)
        for row in cursor.fetchall():
            cp_id, int_ref, cp_person, source_person = row
            print(f"  {int_ref}: '{cp_person}' → '{source_person}'")
            changes.append((cp_id, source_person))
        
        # Sync WhatsApp entries
        print("\n💬 Checking WhatsApp entries...")
        cursor.execute("""
            SELECT cp.id, cp.int_reference, cp.alleged_person as cp_person, 
                   w.alleged_person as source_person
            FROM case_profile cp
            JOIN whatsapp_entry w ON cp.source_id = w.id
            WHERE cp.source_type = 'whatsapp'
            AND (cp.alleged_person IS DISTINCT FROM w.alleged_person)
        """)
        for row in cursor.fetchall():
            cp_id, int_ref, cp_person, source_person = row
            print(f"  {int_ref}: '{cp_person}' → '{source_person}'")
            changes.append((cp_id, source_person))
        
        # Sync Online Patrol entries
        print("\n🌐 Checking Online Patrol entries...")
        cursor.execute("""
            SELECT cp.id, cp.int_reference, cp.alleged_person as cp_person, 
                   o.alleged_person as source_person
            FROM case_profile cp
            JOIN online_patrol_entry o ON cp.source_id = o.id
            WHERE cp.source_type = 'patrol'
            AND (cp.alleged_person IS DISTINCT FROM o.alleged_person)
        """)
        for row in cursor.fetchall():
            cp_id, int_ref, cp_person, source_person = row
            print(f"  {int_ref}: '{cp_person}' → '{source_person}'")
            changes.append((cp_id, source_person))
        
        # Sync Surveillance entries (uses targets, not alleged_person directly)
        print("\n👁️ Checking Surveillance entries...")
        cursor.execute("""
            SELECT cp.id, cp.int_reference, cp.alleged_person as cp_person,
                   (SELECT string_agg(t.name, ', ') FROM target t WHERE t.surveillance_id = s.id) as source_person
            FROM case_profile cp
            JOIN surveillance_entry s ON cp.source_id = s.id
            WHERE cp.source_type = 'surveillance'
        """)
        for row in cursor.fetchall():
            cp_id, int_ref, cp_person, source_person = row
            if cp_person != source_person and source_person:
                print(f"  {int_ref}: '{cp_person}' → '{source_person}'")
                changes.append((cp_id, source_person))
        
        # Sync Received by Hand entries
        print("\n📄 Checking Received by Hand entries...")
        cursor.execute("""
            SELECT cp.id, cp.int_reference, cp.alleged_person as cp_person, 
                   r.alleged_person as source_person
            FROM case_profile cp
            JOIN received_by_hand r ON cp.source_id = r.id
            WHERE cp.source_type = 'received_by_hand'
            AND (cp.alleged_person IS DISTINCT FROM r.alleged_person)
        """)
        for row in cursor.fetchall():
            cp_id, int_ref, cp_person, source_person = row
            print(f"  {int_ref}: '{cp_person}' → '{source_person}'")
            changes.append((cp_id, source_person))
        
        # Apply changes
        if changes:
            print(f"\n🔄 Applying {len(changes)} updates...")
            for cp_id, new_person in changes:
                cursor.execute("""
                    UPDATE case_profile 
                    SET alleged_person = %s 
                    WHERE id = %s
                """, (new_person, cp_id))
            
            conn.commit()
            print(f"✅ Updated {len(changes)} case_profile records!")
        else:
            print("\n✅ All case_profile records are already in sync!")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Sync completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_sync()

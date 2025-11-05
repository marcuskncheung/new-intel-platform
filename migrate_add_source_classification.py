#!/usr/bin/env python3
"""
Migration: Add Source Classification Fields to Email Table
============================================================
Date: 2025-11-05
Purpose: Add comprehensive source classification system to track whether
         intelligence sources are internal or external, with detailed subcategories

New Fields:
-----------
1. source_category: 'INTERNAL' or 'EXTERNAL'
2. internal_source_type: For INTERNAL sources
   - 'MARKET_CONDUCT_SUPERVISION'
   - 'COMPLAINT_TEAM'
   - 'OTHER_INTERNAL'
3. internal_source_other: Free text for OTHER_INTERNAL
4. external_source_type: For EXTERNAL sources
   - 'REGULATOR' (SFC, HKMA, MPFA)
   - 'LAW_ENFORCEMENT' (Police, ICAC, Customs)
   - 'INSURANCE_INDUSTRY'
   - 'OTHER_EXTERNAL'
5. external_regulator: If REGULATOR selected (SFC, HKMA, MPFA, OTHER)
6. external_law_enforcement: If LAW_ENFORCEMENT selected (POLICE, ICAC, CUSTOMS, OTHER)
7. external_source_other: Free text for OTHER_EXTERNAL or OTHER regulators

Usage:
------
python migrate_add_source_classification.py
"""

import os
import sys
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db

def run_migration():
    """Add source classification columns to email table"""
    
    print("=" * 80)
    print("📊 EMAIL SOURCE CLASSIFICATION MIGRATION")
    print("=" * 80)
    print()
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('email')]
            
            columns_to_add = [
                ('source_category', 'VARCHAR(20)'),
                ('internal_source_type', 'VARCHAR(50)'),
                ('internal_source_other', 'VARCHAR(255)'),
                ('external_source_type', 'VARCHAR(50)'),
                ('external_regulator', 'VARCHAR(50)'),
                ('external_law_enforcement', 'VARCHAR(50)'),
                ('external_source_other', 'VARCHAR(255)')
            ]
            
            added_count = 0
            skipped_count = 0
            
            for col_name, col_type in columns_to_add:
                if col_name in existing_columns:
                    print(f"⏭️  Column '{col_name}' already exists, skipping")
                    skipped_count += 1
                else:
                    print(f"➕ Adding column: {col_name} ({col_type})")
                    
                    # Add column with NULL default
                    alter_sql = f"ALTER TABLE email ADD COLUMN {col_name} {col_type}"
                    db.session.execute(text(alter_sql))
                    db.session.commit()
                    
                    print(f"✅ Column '{col_name}' added successfully")
                    added_count += 1
            
            print()
            print("=" * 80)
            print(f"✅ MIGRATION COMPLETE")
            print(f"   • Columns added: {added_count}")
            print(f"   • Columns skipped (already exist): {skipped_count}")
            print("=" * 80)
            print()
            print("📋 SOURCE CATEGORY OPTIONS:")
            print()
            print("INTERNAL:")
            print("  1. Market Conduct Supervision Team")
            print("  2. Complaint Team")
            print("  3. Other Internal Department (specify)")
            print()
            print("EXTERNAL:")
            print("  A. Regulators:")
            print("     - SFC (Securities and Futures Commission)")
            print("     - HKMA (Hong Kong Monetary Authority)")
            print("     - MPFA (Mandatory Provident Fund Schemes Authority)")
            print("     - Other Regulator (specify)")
            print()
            print("  B. Law Enforcement:")
            print("     - Hong Kong Police Force")
            print("     - ICAC (Independent Commission Against Corruption)")
            print("     - Customs and Excise Department")
            print("     - Other Law Enforcement (specify)")
            print()
            print("  C. Insurance Industry")
            print("  D. Other External Source (specify)")
            print()
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ ERROR during migration: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    run_migration()

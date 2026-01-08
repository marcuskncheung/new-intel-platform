#!/usr/bin/env python3
"""
Migration Analysis Script
Identifies all changes needed to switch from app1_production.py to blueprints

Run: python analyze_migration_changes.py
"""

import os
import re
from collections import defaultdict

# Blueprint route mappings (old name -> new blueprint.name)
ROUTE_MAPPINGS = {
    # Auth
    'login': 'auth.login',
    'logout': 'auth.logout',
    'signup': 'auth.signup',
    
    # Main
    'home': 'main.home',
    'dashboard': 'main.home',
    'index': 'main.index',
    'about': 'main.about',
    'tools': 'main.tools',
    'health': 'main.health_check',
    'global_search_page': 'main.global_search_page',
    'welcome': 'main.home',
    
    # Admin
    'admin_dashboard': 'admin.admin_dashboard',
    'admin_users': 'admin.admin_users',
    'admin_create_user': 'admin.admin_create_user',
    'admin_edit_user': 'admin.admin_edit_user',
    'admin_delete_user': 'admin.admin_delete_user',
    'admin_features': 'admin.admin_features',
    'admin_features_update': 'admin.admin_features_update',
    'admin_database': 'admin.admin_database',
    'admin_logs': 'admin.admin_logs',
    'admin_logs_export': 'admin.admin_logs_export',
    'admin_restart_server': 'admin.admin_restart_server',
    'admin_shutdown_server': 'admin.admin_shutdown_server',
    'security_admin': 'admin.admin_security',
    
    # Email Intel
    'int_source': 'email_intel.int_source',
    'int_source_email_detail': 'email_intel.email_detail',
    'delete_email': 'email_intel.delete_email',
    'process_exchange_inbox': 'email_intel.process_exchange_inbox',
    'assign_case_number': 'email_intel.assign_case_number',
    'download_email_attachment': 'email_intel.download_attachment',
    'view_email_attachment': 'email_intel.view_attachment',
    
    # WhatsApp Intel
    'add_whatsapp': 'whatsapp_intel.add_whatsapp',
    'int_source_whatsapp_detail': 'whatsapp_intel.whatsapp_detail',
    'delete_whatsapp': 'whatsapp_intel.delete_whatsapp',
    'whatsapp_image': 'whatsapp_intel.whatsapp_image',
    
    # Patrol Intel
    'add_online_patrol': 'patrol_intel.add_patrol',
    'online_patrol_detail': 'patrol_intel.patrol_detail',
    'delete_online_patrol': 'patrol_intel.delete_patrol',
    
    # Surveillance Intel
    'add_surveillance': 'surveillance_intel.add_surveillance',
    'surveillance_detail': 'surveillance_intel.surveillance_detail',
    
    # Received By Hand Intel
    'add_received_by_hand': 'received_by_hand_intel.add_received_by_hand',
    'received_by_hand_detail': 'received_by_hand_intel.received_by_hand_detail',
    'delete_received_by_hand': 'received_by_hand_intel.delete_received_by_hand',
    
    # POI
    'alleged_subject_list': 'poi.alleged_subject_list',
    'alleged_subject_profiles': 'poi.alleged_subject_profiles',
    'alleged_subject_profile': 'poi.alleged_subject_profile',
    'create_alleged_person_profile': 'poi.create_profile',
    'delete_alleged_person_profile': 'poi.delete_alleged_person_profile',
    
    # INT Reference
    'int_reference_detail': 'int_reference.int_reference_detail',
    
    # Analytics
    'int_analytics': 'analytics.int_analytics',
    
    # Export
    'master_export': 'export.master_export',
    'inbox_export': 'export.inbox_export',
}


def find_url_for_calls(content):
    """Find all url_for() calls in content"""
    # Match url_for('route_name') or url_for("route_name")
    pattern = r"url_for\(['\"]([^'\"]+)['\"]"
    return re.findall(pattern, content)


def analyze_templates():
    """Analyze HTML templates for url_for() calls"""
    template_dir = 'templates'
    results = defaultdict(list)
    
    if not os.path.exists(template_dir):
        print(f"⚠️  Template directory not found: {template_dir}")
        return results
    
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    routes = find_url_for_calls(content)
                    for route in routes:
                        if route != 'static':  # Ignore static files
                            results[route].append(filepath)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return results


def analyze_python_files():
    """Analyze Python files for app1_production imports"""
    results = []
    
    for file in os.listdir('.'):
        if file.endswith('.py') and file not in ['analyze_migration_changes.py']:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'from app1_production import' in content or 'import app1_production' in content:
                    results.append(file)
            except Exception as e:
                pass
    
    return results


def analyze_docker_files():
    """Analyze Docker files for entry point"""
    results = {}
    
    if os.path.exists('Dockerfile'):
        with open('Dockerfile', 'r') as f:
            content = f.read()
        if 'app1_production.py' in content:
            results['Dockerfile'] = 'Uses app1_production.py as entry point'
    
    if os.path.exists('docker-compose.yml'):
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
        if 'app1_production.py' in content:
            results['docker-compose.yml'] = 'References app1_production.py'
    
    return results


def main():
    print("=" * 70)
    print("🔍 BLUEPRINT MIGRATION ANALYSIS")
    print("=" * 70)
    
    # 1. Analyze templates
    print("\n📄 TEMPLATE ANALYSIS (url_for() calls)")
    print("-" * 50)
    
    template_routes = analyze_templates()
    
    needs_update = []
    already_blueprint = []
    unknown = []
    
    for route, files in sorted(template_routes.items()):
        if '.' in route:
            already_blueprint.append((route, files))
        elif route in ROUTE_MAPPINGS:
            needs_update.append((route, ROUTE_MAPPINGS[route], files))
        else:
            unknown.append((route, files))
    
    print(f"\n✅ Already using blueprint format: {len(already_blueprint)}")
    print(f"🔄 Need to update: {len(needs_update)}")
    print(f"❓ Unknown (may need manual check): {len(unknown)}")
    
    if needs_update:
        print("\n🔄 Routes that need updating:")
        for old, new, files in needs_update[:20]:
            print(f"   {old} → {new}")
            print(f"      Used in: {len(files)} file(s)")
    
    if unknown:
        print("\n❓ Unknown routes (check manually):")
        for route, files in unknown[:20]:
            print(f"   {route}")
            print(f"      Used in: {files[0]}" + (f" (+{len(files)-1} more)" if len(files) > 1 else ""))
    
    # 2. Analyze Python files
    print("\n\n🐍 PYTHON FILES (importing from app1_production)")
    print("-" * 50)
    
    python_files = analyze_python_files()
    print(f"Files that import from app1_production.py: {len(python_files)}")
    for f in python_files:
        print(f"   - {f}")
    
    # 3. Analyze Docker files
    print("\n\n🐳 DOCKER FILES")
    print("-" * 50)
    
    docker_results = analyze_docker_files()
    for file, status in docker_results.items():
        print(f"   {file}: {status}")
    
    # 4. Summary
    print("\n\n📊 SUMMARY")
    print("=" * 70)
    print(f"""
OPTION A: Keep app1_production.py (SAFE - NO CHANGES NEEDED)
   - Blueprints are ready but not activated
   - app1_production.py continues to handle all routes
   - Gradual migration possible

OPTION B: Switch to Blueprints (REQUIRES CHANGES)
   - Update Dockerfile: CMD ["python", "app.py"]
   - Update {len(needs_update)} url_for() calls in templates
   - Update {len(python_files)} Python files
   - Test thoroughly before deploying

RECOMMENDED: Start with Option A, test locally, then switch to Option B
""")


if __name__ == '__main__':
    main()

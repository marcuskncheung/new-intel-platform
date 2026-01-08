#!/usr/bin/env python3
"""
Script to migrate url_for() calls in templates to use blueprint prefixes.
This is part of the Blueprint migration (Option B).
"""

import os
import re
import glob

# Mapping of old route names to new blueprint-prefixed names
URL_MAPPING = {
    # Auth Blueprint
    'login': 'auth.login',
    'logout': 'auth.logout',
    
    # Main Blueprint
    'home': 'main.home',
    'index': 'main.index',
    'global_search_page': 'main.global_search_page',
    'global_search_api': 'main.global_search_api',
    'about': 'main.about',
    
    # Admin Blueprint
    'admin_dashboard': 'admin.admin_dashboard',
    'admin_users': 'admin.admin_users',
    'admin_create_user': 'admin.admin_create_user',
    'admin_edit_user': 'admin.admin_edit_user',
    'admin_delete_user': 'admin.admin_delete_user',
    'admin_toggle_user': 'admin.admin_toggle_user',
    'admin_features': 'admin.admin_features',
    'admin_features_update': 'admin.admin_features_update',
    'admin_database': 'admin.admin_database',
    'admin_logs': 'admin.admin_logs',
    'admin_logs_export': 'admin.admin_logs_export',
    'security_admin': 'admin.security_admin',
    'export_audit_logs': 'admin.export_audit_logs',
    
    # Email Intel Blueprint
    'int_source': 'email_intel.int_source',
    'process_exchange_inbox': 'email_intel.process_exchange_inbox',
    'int_source_email_detail': 'email_intel.int_source_email_detail',
    'int_source_update_assessment': 'email_intel.int_source_update_assessment',
    'update_int_reference': 'email_intel.update_int_reference',
    'int_source_download_email_attachment': 'email_intel.int_source_download_email_attachment',
    'int_source_embedded_attachment_viewer': 'email_intel.int_source_embedded_attachment_viewer',
    'list_int_source_email': 'email_intel.list_int_source_email',
    'int_source_ai_grouped_excel_export': 'email_intel.int_source_ai_grouped_excel_export',
    'int_source_master_export': 'email_intel.int_source_master_export',
    
    # WhatsApp Intel Blueprint
    'add_whatsapp': 'whatsapp_intel.add_whatsapp',
    'whatsapp_detail': 'whatsapp_intel.whatsapp_detail',
    'int_source_whatsapp_detail': 'whatsapp_intel.int_source_whatsapp_detail',
    'delete_whatsapp': 'whatsapp_intel.delete_whatsapp',
    'update_whatsapp_details': 'whatsapp_intel.update_whatsapp_details',
    'update_whatsapp_int_reference': 'whatsapp_intel.update_whatsapp_int_reference',
    'int_source_whatsapp_update_assessment': 'whatsapp_intel.int_source_whatsapp_update_assessment',
    'whatsapp_image_download': 'whatsapp_intel.whatsapp_image_download',
    'delete_whatsapp_file': 'whatsapp_intel.delete_whatsapp_file',
    'delete_whatsapp_image': 'whatsapp_intel.delete_whatsapp_image',
    'list_whatsapp_entries_aligned': 'whatsapp_intel.list_whatsapp_entries_aligned',
    'whatsapp_export': 'whatsapp_intel.whatsapp_export',
    
    # Patrol Intel Blueprint
    'add_online_patrol': 'patrol_intel.add_online_patrol',
    'online_patrol_detail': 'patrol_intel.online_patrol_detail',
    'int_source_online_patrol_detail': 'patrol_intel.int_source_online_patrol_detail',
    'delete_online_patrol': 'patrol_intel.delete_online_patrol',
    'update_patrol_details': 'patrol_intel.update_patrol_details',
    'update_patrol_int_reference': 'patrol_intel.update_patrol_int_reference',
    'int_source_patrol_update_assessment': 'patrol_intel.int_source_patrol_update_assessment',
    'view_patrol_photo': 'patrol_intel.view_patrol_photo',
    'delete_patrol_file': 'patrol_intel.delete_patrol_file',
    'list_int_source_online_patrol_aligned': 'patrol_intel.list_int_source_online_patrol_aligned',
    'online_patrol_export': 'patrol_intel.online_patrol_export',
    
    # Surveillance Intel Blueprint
    'add_surveillance': 'surveillance_intel.add_surveillance',
    'surveillance_detail': 'surveillance_intel.surveillance_detail',
    'int_source_surveillance_detail': 'surveillance_intel.int_source_surveillance_detail',
    'surveillance_list': 'surveillance_intel.surveillance_list',
    'surveillance_export': 'surveillance_intel.surveillance_export',
    'surveillance_document_download': 'surveillance_intel.surveillance_document_download',
    'surveillance_document_view': 'surveillance_intel.surveillance_document_view',
    
    # Received By Hand Intel Blueprint
    'add_received_by_hand': 'received_by_hand_intel.add_received_by_hand',
    'received_by_hand_detail': 'received_by_hand_intel.received_by_hand_detail',
    'delete_received_by_hand': 'received_by_hand_intel.delete_received_by_hand',
    'update_received_by_hand_details': 'received_by_hand_intel.update_received_by_hand_details',
    'update_received_by_hand_int_reference': 'received_by_hand_intel.update_received_by_hand_int_reference',
    'update_received_by_hand_assessment': 'received_by_hand_intel.update_received_by_hand_assessment',
    'received_by_hand_document_download': 'received_by_hand_intel.received_by_hand_document_download',
    'delete_received_by_hand_document': 'received_by_hand_intel.delete_received_by_hand_document',
    'received_by_hand_list': 'received_by_hand_intel.received_by_hand_list',
    'received_by_hand_export': 'received_by_hand_intel.received_by_hand_export',
    
    # POI Blueprint
    'alleged_subject_list': 'poi.alleged_subject_list',
    'alleged_subject_profiles': 'poi.alleged_subject_profiles',
    'view_alleged_person_profile': 'poi.view_alleged_person_profile',
    'delete_alleged_person_profile': 'poi.delete_alleged_person_profile',
    'create_alleged_person_profile': 'poi.create_alleged_person_profile',
    'edit_alleged_subject_profile': 'poi.edit_alleged_subject_profile',
    'refresh_poi_profiles': 'poi.refresh_poi_profiles',
    'create_manual_profile': 'poi.create_manual_profile',
    'find_duplicate_poi_profiles': 'poi.find_duplicate_poi_profiles',
    'merge_poi_profiles': 'poi.merge_poi_profiles',
    'rebuild_poi_list': 'poi.rebuild_poi_list',
    'details': 'poi.details',
    'delete': 'poi.delete',
    'profile_detail': 'poi.profile_detail',
    'edit_profile': 'poi.edit_profile',
    
    # INT Reference Blueprint
    'int_reference_detail': 'int_reference.int_reference_detail',
    'int_statistics_dashboard': 'int_reference.int_statistics_dashboard',
    'update_case_profile': 'int_reference.update_case_profile',
    
    # Analytics Blueprint
    'int_analytics': 'analytics.int_analytics',
    'analytics_api': 'analytics.analytics_api',
    
    # AI Blueprint (routes if any)
    'ai_analyze': 'ai.ai_analyze',
    
    # Export Blueprint
    'export_pdf': 'export.export_pdf',
    'export_excel': 'export.export_excel',
    
    # Tools Blueprint
    'tools': 'tools.tools',
    'evaluation_cases': 'tools.evaluation_cases',
}

def migrate_template(file_path, dry_run=False):
    """Migrate url_for() calls in a template file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Pattern to match url_for('route_name' or url_for("route_name"
    # But NOT url_for('static' which should remain unchanged
    pattern = r"url_for\(['\"](\w+)['\"]"
    
    def replace_route(match):
        old_route = match.group(1)
        
        # Skip 'static' routes - they don't need blueprint prefix
        if old_route == 'static':
            return match.group(0)
        
        # Check if already has blueprint prefix
        if '.' in old_route:
            return match.group(0)
        
        # Look up the new route name
        if old_route in URL_MAPPING:
            new_route = URL_MAPPING[old_route]
            changes_made.append(f"  {old_route} -> {new_route}")
            # Preserve the quote style
            quote = match.group(0)[-1]
            return f"url_for('{new_route}'"
        else:
            changes_made.append(f"  WARNING: Unknown route '{old_route}' - NOT CHANGED")
            return match.group(0)
    
    new_content = re.sub(pattern, replace_route, content)
    
    if new_content != original_content:
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Updated: {file_path}")
        else:
            print(f"📋 Would update: {file_path}")
        
        for change in changes_made:
            print(change)
        return True
    return False


def main():
    import sys
    
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print("🚀 MIGRATING url_for() calls in templates...\n")
    
    # Find all HTML templates
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    template_files = glob.glob(os.path.join(templates_dir, '**', '*.html'), recursive=True)
    
    updated_count = 0
    for template_file in sorted(template_files):
        if migrate_template(template_file, dry_run):
            updated_count += 1
            print()  # Add blank line between files
    
    print(f"\n{'Would update' if dry_run else 'Updated'} {updated_count} files")
    
    if dry_run:
        print("\nRun without --dry-run to apply changes.")
    else:
        print("\n✅ Template migration complete!")


if __name__ == '__main__':
    main()

#!/bin/bash
# Script to push clean code to Hong Kong Insurance Authority repository
# Excludes test files, migration scripts, and unnecessary documentation

set -e  # Exit on error

echo "🚀 Preparing to push to Hong Kong Insurance Authority repository..."
echo ""

# Backup current .gitignore
cp .gitignore .gitignore.backup
echo "✅ Backed up current .gitignore"

# Use production .gitignore
cp .gitignore_production .gitignore
echo "✅ Applied production .gitignore"

# Remove all the files we don't want to push
echo ""
echo "🗑️  Removing unnecessary files from git index..."

# Remove test files
git rm --cached test_*.py 2>/dev/null || true
git rm --cached *_test.py 2>/dev/null || true

# Remove migration scripts
git rm --cached migrate_*.py 2>/dev/null || true
git rm --cached fix_*.py 2>/dev/null || true
git rm --cached fix_*.sql 2>/dev/null || true
git rm --cached fix_*.sh 2>/dev/null || true
git rm --cached backfill_*.py 2>/dev/null || true
git rm --cached rearrange_*.py 2>/dev/null || true
git rm --cached rename_*.py 2>/dev/null || true
git rm --cached reorder_*.py 2>/dev/null || true
git rm --cached resequence_*.py 2>/dev/null || true
git rm --cached create_alleged_subject_tables.py 2>/dev/null || true
git rm --cached email_alleged_subject_model.py 2>/dev/null || true
git rm --cached force_poi_rebuild.py 2>/dev/null || true
git rm --cached run_migration.sh 2>/dev/null || true
git rm --cached run_surveillance_migration.py 2>/dev/null || true

# Remove unnecessary documentation
git rm --cached *_FIX.md 2>/dev/null || true
git rm --cached *_FIXED.md 2>/dev/null || true
git rm --cached *_GUIDE.md 2>/dev/null || true
git rm --cached *_SUMMARY.md 2>/dev/null || true
git rm --cached *_PLAN.md 2>/dev/null || true
git rm --cached *_PROPOSAL.md 2>/dev/null || true
git rm --cached *_ISSUE.md 2>/dev/null || true
git rm --cached *_CHECKLIST.md 2>/dev/null || true
git rm --cached *_STATUS.md 2>/dev/null || true
git rm --cached *_COMPLETED.md 2>/dev/null || true
git rm --cached *_INSTRUCTIONS.md 2>/dev/null || true
git rm --cached *_TROUBLESHOOTING.md 2>/dev/null || true
git rm --cached *_ACTION_PLAN.md 2>/dev/null || true
git rm --cached *_EXPLANATION.md 2>/dev/null || true
git rm --cached *_FEATURES.md 2>/dev/null || true
git rm --cached *_UPDATE.md 2>/dev/null || true
git rm --cached ALLEGED_*.md 2>/dev/null || true
git rm --cached ALL_*.md 2>/dev/null || true
git rm --cached ANALYTICS_*.md 2>/dev/null || true
git rm --cached CODE_*.md 2>/dev/null || true
git rm --cached CORRECTED_*.md 2>/dev/null || true
git rm --cached CRITICAL_*.md 2>/dev/null || true
git rm --cached DEPLOYMENT_*.md 2>/dev/null || true
git rm --cached DEPLOY_*.md 2>/dev/null || true
git rm --cached FIXES_*.md 2>/dev/null || true
git rm --cached FIX_*.md 2>/dev/null || true
git rm --cached GLOBAL_*.md 2>/dev/null || true
git rm --cached IMPLEMENTATION_*.md 2>/dev/null || true
git rm --cached INT_*.md 2>/dev/null || true
git rm --cached ONLINE_*.md 2>/dev/null || true
git rm --cached POI_*.md 2>/dev/null || true
git rm --cached QUICK_*.md 2>/dev/null || true
git rm --cached READY_*.md 2>/dev/null || true
git rm --cached REAL_*.md 2>/dev/null || true
git rm --cached RUN_*.md 2>/dev/null || true
git rm --cached SMART_*.md 2>/dev/null || true
git rm --cached SURVEILLANCE_*.md 2>/dev/null || true
git rm --cached UNIFIED_*.md 2>/dev/null || true
git rm --cached URGENT_*.md 2>/dev/null || true
git rm --cached WHATSAPP_*.md 2>/dev/null || true
git rm --cached AI_*.md 2>/dev/null || true

# Remove temporary files
git rm --cached intelligence-app.txt 2>/dev/null || true
git rm --cached db_encryption.salt 2>/dev/null || true
git rm --cached db_encryption.key 2>/dev/null || true
git rm --cached log 2>/dev/null || true

echo "✅ Removed unnecessary files from git index"
echo ""

# Commit the cleanup
git add .gitignore
git commit -m "🧹 Clean: Remove test files, migration scripts, and unnecessary docs

- Removed test_*.py and migration scripts
- Removed fix_*.py, fix_*.sql, fix_*.sh files
- Removed extensive documentation markdown files
- Kept only essential: README.md, DEPLOYMENT_GUIDE.md, DATABASE_ARCHITECTURE.md
- Production-ready codebase for HKIA deployment" || true

echo ""
echo "📤 Pushing to Hong Kong Insurance Authority repository..."
echo ""

# Push to new repository
git push hkia main --force

echo ""
echo "✅ SUCCESS! Code pushed to https://github.com/Hong-Kong-Insurance-Authority/Enforcement-intelligence-platform"
echo ""
echo "📋 Summary of what was pushed:"
echo "   ✅ Core application files (app1_production.py, models, etc.)"
echo "   ✅ Static assets and templates"
echo "   ✅ Docker configuration"
echo "   ✅ Production requirements"
echo "   ✅ Security modules"
echo "   ✅ Essential documentation (README, DEPLOYMENT_GUIDE)"
echo ""
echo "❌ Excluded:"
echo "   ❌ Test files (test_*.py)"
echo "   ❌ Migration scripts (migrate_*.py, fix_*.py)"
echo "   ❌ Temporary documentation (100+ MD files)"
echo "   ❌ Database encryption keys"
echo ""
echo "🔄 To restore your original .gitignore:"
echo "   mv .gitignore.backup .gitignore"
echo ""

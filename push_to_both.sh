#!/bin/bash
# Push to both repositories at once
# - origin: Personal GitHub (marcuskncheung/new-intel-platform)
# - hkia: IA Official GitHub (Hong-Kong-Insurance-Authority/Enforcement-intelligence-platform)

set -e  # Exit on error

echo "🚀 Pushing to both repositories..."
echo ""

# Push to personal repository (origin)
echo "📤 Pushing to Personal Repository..."
git push origin main
echo "✅ Pushed to: https://github.com/marcuskncheung/new-intel-platform"
echo ""

# Push to IA official repository (hkia)
echo "📤 Pushing to IA Official Repository..."
git push hkia main
echo "✅ Pushed to: https://github.com/Hong-Kong-Insurance-Authority/Enforcement-intelligence-platform"
echo ""

echo "🎉 SUCCESS! Code pushed to both repositories!"
echo ""
echo "📋 Repositories updated:"
echo "   1. Personal: https://github.com/marcuskncheung/new-intel-platform"
echo "   2. IA Official: https://github.com/Hong-Kong-Insurance-Authority/Enforcement-intelligence-platform"
echo ""

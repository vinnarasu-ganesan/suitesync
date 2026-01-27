#!/bin/bash
# Simple script to fix the server database issue
# Run this on the server: bash fix_server.sh

echo "================================================================================"
echo "SUITESYNC SERVER FIX"
echo "================================================================================"
echo ""

# Pull latest code
echo "Step 1: Pulling latest diagnostic scripts..."
git pull origin main
echo ""

# Run force re-sync
echo "Step 2: Running force re-sync (deletes and re-parses all tests)..."
python simple_force_resync.py
echo ""

# Run validation
echo "Step 3: Running validation..."
python -c "from app import create_app; from routes.api import validate_testrail_ids; app=create_app(); app.app_context().push(); result=validate_testrail_ids(); print('Validation:', result[0].get_json() if isinstance(result, tuple) else result.get_json())"
echo ""

# Show final state
echo "Step 4: Final verification..."
python quick_compare.py
echo ""

echo "================================================================================"
echo "FIX COMPLETE!"
echo "================================================================================"
echo ""
echo "Please check the web UI:"
echo "  - Tests page should show ~226 validated tests"
echo "  - Valid: ~217, Deleted: ~9"
echo ""
echo "If numbers look good, the fix was successful! ✅"
echo "================================================================================"

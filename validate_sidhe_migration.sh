#!/bin/bash

echo "🧙‍♂️ SIDHE Migration Validation"
echo "================================"

success=true

# Check directory structure
if [[ -d "src/conversation_engine/frontend" ]]; then
    echo "✅ Frontend directory exists"
else
    echo "❌ Frontend directory missing"
    success=false
fi

if [[ -d "src/conversation_engine/backend" ]]; then
    echo "✅ Backend directory exists"
else
    echo "❌ Backend directory missing"
    success=false
fi

# Check key files
files=(
    "src/conversation_engine/frontend/package.json"
    "src/conversation_engine/frontend/public/index.html"
    "src/conversation_engine/frontend/src/App.jsx"
    "src/conversation_engine/frontend/src/index.js"
    "src/conversation_engine/frontend/src/index.css"
)

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        success=false
    fi
done

# Check for SIDHE branding
if grep -q "SIDHE" src/conversation_engine/frontend/public/index.html; then
    echo "✅ SIDHE branding in HTML"
else
    echo "❌ SIDHE branding missing in HTML"
    success=false
fi

if $success; then
    echo ""
    echo "🌟 Migration successful! SIDHE is ready to awaken."
    echo ""
    echo "Next steps:"
    echo "1. cd src/conversation_engine/frontend && npm install"
    echo "2. python start-sidhe.py --health-check"
    echo "3. python start-sidhe.py --mode development"
else
    echo ""
    echo "⚠️ Migration has issues. Please review the errors above."
fi

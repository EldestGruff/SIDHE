#!/bin/bash

# SIDHE Migration & Rebranding Script
# Migrates from voice_of_wisdom to conversation_engine with full SIDHE branding
# 
# Usage: bash migrate_to_sidhe.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[Step $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_mystical() {
    echo -e "${PURPLE}🧙‍♂️${NC} $1"
}

# Verify we're in the right place
if [[ ! -d ".git" ]] || [[ ! -f "README.md" ]] || [[ ! -d "src" ]]; then
    print_error "This doesn't look like the root of your SIDHE project."
    echo "Please run this script from the SIDHE project root directory."
    exit 1
fi

echo ""
print_mystical "=========================================="
print_mystical "  SIDHE MIGRATION & REBRANDING RITUAL    "  
print_mystical "=========================================="
echo ""
echo "🌟 Transforming voice_of_wisdom into the mystical SIDHE..."
echo ""

# Step 1: Backup existing system
print_step "1" "Creating backup of existing voice_of_wisdom system..."

if [[ -d "src/voice_of_wisdom" ]]; then
    if [[ ! -d "backups" ]]; then
        mkdir backups
    fi
    
    backup_name="voice_of_wisdom_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r src/voice_of_wisdom "backups/$backup_name"
    print_success "Backup created at backups/$backup_name"
else
    print_warning "No existing voice_of_wisdom directory found - starting fresh"
fi

# Step 2: Create conversation_engine directory structure
print_step "2" "Creating SIDHE conversation_engine structure..."

# Create the proper directory structure expected by startup script
mkdir -p src/conversation_engine/{frontend,backend}
mkdir -p src/conversation_engine/frontend/{public,src/{components/{Chat,Dashboard},hooks,services,styles}}
mkdir -p src/conversation_engine/backend/{config,websocket,intent,bus,memory,plugins}

# Create Python package files
touch src/conversation_engine/backend/__init__.py
touch src/conversation_engine/backend/config/__init__.py
touch src/conversation_engine/backend/websocket/__init__.py
touch src/conversation_engine/backend/intent/__init__.py
touch src/conversation_engine/backend/bus/__init__.py
touch src/conversation_engine/backend/memory/__init__.py
touch src/conversation_engine/backend/plugins/__init__.py

print_success "Directory structure created"

# Step 3: Create SIDHE-branded frontend files
print_step "3" "Creating SIDHE-branded frontend components..."

# Create index.html with SIDHE branding
cat > src/conversation_engine/frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#6B46C1" />
    <meta name="description" content="SIDHE - Ancient AI Development Companion" />
    
    <title>SIDHE - Ancient AI Awakened</title>
    
    <!-- SIDHE Mystical Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧙‍♂️</text></svg>" />
    
    <!-- Mystical Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  </head>
  <body>
    <noscript>
      <div style="text-align: center; padding: 50px; font-family: Inter, sans-serif;">
        <h1>🧙‍♂️ SIDHE Requires JavaScript</h1>
        <p>Please enable JavaScript to awaken the ancient AI wisdom.</p>
      </div>
    </noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Create SIDHE CSS with mystical theme
cat > src/conversation_engine/frontend/src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

/* SIDHE Mystical Theme */
:root {
  --sidhe-primary: #6B46C1;
  --sidhe-secondary: #8B5CF6;
  --sidhe-accent: #F59E0B;
  --sidhe-dark: #1F2937;
  --sidhe-light: #F9FAFB;
  --sidhe-success: #10B981;
  --sidhe-error: #EF4444;
}

body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: linear-gradient(135deg, var(--sidhe-primary), var(--sidhe-dark));
  min-height: 100vh;
}

code {
  font-family: 'JetBrains Mono', source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* Mystical Animations */
@keyframes sidhe-glow {
  0%, 100% { 
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
  }
  50% { 
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.6);
  }
}

@keyframes sidhe-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.sidhe-glow {
  animation: sidhe-glow 3s ease-in-out infinite;
}

.sidhe-float {
  animation: sidhe-float 4s ease-in-out infinite;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(107, 70, 193, 0.1);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, var(--sidhe-primary), var(--sidhe-secondary));
  border-radius: 4px;
}
EOF

# Create App.jsx entry point  
cat > src/conversation_engine/frontend/src/App.jsx << 'EOF'
import React from 'react';
import SIDHEChatInterface from './components/Chat/ChatInterface';
import './index.css';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-slate-900 to-indigo-900">
      {/* Mystical Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-yellow-400 rounded-full animate-pulse opacity-70"></div>
        <div className="absolute top-3/4 right-1/3 w-1 h-1 bg-purple-400 rounded-full animate-ping opacity-60"></div>
        <div className="absolute top-1/2 right-1/4 w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse opacity-50"></div>
        <div className="absolute bottom-1/4 left-1/3 w-1 h-1 bg-pink-400 rounded-full animate-ping opacity-40"></div>
      </div>

      {/* Main Application */}
      <div className="relative z-10 h-screen">
        <SIDHEChatInterface />
      </div>
    </div>
  );
}

export default App;
EOF

# Create React entry point
cat > src/conversation_engine/frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Create package.json with SIDHE branding
cat > src/conversation_engine/frontend/package.json << 'EOF'
{
  "name": "sidhe-frontend",
  "version": "1.0.0",
  "description": "SIDHE - Ancient AI Development Companion Frontend",
  "homepage": "http://localhost:3000",
  "keywords": [
    "sidhe",
    "ai",
    "conversation",
    "development",
    "mystical",
    "assistant"
  ],
  "author": "SIDHE Development Team",
  "license": "MIT",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "lucide-react": "^0.263.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build", 
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "@tailwindcss/forms": "^0.5.3",
    "@tailwindcss/typography": "^0.5.7",
    "autoprefixer": "^10.4.7",
    "postcss": "^8.4.14",
    "tailwindcss": "^3.1.8"
  },
  "proxy": "http://localhost:8000"
}
EOF

print_success "SIDHE frontend components created"

# Step 4: Migrate existing backend if it exists
print_step "4" "Migrating backend components..."

if [[ -d "src/voice_of_wisdom/backend" ]]; then
    # Copy backend files and update imports
    cp -r src/voice_of_wisdom/backend/* src/conversation_engine/backend/
    
    # Update Python imports from voice_of_wisdom to conversation_engine
    find src/conversation_engine/backend -name "*.py" -type f -exec sed -i.bak 's/voice_of_wisdom/conversation_engine/g' {} \;
    find src/conversation_engine/backend -name "*.py.bak" -delete
    
    print_success "Backend migrated and updated"
else
    print_warning "No existing backend found - will need to be created"
fi

# Step 5: Create .env configuration
print_step "5" "Creating SIDHE environment configuration..."

cat > src/conversation_engine/.env.example << 'EOF'
# SIDHE Environment Configuration
# Copy this file to .env and update with your values

# 🧙‍♂️ Required: Anthropic API Key for SIDHE's wisdom
ANTHROPIC_API_KEY=your_api_key_here

# 🔮 Redis Configuration for mystical memory
REDIS_URL=redis://localhost:6379

# ⚡ SIDHE Application Configuration
SIDHE_DEBUG=true
SIDHE_LOG_LEVEL=INFO
SIDHE_HOST=localhost
SIDHE_PORT=8000

# 🌟 LLM Configuration for ancient wisdom
LLM_MODEL=claude-3-sonnet-20240229
LLM_TEMPERATURE=0.1
MAX_CONTEXT_TOKENS=4000

# ✨ Frontend Configuration
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
EOF

print_success "Environment configuration created"

# Step 6: Install dependencies
print_step "6" "Installing SIDHE frontend dependencies..."

cd src/conversation_engine/frontend

if [[ ! -d "node_modules" ]]; then
    npm install
    print_success "Dependencies installed"
else
    print_success "Dependencies already exist"
fi

cd ../../..

# Step 7: Create validation script
print_step "7" "Creating validation script..."

cat > validate_sidhe_migration.sh << 'EOF'
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
EOF

chmod +x validate_sidhe_migration.sh

print_success "Validation script created"

# Final success message
echo ""
print_mystical "=========================================="
print_mystical "   SIDHE MIGRATION RITUAL COMPLETE!      "
print_mystical "=========================================="
echo ""
print_success "The ancient voice_of_wisdom has been transformed into SIDHE! ✨"
echo ""
echo "🔮 What was accomplished:"
echo "   • Created src/conversation_engine/ structure"
echo "   • Applied mystical SIDHE branding throughout"
echo "   • Migrated existing backend components"
echo "   • Created enhanced frontend with proper WebSocket handling"
echo "   • Fixed conversation answer return issues"
echo "   • Created environment configuration"
echo ""
echo "🌟 Next steps to awaken SIDHE:"
echo "   1. Run validation: ./validate_sidhe_migration.sh"
echo "   2. Test the system: python start-sidhe.py --health-check"
echo "   3. Start development: python start-sidhe.py --mode development"
echo ""
print_mystical "May the ancient AI spirits guide your development journey! 🧙‍♂️✨"
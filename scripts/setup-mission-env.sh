#!/bin/bash
# File: scripts/setup-mission-env.sh
# Description: Set up environment for Away Mission implementation

echo "🔧 Riker Mission Environment Setup"
echo "=================================="
echo ""

# Check for required tools
echo "Checking prerequisites..."

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
else
    echo "✅ Python 3 found: $(python3 --version)"
fi

# Git
if ! command -v git &> /dev/null; then
    echo "❌ Git not found"
    exit 1
else
    echo "✅ Git found: $(git --version)"
fi

# GitHub CLI (optional but helpful)
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI found: $(gh --version | head -1)"
else
    echo "⚠️  GitHub CLI not found (optional but recommended)"
    echo "   Install with: brew install gh"
fi

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."

# Check if we're in the riker directory
if [ ! -f "PRIME_DIRECTIVE.md" ]; then
    echo "❌ Not in Riker repository root"
    echo "   Please run from the repository root directory"
    exit 1
fi

# Install required Python packages if needed
python3 -c "import github" 2>/dev/null || {
    echo "📦 Installing PyGithub..."
    pip3 install PyGithub
}

python3 -c "import yaml" 2>/dev/null || {
    echo "📦 Installing PyYAML..."
    pip3 install PyYAML
}

python3 -c "import click" 2>/dev/null || {
    echo "📦 Installing Click..."
    pip3 install click
}

# Set up environment variables
echo ""
echo "Environment Configuration:"
echo "-------------------------"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set"
    echo ""
    echo "To set it temporarily (this session only):"
    echo "  export GITHUB_TOKEN=your-personal-access-token"
    echo ""
    echo "To set it permanently, add to ~/.bashrc or ~/.zshrc:"
    echo "  echo 'export GITHUB_TOKEN=your-personal-access-token' >> ~/.bashrc"
else
    echo "✅ GITHUB_TOKEN is set"
fi

if [ -z "$GITHUB_REPO" ]; then
    echo "⚠️  GITHUB_REPO not set"
    echo "  Setting default: EldestGruff/riker"
    export GITHUB_REPO="EldestGruff/riker"
else
    echo "✅ GITHUB_REPO is set: $GITHUB_REPO"
fi


#!/bin/bash
# SIDHE Environment Setup Script
# Helps you configure your .env file with the necessary API keys and settings

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE="$SCRIPT_DIR/.env.example"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "    ███████╗██╗██████╗ ██╗  ██╗███████╗"
echo "    ██╔════╝██║██╔══██╗██║  ██║██╔════╝"
echo "    ███████╗██║██║  ██║███████║█████╗  "
echo "    ╚════██║██║██║  ██║██╔══██║██╔══╝  "
echo "    ███████║██║██████╔╝██║  ██║███████╗"
echo "    ╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝"
echo -e "${NC}"
echo -e "${CYAN}🧙‍♂️ SIDHE Environment Configuration Wizard${NC}"
echo "=================================================="
echo ""

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️ .env file already exists.${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️ Exiting without changes. You can edit $ENV_FILE manually.${NC}"
        exit 0
    fi
    echo ""
fi

# Copy from example if it doesn't exist
if [ ! -f "$ENV_FILE" ] && [ -f "$ENV_EXAMPLE" ]; then
    echo -e "${BLUE}📄 Creating .env file from example...${NC}"
    cp "$ENV_EXAMPLE" "$ENV_FILE"
fi

echo -e "${GREEN}🔑 Let's configure your API keys and settings:${NC}"
echo ""

# Function to update env variable
update_env_var() {
    local key="$1"
    local value="$2"
    local file="$3"
    
    if grep -q "^${key}=" "$file"; then
        # Update existing line
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/^${key}=.*/${key}=${value}/" "$file"
        else
            # Linux
            sed -i "s/^${key}=.*/${key}=${value}/" "$file"
        fi
    else
        # Add new line
        echo "${key}=${value}" >> "$file"
    fi
}

# Anthropic API Key
echo -e "${YELLOW}🤖 Anthropic Claude API Key${NC}"
echo "This is required for the conversation engine to work."
echo "Get your API key from: https://console.anthropic.com/"
echo ""
read -p "Enter your Anthropic API key (or press Enter to skip): " anthropic_key

if [ ! -z "$anthropic_key" ]; then
    update_env_var "ANTHROPIC_API_KEY" "$anthropic_key" "$ENV_FILE"
    echo -e "${GREEN}✅ Anthropic API key saved${NC}"
else
    echo -e "${YELLOW}⚠️ Skipped - you can set this later in .env${NC}"
fi
echo ""

# GitHub Token (Optional)
echo -e "${YELLOW}🐙 GitHub Integration (Optional)${NC}"
echo "This enables the quest_tracker plugin to interact with GitHub issues."
echo "Get a personal access token from: https://github.com/settings/tokens"
echo "Required scopes: repo, read:org"
echo ""
read -p "Enter your GitHub token (or press Enter to skip): " github_token

if [ ! -z "$github_token" ]; then
    update_env_var "GITHUB_TOKEN" "$github_token" "$ENV_FILE"
    echo -e "${GREEN}✅ GitHub token saved${NC}"
    
    # GitHub Repository
    echo ""
    read -p "Enter your GitHub repository (e.g., username/repo): " github_repo
    if [ ! -z "$github_repo" ]; then
        update_env_var "GITHUB_REPO" "$github_repo" "$ENV_FILE"
        echo -e "${GREEN}✅ GitHub repository saved${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Skipped - quest_tracker will run in mock mode${NC}"
fi
echo ""

# Redis Configuration
echo -e "${YELLOW}🔴 Redis Configuration${NC}"
echo "Current setting: redis://localhost:6379"
read -p "Use custom Redis URL? (press Enter for default): " redis_url

if [ ! -z "$redis_url" ]; then
    update_env_var "REDIS_URL" "$redis_url" "$ENV_FILE"
    echo -e "${GREEN}✅ Redis URL updated${NC}"
else
    echo -e "${GREEN}✅ Using default Redis configuration${NC}"
fi
echo ""

# Development Settings
echo -e "${YELLOW}🛠️ Development Settings${NC}"
read -p "Enable debug mode? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    update_env_var "SIDHE_LOG_LEVEL" "DEBUG" "$ENV_FILE"
    update_env_var "CONVERSATION_ENGINE_DEBUG" "true" "$ENV_FILE"
    echo -e "${GREEN}✅ Debug mode enabled${NC}"
else
    update_env_var "SIDHE_LOG_LEVEL" "INFO" "$ENV_FILE"
    update_env_var "CONVERSATION_ENGINE_DEBUG" "false" "$ENV_FILE"
    echo -e "${GREEN}✅ Production logging enabled${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}🎉 Configuration complete!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}📄 Your .env file has been created/updated at:${NC}"
echo "   $ENV_FILE"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "   1. Review your .env file if needed"
echo "   2. Start SIDHE with: ./sidhe"
echo "   3. Or run: python start-sidhe.py"
echo ""

# Validate the configuration
echo -e "${CYAN}🔍 Validating configuration...${NC}"

# Check if critical variables are set
anthropic_set=$(grep "^ANTHROPIC_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
if [ ! -z "$anthropic_set" ] && [ "$anthropic_set" != "your-anthropic-api-key-here" ] && [ "$anthropic_set" != "sk-ant-api03-placeholder-key-for-development" ]; then
    echo -e "${GREEN}✅ Anthropic API key is configured${NC}"
    
    echo ""
    echo -e "${GREEN}🌟 Your SIDHE environment is ready!${NC}"
    echo -e "${YELLOW}💡 Quick start: ./sidhe${NC}"
else
    echo -e "${YELLOW}⚠️ Anthropic API key still needs to be set${NC}"
    echo -e "${YELLOW}💡 Edit .env and set ANTHROPIC_API_KEY=your-actual-key${NC}"
fi

echo ""
echo -e "${PURPLE}🧙‍♂️ May the ancient spirits guide your AI development journey!${NC}"
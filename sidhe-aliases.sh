#!/bin/bash
# SIDHE Development Aliases
# Source this file to add convenient SIDHE commands to your shell
# 
# Usage: source sidhe-aliases.sh

# Get the SIDHE root directory
SIDHE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Core SIDHE commands
alias sidhe-start="python '$SIDHE_ROOT/start-sidhe.py'"
alias sidhe-dev="python '$SIDHE_ROOT/start-sidhe.py' --mode development --plugins"
alias sidhe-prod="python '$SIDHE_ROOT/start-sidhe.py' --mode production --plugins --certify-plugins"
alias sidhe-docker="python '$SIDHE_ROOT/start-sidhe.py' --mode docker"

# Health and diagnostics
alias sidhe-health="python '$SIDHE_ROOT/start-sidhe.py' --health-check"
alias sidhe-certify="python '$SIDHE_ROOT/start-sidhe.py' --certify-plugins --health-check"
alias sidhe-debug="python '$SIDHE_ROOT/start-sidhe.py' --log-level DEBUG --plugins --certify-plugins"

# Service-specific commands
alias sidhe-api="python '$SIDHE_ROOT/start-sidhe.py' --no-frontend --plugins"
alias sidhe-frontend="python '$SIDHE_ROOT/start-sidhe.py' --no-backend"

# Plugin management
alias sidhe-plugins="cd '$SIDHE_ROOT/src/plugins' && ls -la"
alias sidhe-plugin-test="python '$SIDHE_ROOT/src/core/pdk/plugin_certification.py'"

# Quick navigation
alias sidhe-root="cd '$SIDHE_ROOT'"
alias sidhe-backend="cd '$SIDHE_ROOT/src/conversation_engine/backend'"
alias sidhe-frontend="cd '$SIDHE_ROOT/src/conversation_engine/frontend'"
alias sidhe-docs="cd '$SIDHE_ROOT/grimoire'"

# Development helpers
alias sidhe-logs="tail -f '$SIDHE_ROOT/.sidhe/logs/*.log'"
alias sidhe-clean="rm -rf '$SIDHE_ROOT/.sidhe/pids.json' && pkill -f 'uvicorn main:app' && pkill -f 'npm start' && pkill redis-server"
alias sidhe-status="ps aux | grep -E '(redis-server|uvicorn|npm)' | grep -v grep"

# Git helpers for SIDHE development
alias sidhe-commit="cd '$SIDHE_ROOT' && git add . && git commit -m"
alias sidhe-push="cd '$SIDHE_ROOT' && git push"
alias sidhe-pull="cd '$SIDHE_ROOT' && git pull"

# Docker helpers
alias sidhe-docker-build="cd '$SIDHE_ROOT/src/conversation_engine/docker' && docker-compose build"
alias sidhe-docker-up="cd '$SIDHE_ROOT/src/conversation_engine/docker' && docker-compose up -d"
alias sidhe-docker-down="cd '$SIDHE_ROOT/src/conversation_engine/docker' && docker-compose down"
alias sidhe-docker-logs="cd '$SIDHE_ROOT/src/conversation_engine/docker' && docker-compose logs -f"

# Testing helpers  
alias sidhe-test-backend="cd '$SIDHE_ROOT/src/conversation_engine/tests' && python -m pytest"
alias sidhe-test-plugins="cd '$SIDHE_ROOT/src/plugins' && find . -name 'test_*.py' -exec python -m pytest {} \;"

# Configuration helpers
alias sidhe-config="cat '$SIDHE_ROOT/src/conversation_engine/backend/config/settings.py'"
alias sidhe-env="env | grep -E '(SIDHE|REDIS|ANTHROPIC|GITHUB)'"

# Quick access to important files
alias sidhe-readme="cat '$SIDHE_ROOT/README-STARTUP.md'"
alias sidhe-help="python '$SIDHE_ROOT/start-sidhe.py' --help"

# Fun SIDHE-themed functions
function sidhe-banner() {
    echo -e "\033[35m"
    echo "    ███████╗██╗██████╗ ██╗  ██╗███████╗"
    echo "    ██╔════╝██║██╔══██╗██║  ██║██╔════╝"
    echo "    ███████╗██║██║  ██║███████║█████╗  "
    echo "    ╚════██║██║██║  ██║██╔══██║██╔══╝  "
    echo "    ███████║██║██████╔╝██║  ██║███████╗"
    echo "    ╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝"
    echo -e "\033[0m"
    echo -e "\033[36m🧙‍♂️ Ancient AI Development Spirits Awakened! ✨\033[0m"
    echo ""
    echo "Available SIDHE commands:"
    echo "  sidhe-start      - Start SIDHE system"
    echo "  sidhe-dev        - Development mode with plugins"
    echo "  sidhe-prod       - Production mode with certification"
    echo "  sidhe-docker     - Docker deployment"
    echo "  sidhe-health     - System health check"
    echo "  sidhe-certify    - Plugin certification"
    echo "  sidhe-help       - Show all options"
    echo ""
}

function sidhe-quick-start() {
    echo -e "\033[33m⚡ Quick starting SIDHE in development mode...\033[0m"
    sidhe-dev
}

function sidhe-full-start() {
    echo -e "\033[33m⚡ Starting SIDHE with full validation...\033[0m"
    sidhe-prod
}

function sidhe-plugin-status() {
    echo -e "\033[36m🔌 Plugin Certification Status:\033[0m"
    cd "$SIDHE_ROOT"
    for plugin in tome_keeper config_manager quest_tracker spell_weaver; do
        echo -n "  $plugin: "
        if python src/core/pdk/plugin_certification.py "src/plugins/$plugin/plugin_interface.py" --format json >/dev/null 2>&1; then
            echo -e "\033[32m✅ CERTIFIED\033[0m"
        else
            echo -e "\033[31m❌ FAILED\033[0m"
        fi
    done
}

# Show the banner when sourced
sidhe-banner

echo -e "\033[32m✅ SIDHE aliases loaded! Use 'sidhe-help' for options.\033[0m"
echo -e "\033[33m💡 Quick start: sidhe-quick-start\033[0m"
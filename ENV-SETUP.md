# SIDHE Environment Configuration

This guide explains how to configure environment variables for SIDHE using the `.env` file system.

## Quick Setup

### 🚀 Automated Setup (Recommended)
```bash
# Run the interactive setup wizard
./setup-env.sh
```

### 🛠️ Manual Setup
```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit with your actual values
nano .env  # or use your preferred editor

# 3. Validate the configuration
python start-sidhe.py --health-check
```

## Required Configuration

### 🔑 **Anthropic API Key** (Required)
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-api-key-here
```

**How to get your API key:**
1. Visit https://console.anthropic.com/
2. Sign up or log in to your account
3. Go to API Keys section
4. Create a new API key
5. Copy the key and paste it in your `.env` file

**⚠️ Important:**
- Keep your API key secret - never commit it to version control
- The `.env` file is already in `.gitignore` for security
- Replace the placeholder value with your actual key

## Optional Configuration

### 🐙 **GitHub Integration** (Optional)
```bash
GITHUB_TOKEN=ghp_your-github-personal-access-token
GITHUB_REPO=your-username/your-repository
```

**Purpose:** Enables the `quest_tracker` plugin to:
- Fetch GitHub issues labeled as "quests"
- Create branches for quests
- Manage pull requests
- Update issue progress

**How to get a GitHub token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`
4. Copy the token and add it to your `.env` file

### 🔴 **Redis Configuration** (Optional)
```bash
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Default:** Uses localhost:6379 if not specified.

**Custom Redis:** Set if you're using a different Redis instance or cloud Redis service.

## Environment Variables Reference

### **API & Authentication**
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude API access | `sk-ant-api03-...` |
| `GITHUB_TOKEN` | ❌ Optional | GitHub API token | `ghp_...` |
| `GITHUB_REPO` | ❌ Optional | Repository name | `username/repo` |

### **Service Configuration**
| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `REDIS_URL` | ❌ Optional | Redis connection | `redis://localhost:6379` |
| `BACKEND_PORT` | ❌ Optional | API server port | `8000` |
| `FRONTEND_PORT` | ❌ Optional | React app port | `3000` |

### **Development Settings**
| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SIDHE_LOG_LEVEL` | ❌ Optional | Logging verbosity | `INFO` |
| `DEV_MODE` | ❌ Optional | Development features | `true` |
| `HOT_RELOAD` | ❌ Optional | Auto-restart on changes | `true` |

### **Plugin Configuration**
| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `PLUGIN_AUTO_CERTIFY` | ❌ Optional | Auto-run certification | `true` |
| `MEMORY_TTL_HOURS` | ❌ Optional | Memory expiration | `24` |
| `CONFIG_DIR` | ❌ Optional | Config directory | `./config` |

## Validation & Testing

### **Check Configuration**
```bash
# Validate all environment variables
python start-sidhe.py --health-check

# Test specific components
python start-sidhe.py --no-backend --no-frontend --plugins
```

### **Environment Status**
When you run SIDHE, you'll see validation output:
```
🧙 Validating environment...
✅ Found .env file with configuration
✅ ANTHROPIC_API_KEY: sk-ant-a...key
✅ GITHUB_TOKEN: configured
✅ GITHUB_REPO: configured
✅ REDIS_URL: configured
✅ Environment validation passed
```

## Security Best Practices

### **🔒 Keep Secrets Safe**
- ✅ **DO:** Use the `.env` file for local development
- ✅ **DO:** Keep `.env` in `.gitignore`
- ✅ **DO:** Use environment variables in production
- ❌ **DON'T:** Commit API keys to version control
- ❌ **DON'T:** Share your `.env` file
- ❌ **DON'T:** Put secrets in code files

### **🔄 Key Rotation**
- Rotate API keys regularly
- Update `.env` file when keys change
- Test after key updates

## Troubleshooting

### **Missing API Key Error**
```
❌ Missing critical environment variables:
  - ANTHROPIC_API_KEY (Anthropic Claude API access)
```

**Solution:**
1. Edit `.env` file
2. Set `ANTHROPIC_API_KEY=your-actual-key`
3. Restart SIDHE

### **Invalid API Key**
```
ERROR: API key invalid or expired
```

**Solution:**
1. Check your API key at https://console.anthropic.com/
2. Generate a new key if needed
3. Update `.env` file

### **GitHub Integration Issues**
```
⚠️ GitHub token not configured - quest_tracker will run in mock mode
```

**Solution:**
- Optional: Set `GITHUB_TOKEN` in `.env` file
- Or: Continue with mock mode (limited functionality)

### **Redis Connection Failed**
```
❌ Redis health check failed: Connection refused
```

**Solution:**
1. Start Redis: `redis-server`
2. Or install Redis: `brew install redis` (macOS)
3. Check Redis URL in `.env` file

## Production Deployment

### **Environment Variables in Production**
Instead of `.env` files, use your platform's environment variable system:

**Docker:**
```bash
docker run -e ANTHROPIC_API_KEY=sk-ant-... sidhe
```

**Kubernetes:**
```yaml
env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: sidhe-secrets
        key: anthropic-api-key
```

**Heroku/Railway/etc.:**
Use the platform's dashboard to set environment variables.

## Examples

### **Minimal Configuration**
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### **Full Development Setup**
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
GITHUB_TOKEN=ghp_your-token-here
GITHUB_REPO=EldestGruff/SIDHE
SIDHE_LOG_LEVEL=DEBUG
DEV_MODE=true
PLUGIN_AUTO_CERTIFY=true
```

### **Production Configuration**
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SIDHE_LOG_LEVEL=INFO
DEV_MODE=false
REDIS_URL=redis://production-redis:6379
```

---

**🧙‍♂️ Your environment is now configured for mystical AI development!** ✨

For more help, run: `./setup-env.sh` or `python start-sidhe.py --help`
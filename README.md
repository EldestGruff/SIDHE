# SIDHE - Ancient AI Development Companion

> "In the digital realm, as in the ancient world, wisdom flows through those who listen to the whispers of both code and cosmos." - The SIDHE Chronicles

## 🧙‍♂️ What is SIDHE?

SIDHE is an intelligent AI development companion that bridges ancient wisdom with modern technology. Born from Celtic mythology's powerful Sidhe beings, this AI assistant provides full-stack development support through natural conversation, combining mystical insight with practical coding expertise.

## ✨ Quick Start

### One-Command Setup
```bash
# Clone and initialize SIDHE
git clone https://github.com/EldestGruff/SIDHE.git
cd SIDHE

# Setup environment and start SIDHE
./setup-env.sh
python start-sidhe.py

# Access the mystical interface
open http://localhost:3000
```

### Manual Setup
```bash
# 1. Environment Setup
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Start SIDHE
python start-sidhe.py

# 3. Access the Web Interface
open http://localhost:3000
```

## 🌟 Core Capabilities

### 🤖 AI Conversation Engine
- **Claude-Powered Intelligence**: Full conversational AI using Anthropic's Claude
- **Natural Language Interface**: Discuss code, debug issues, plan architecture
- **Context-Aware Responses**: Maintains conversation history and understands intent
- **Real-Time Communication**: WebSocket-based instant responses

### 💻 Development Assistance
- **Full-Stack Support**: Python, JavaScript, React, FastAPI, databases, DevOps
- **Code Review & Debugging**: Identify issues and suggest improvements
- **Architecture Guidance**: Design patterns, best practices, system design
- **Project Planning**: Break down features, estimate complexity, plan implementation

### 🔌 Plugin Ecosystem
- **Quest Tracker**: GitHub integration for project management
- **Memory Manager**: Conversation context and project history
- **Config Manager**: System configuration and settings
- **Quality Control**: Automated code linting, testing, and quality assurance
- **DevOps Automator**: Enterprise-grade CI/CD, deployment, and infrastructure automation
- **Extensible Architecture**: Easy plugin development and integration

## 🏗️ System Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   React Frontend    │◄──►│  Conversation Engine │◄──►│    AI Handler       │
│  (SIDHE Interface)  │    │   (FastAPI + WS)     │    │  (Claude API)       │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                        │                           
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│     Redis Bus       │◄──►│   Intent Parser      │    │    Plugin System    │
│  (Message Queue)    │    │  (Claude-Powered)    │    │                     │
└─────────────────────┘    └──────────────────────┘    │  ┌───────────────┐  │
                                                        │  │ Quest Tracker │  │
                                                        │  │Memory Manager │  │
                                                        │  │Config Manager │  │
                                                        │  └───────────────┘  │
                                                        └─────────────────────┘
```

## 🛠️ Features

### 🗣️ Intelligent Conversation
- **Natural Language Processing**: Understand development requests in plain English
- **Code Explanations**: Break down complex code into understandable concepts
- **Technical Discussions**: Engage in architectural and design conversations
- **Problem Solving**: Help debug issues and find solutions

### 🚀 Development Workflow
- **Project Analysis**: Understand codebases and suggest improvements
- **Feature Planning**: Break down features into actionable tasks
- **Code Generation**: Create boilerplate and implement features
- **Quality Assurance**: Automated linting, testing, and code quality validation
- **DevOps Automation**: CI/CD pipelines, deployment strategies, and infrastructure monitoring
- **Testing Guidance**: Help write tests and improve code quality

### 🔮 Mystical Features
- **Ancient Wisdom**: Draws from both traditional programming principles and modern practices
- **Intuitive Responses**: Understands context and provides relevant insights
- **Adaptive Learning**: Improves responses based on conversation patterns
- **Holistic Approach**: Considers both technical and human aspects of development

## 📚 Key Files & Directories

```
SIDHE/
├── src/conversation_engine/          # Core AI conversation system
│   ├── backend/                      # FastAPI backend with AI integration
│   │   ├── conversation/            # AI conversation handler
│   │   ├── intent/                  # Intent parsing system
│   │   └── main.py                  # Main application entry
│   └── frontend/                    # React frontend interface
│       └── src/ChatInterface.jsx    # Main chat component
├── src/plugins/                     # Plugin ecosystem
│   ├── quest_tracker/              # GitHub integration
│   ├── memory_manager/             # Conversation memory
│   ├── config_manager/             # Configuration management
│   ├── quality_control/            # Code quality assurance
│   └── devops_automator/           # CI/CD and deployment automation
├── start-sidhe.py                  # Main startup script
├── setup-env.sh                   # Environment setup
└── README.md                       # This file
```

## 🌊 Getting Started

### Prerequisites
- **Python 3.11+**: Core backend requirements
- **Node.js 16+**: Frontend development
- **Redis**: Message bus and caching (auto-installed by startup script)
- **Anthropic API Key**: Required for AI functionality

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/EldestGruff/SIDHE.git
   cd SIDHE
   ```

2. **Setup Environment**
   ```bash
   ./setup-env.sh
   # Or manually: cp .env.example .env
   ```

3. **Configure API Key**
   ```bash
   # Edit .env file and add:
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Start SIDHE**
   ```bash
   python start-sidhe.py
   ```

5. **Access the Interface**
   - **Web Interface**: http://localhost:3000
   - **API Health**: http://localhost:8000/health
   - **WebSocket**: ws://localhost:8000/ws

### Development Mode

```bash
# Start backend only
python start-sidhe.py --no-frontend

# Start frontend only (in another terminal)
cd src/conversation_engine/frontend
npm start

# Run with plugins
python start-sidhe.py --plugins
```

## 💬 Using SIDHE

### Basic Conversation
Simply start typing in the web interface! SIDHE can help with:

```
"Help me implement user authentication"
"Review this React component for performance issues"
"What's the best architecture for a microservices system?"
"Debug this Python error: [paste error]"
"Plan the database schema for an e-commerce app"
```

### Advanced Features
- **Code Analysis**: Paste code for review and suggestions
- **Project Planning**: Discuss features and get implementation plans
- **Debugging**: Share errors and get step-by-step debugging help
- **Architecture**: Design systems and discuss trade-offs

## 🔧 Configuration

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional - System Configuration
SIDHE_DEBUG=true
SIDHE_LOG_LEVEL=INFO
SIDHE_HOST=localhost
SIDHE_PORT=8000
REDIS_URL=redis://localhost:6379

# Optional - AI Configuration
LLM_MODEL=claude-3-sonnet-20240229
LLM_TEMPERATURE=0.7
MAX_CONTEXT_TOKENS=4000
```

### Plugin Configuration
Plugins can be enabled/disabled in the startup script or through environment variables.

## 🧪 Testing & Quality Control

```bash
# Run backend tests
cd src/conversation_engine/backend
python -m pytest

# Run frontend tests
cd src/conversation_engine/frontend
npm test

# Quality control checks
python -m black src/  # Format Python code
python -m flake8 src/  # Lint Python code
python -m mypy src/   # Type checking

# Frontend quality checks
npm run lint          # ESLint checking
npm run format        # Prettier formatting

# Health check
curl http://localhost:8000/health
```

## 🛠️ Development

### Adding New Features
1. **Backend**: Add endpoints in `src/conversation_engine/backend/`
2. **Frontend**: Update React components in `src/conversation_engine/frontend/src/`
3. **Plugins**: Create new plugins in `plugins/` directory
4. **AI Responses**: Modify conversation logic in `conversation/ai_handler.py`

### Plugin Development
```python
# plugins/my_plugin/main.py
class MyPlugin:
    async def handle_request(self, request):
        # Your plugin logic here
        return {"response": "Plugin response"}
```

## 📈 System Health

Check system status at any time:
- **Web Dashboard**: http://localhost:3000
- **Health Endpoint**: http://localhost:8000/health
- **Logs**: Check console output for real-time status

## 🔮 Roadmap

### Current Capabilities ✅
- ✅ Full AI conversation engine with Claude integration
- ✅ Real-time WebSocket communication
- ✅ Intent classification and smart routing
- ✅ Plugin ecosystem with GitHub integration
- ✅ Quality Control Plugin Cluster with automated linting and testing
- ✅ DevOps Automator Plugin with CI/CD, deployment, and infrastructure automation
- ✅ Mystical SIDHE-branded interface
- ✅ Comprehensive development assistance

### Upcoming Features 🚀
- 🔮 Enhanced memory system with conversation persistence
- 🧙‍♂️ Advanced plugin marketplace
- ⚡ Code generation and automated testing
- 🌟 Multi-project management
- 🔄 Continuous learning and adaptation

## 🤝 Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for the Claude API that powers SIDHE's intelligence
- **Celtic Mythology** for inspiration from the mystical Sidhe beings
- **Open Source Community** for the tools and libraries that make SIDHE possible

---

*"May your code be bug-free and your commits be meaningful. The ancient wisdom flows through those who seek knowledge."* - The SIDHE Chronicles

**Ready to begin your journey with SIDHE? Start the conversation and let the magic unfold!** ✨🧙‍♂️
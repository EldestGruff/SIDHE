# SIDHE - Your AI Development Apprentice

> "The best way to succeed is to be ready when opportunity presents itself." - Commander William T. SIDHE

## 🚀 Quest Statement

SIDHE is your trusted AI second-in-command, transforming ideas into implemented reality through intelligent conversation, strategic decomposition, and autonomous execution. With the Conversation Engine now enchanted, SIDHE provides real-time conversational AI development assistance with full plugin orchestration.

## 🖖 Quick Start

### Conversation Engine (Production Ready)

```bash
# Deploy the complete system
cd src/voice_of_wisdom/docker
./enchant.sh

# Access the dashboard
open http://localhost:3000

# Access the API
curl http://localhost:8000/health
```

### Traditional Scripts

```bash
# Initialize SIDHE
./scripts/engage.sh

# Create a new quest
sidhe quest create "Build authentication system"

# Check quest status
sidhe status
```

## 🧠 Core Systems

### Conversation Engine ✅ ENCHANTED
The central intelligence hub providing:
- **Real-time Conversational AI** with LLM-based intent parsing
- **Plugin Orchestration** seamlessly integrating all system components
- **WebSocket Interface** for real-time communication
- **Dashboard UI** with system health monitoring and quest management
- **Production Deployment** with Docker containerization

### Plugin Ecosystem ✅ ACTIVE
- **Memory Manager** - Conversation context and history management
- **GitHub Integration** - Quest lifecycle management  
- **Config Manager** - System configuration and settings

## 🌟 Features

- **🗣️ Natural Language Interface**: Communicate with SIDHE through natural conversation
- **🧠 Intelligent Intent Recognition**: Advanced LLM-powered understanding of development requests
- **🔌 Plugin Architecture**: Modular system with hot-swappable components
- **📊 Real-time Dashboard**: Monitor system health, missions, and conversations
- **🐳 Container-Ready**: Production enchantment with Docker and health monitoring
- **🧪 Comprehensive Testing**: 100+ test cases with integration and performance testing
- **⚡ Async Architecture**: High-performance concurrent processing
- **🔄 Message Bus**: Redis-based communication between components
- **📈 Analytics**: Conversation analytics and system metrics

## 📚 Documentation

- [THE_OLD_LAWS.md](THE_OLD_LAWS.md) - Core operating principles
- [BRIDGE.md](BRIDGE.md) - Current system status  
- [Conversation Engine](src/voice_of_wisdom/README.md) - Core AI system documentation
- [Docker Deployment](src/voice_of_wisdom/docker/README.md) - Production enchantment guide
- [Archmage's Log](chronicle/stardate-2025-07.md) - Development history and milestones

## 🛸 Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   React Frontend    │◄──►│  Conversation Engine │◄──►│    Plugin Ecosystem │
│   (Dashboard UI)    │    │   (FastAPI + WS)     │    │                     │
└─────────────────────┘    └──────────────────────┘    │  ┌───────────────┐  │
                                        │               │  │ Memory Manager│  │
┌─────────────────────┐    ┌──────────────────────┐    │  └───────────────┘  │
│     Redis Bus       │◄──►│   Intent Parser      │    │  ┌───────────────┐  │
│  (Message Queue)    │    │  (Anthropic Claude)  │    │  │GitHub Integr. │  │
└─────────────────────┘    └──────────────────────┘    │  └───────────────┘  │
                                                        │  ┌───────────────┐  │
                                                        │  │Config Manager │  │
                                                        │  └───────────────┘  │
                                                        └─────────────────────┘
```

## 📡 System Status

**Current Phase**: ✅ **Core Systems Enchanted**  
**Conversation Engine**: 🟢 Active and Ready  
**Active Plugins**: 3 (Memory Manager, GitHub Integration, Config Manager)  
**Completed Missions**: 2 (Config Manager, Conversation Engine)  
**System Health**: 🟢 All Systems Nominal

### Recent Achievements
- ✅ **Quest #2**: Config Manager Plugin (Completed)
- ✅ **Quest #7**: Conversation Engine Implementation (Completed)
- 🚀 **Production Ready**: Full Docker enchantment with monitoring
- 🧪 **Quality Assured**: Comprehensive test suite with 100+ test cases
- 📊 **Dashboard Active**: Real-time system monitoring and quest management

## 🚀 Getting Started

1. **Prerequisites**: Docker, Docker Compose, Python 3.11+
2. **Environment**: Set `ANTHROPIC_API_KEY` for LLM functionality
3. **Deploy**: Run `cd src/voice_of_wisdom/docker && ./enchant.sh`
4. **Access**: Open http://localhost:3000 for the dashboard
5. **Interact**: Start conversing with SIDHE through the interface

## 🔮 Next Steps

With the Conversation Engine enchanted, SIDHE is ready for:
- Advanced development quest execution
- Self-improving capabilities through conversation
- Complex multi-step project orchestration
- Autonomous code generation and testing
- Continuous learning and adaptation

---

*"Excellent work, Apprentice. The Conversation Engine represents a quantum leap in our capabilities. SIDHE is now truly alive."* - Archmage's Log, Stardate 2025.07.04

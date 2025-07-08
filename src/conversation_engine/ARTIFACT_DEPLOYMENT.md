# Artifact Deployment Guide

Copy each Claude artifact to its designated location:

## 📋 Artifact → File Mapping

| Artifact Name | Copy To Location |
|---------------|------------------|
| `voice_of_wisdom_spec` | `grimoire/conversation-engine-spec.md` |
| `claude_handoff_guide` | `src/voice_of_wisdom/docs/claude-handoff.md` |
| `away_quest_template` | `.github/ISSUE_TEMPLATE/conversation-engine-quest.md` |
| `backend_main_py` | `src/voice_of_wisdom/backend/main.py` |
| `backend_settings` | `src/voice_of_wisdom/backend/config/settings.py` |
| `backend_requirements` | `src/voice_of_wisdom/backend/requirements.txt` |
| `intent_models` | `src/voice_of_wisdom/backend/intent/models.py` |
| `websocket_connection` | `src/voice_of_wisdom/backend/websocket/connection.py` |
| `backend_test_example` | `src/voice_of_wisdom/tests/backend/test_main.py` |
| `frontend_package_json` | `src/voice_of_wisdom/frontend/package.json` |
| `frontend_app_jsx` | `src/voice_of_wisdom/frontend/src/App.jsx` |
| `chat_interface` | `src/voice_of_wisdom/frontend/src/components/Chat/ChatInterface.jsx` |
| `message_list` | `src/voice_of_wisdom/frontend/src/components/Chat/MessageList.jsx` |
| `message_input` | `src/voice_of_wisdom/frontend/src/components/Chat/MessageInput.jsx` |
| `typing_indicator` | `src/voice_of_wisdom/frontend/src/components/Chat/TypingIndicator.jsx` |
| `websocket_hook` | `src/voice_of_wisdom/frontend/src/hooks/useWebSocket.js` |
| `conversation_hook` | `src/voice_of_wisdom/frontend/src/hooks/useConversation.js` |
| `docker_compose_config` | `src/voice_of_wisdom/docker/docker-compose.yml` |
| `dockerfile_backend` | `src/voice_of_wisdom/docker/Dockerfile.backend` |
| `dockerfile_frontend` | `src/voice_of_wisdom/docker/Dockerfile.frontend` |

## ✅ After copying all artifacts, run: bash verify_foundation.sh

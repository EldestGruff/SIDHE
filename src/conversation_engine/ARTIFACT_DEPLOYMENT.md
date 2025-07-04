# Artifact Deployment Guide

Copy each Claude artifact to its designated location:

## 📋 Artifact → File Mapping

| Artifact Name | Copy To Location |
|---------------|------------------|
| `conversation_engine_spec` | `crew-quarters/conversation-engine-spec.md` |
| `claude_handoff_guide` | `src/conversation_engine/docs/claude-handoff.md` |
| `away_mission_template` | `.github/ISSUE_TEMPLATE/conversation-engine-mission.md` |
| `backend_main_py` | `src/conversation_engine/backend/main.py` |
| `backend_settings` | `src/conversation_engine/backend/config/settings.py` |
| `backend_requirements` | `src/conversation_engine/backend/requirements.txt` |
| `intent_models` | `src/conversation_engine/backend/intent/models.py` |
| `websocket_connection` | `src/conversation_engine/backend/websocket/connection.py` |
| `backend_test_example` | `src/conversation_engine/tests/backend/test_main.py` |
| `frontend_package_json` | `src/conversation_engine/frontend/package.json` |
| `frontend_app_jsx` | `src/conversation_engine/frontend/src/App.jsx` |
| `chat_interface` | `src/conversation_engine/frontend/src/components/Chat/ChatInterface.jsx` |
| `message_list` | `src/conversation_engine/frontend/src/components/Chat/MessageList.jsx` |
| `message_input` | `src/conversation_engine/frontend/src/components/Chat/MessageInput.jsx` |
| `typing_indicator` | `src/conversation_engine/frontend/src/components/Chat/TypingIndicator.jsx` |
| `websocket_hook` | `src/conversation_engine/frontend/src/hooks/useWebSocket.js` |
| `conversation_hook` | `src/conversation_engine/frontend/src/hooks/useConversation.js` |
| `docker_compose_config` | `src/conversation_engine/docker/docker-compose.yml` |
| `dockerfile_backend` | `src/conversation_engine/docker/Dockerfile.backend` |
| `dockerfile_frontend` | `src/conversation_engine/docker/Dockerfile.frontend` |

## ✅ After copying all artifacts, run: bash verify_foundation.sh

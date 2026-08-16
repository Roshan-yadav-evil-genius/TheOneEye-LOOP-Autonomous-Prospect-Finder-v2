import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessageChunk
from contracts.domain import ChatStreamRequest
from application.setup_chat_service import SetupChatService


@pytest.mark.asyncio
async def test_setup_chat_service_fork_retry_flow(monkeypatch):
    mock_agent = AsyncMock()
    mock_fork_config = {
        "configurable": {
            "thread_id": "thread-123",
            "checkpoint_ns": "ns-1",
            "checkpoint_id": "cp-forked-123"
        }
    }
    mock_agent.aupdate_state.return_value = mock_fork_config

    async def mock_astream_events(input_data, config, version, subgraphs):
        assert input_data is None
        assert config["configurable"]["checkpoint_id"] == "cp-forked-123"
        yield {
            "event": "on_chat_model_stream",
            "name": "agent",
            "data": {
                "chunk": AIMessageChunk(content="Hello from forked checkpoint")
            }
        }

    mock_agent.astream_events = mock_astream_events

    mock_state = MagicMock()
    mock_state.next = None
    mock_agent.aget_state.return_value = mock_state

    def mock_agent_factory(checkpointer):
        return mock_agent

    verify_entity_mock = AsyncMock()

    service = SetupChatService(
        thread_id="thread-123",
        verify_entity=verify_entity_mock,
        agent_factory=mock_agent_factory,
        tool_context={"test": True}
    )

    request = ChatStreamRequest(
        message="",
        mode="ask",
        retry=True,
        config={
            "configurable": {
                "thread_id": "thread-123",
                "checkpoint_id": "cp-original-456"
            }
        }
    )

    class DummyCheckpointScope:
        async def __aenter__(self):
            return MagicMock()
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("application.setup_chat_service.checkpoint_scope", lambda: DummyCheckpointScope())

    events = []
    async for event_chunk in service.stream_chat(request):
        events.append(event_chunk)

    mock_agent.aupdate_state.assert_called_once_with(request.config, values=None)
    assert any("Hello from forked checkpoint" in e for e in events)
    assert any("event: done" in e for e in events)

import aiohttp
import pytest
from orchestrator import orchestrate, Task, Result
from unittest.mock import AsyncMock, patch
import asyncio
from aiohttp import ClientError

@pytest.mark.asyncio
async def test_successful_orchestration():
    tasks = [Task("m1", "prompt1", 10), Task("m2", "prompt2", 20)]
    endpoint = "http://example.com"
    api_key = "fake_key"

    with patch('orchestrator.ClientSession') as mock_session:
        mock_session.return_value = mock_session
        mock_response = type('Response', (), {})
        mock_response.json = AsyncMock(return_value={'result': 'success'})
        mock_session.post.return_value = mock_response

        results = await orchestrate(tasks, endpoint, api_key)

        assert len(results) == 2
        for res in results:
            assert res.status == 'ok'
            assert res.response is not None
            assert res.retries_used == 0
            assert res.error_message is None
            assert isinstance(res.latency_ms, float)
            assert res.latency_ms >= 0

@pytest.mark.asyncio
async def test_retry_on_failure():
    task = Task("m1", "prompt", 10)
    endpoint = "http://example.com"
    api_key = "fake_key"

    error1 = ClientError("First failure")
    error2 = ClientError("Second failure")
    success_response = type('Response', (), {})
    success_response.json = AsyncMock(return_value={'result': 'success'})

    with patch('orchestrator.ClientSession') as mock_session:
        mock_session.return_value = mock_session
        mock_session.post.side_effect = [error1, error2, success_response]

        results = await orchestrate([task], endpoint, api_key)

        res = results[0]
        assert res.status == 'ok'
        assert res.retries_used == 2
        assert res.response == {'result': 'success'}
        assert res.error_message is None

@pytest.mark.asyncio
async def test_max_retries_exceeded():
    task = Task("m1", "prompt", 10)
    endpoint = "http://example.com"
    api_key = "fake_key"

    errors = [ClientError("Failure")] * 4

    with patch('orchestrator.ClientSession') as mock_session:
        mock_session.return_value = mock_session
        mock_session.post.side_effect = errors

        results = await orchestrate([task], endpoint, api_key)

        res = results[0]
        assert res.status == 'error'
        assert res.retries_used == 3
        assert res.error_message is not None

@pytest.mark.asyncio
async def test_timeout_handling():
    task = Task("m1", "prompt", 10)
    endpoint = "http://example.com"
    api_key = "fake_key"

    timeout_error = asyncio.TimeoutError("Timeout")
    success_response = type('Response', (), {})
    success_response.json = AsyncMock(return_value={'result': 'success'})

    with patch('orchestrator.ClientSession') as mock_session:
        mock_session.return_value = mock_session
        mock_session.post.side_effect = [timeout_error, success_response]

        results = await orchestrate([task], endpoint, api_key)

        res = results[0]
        assert res.status == 'ok'
        assert res.retries_used == 1
        assert res.response == {'result': 'success'}

@pytest.mark.asyncio
async def test_concurrent_limiting():
    tasks = [Task(f"m{i}", f"prompt{i}", 10) for i in range(6)]
    endpoint = "http://example.com"
    api_key = "fake_key"

    active_requests = 0
    max_active = 0
    lock = asyncio.Lock()

    with patch('orchestrator.ClientSession') as mock_session:
        mock_session.return_value = mock_session

        async def mock_post(*args, **kwargs):
            nonlocal active_requests, max_active
            async with lock:
                active_requests += 1
                if active_requests > max_active:
                    max_active = active_requests
            await asyncio.sleep(0.01)
            async with lock:
                active_requests -= 1
            mock_response = type('Response', (), {})
            mock_response.json = AsyncMock(return_value={'result': 'success'})
            return mock_response

        mock_session.post = AsyncMock(side_effect=mock_post)

        results = await orchestrate(tasks, endpoint, api_key)

        assert max_active <= 5
        for res in results:
            assert res.status == 'ok'

@pytest.mark.asyncio
async def test_unexpected_error():
    task = Task("m1", "prompt", 10)
    endpoint = "http://example.com"
    api_key = "fake_key"

    with patch('orchestrator.ClientSession') as mock_session:
        mock_session.return_value = mock_session
        mock_session.post = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        results = await orchestrate([task], endpoint, api_key)

        res = results[0]
        assert res.status == 'error'
        assert "Unexpected error" in res.error_message
        assert res.retries_used == 0
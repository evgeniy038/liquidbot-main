"""Portfolio API tests."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_check():
    """Test health endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_create_portfolio():
    """Test portfolio creation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/portfolio/create", json={
            "discord_id": "test_user_123",
            "username": "TestUser",
        })
        # Should either create or return error if already exists
        assert response.status_code in [200, 400]


@pytest.mark.anyio
async def test_get_portfolio_not_found():
    """Test getting non-existent portfolio."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/portfolio/nonexistent_user_99999")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_save_portfolio_not_found():
    """Test saving to non-existent portfolio."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/portfolio/save?discord_id=nonexistent_99999", json={
            "bio": "Test bio",
        })
        assert response.status_code == 404


@pytest.mark.anyio
async def test_submit_portfolio_not_found():
    """Test submitting non-existent portfolio."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/portfolio/submit", json={
            "discord_id": "nonexistent_99999",
        })
        assert response.status_code == 404


@pytest.mark.anyio
async def test_portfolio_list_all():
    """Test listing all portfolios."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/portfolio/list/all")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_portfolio_list_by_status():
    """Test listing portfolios by status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/portfolio/list/all?status=submitted")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_can_resubmit():
    """Test can-resubmit endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/portfolio/test_user/can-resubmit")
        assert response.status_code == 200
        data = response.json()
        assert "can_resubmit" in data


@pytest.mark.anyio
async def test_portfolio_flow():
    """Test full portfolio flow: create -> save -> submit."""
    transport = ASGITransport(app=app)
    test_discord_id = "test_flow_user_12345"
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create portfolio
        create_response = await client.post("/api/portfolio/create", json={
            "discord_id": test_discord_id,
            "username": "TestFlowUser",
        })
        # Accept both 200 (created) and 400 (already exists)
        assert create_response.status_code in [200, 400]
        
        # 2. Save portfolio data
        save_response = await client.post(f"/api/portfolio/save?discord_id={test_discord_id}", json={
            "bio": "This is my unique test bio",
            "twitter_handle": "testhandle",
            "achievements": "My test achievements",
            "target_role": "Current",
        })
        
        if save_response.status_code == 200:
            # 3. Submit portfolio
            submit_response = await client.post("/api/portfolio/submit", json={
                "discord_id": test_discord_id,
            })
            assert submit_response.status_code == 200
            data = submit_response.json()
            assert data["status"] == "submitted"
        
        # 4. Cleanup - delete portfolio
        await client.delete(f"/api/portfolio/{test_discord_id}")


@pytest.mark.anyio
async def test_delete_portfolio():
    """Test portfolio deletion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Try to delete non-existent portfolio
        response = await client.delete("/api/portfolio/delete_test_nonexistent_99999")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_portfolio_history():
    """Test portfolio history endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/portfolio/test_user/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

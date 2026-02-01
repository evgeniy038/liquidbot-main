"""Comprehensive Portfolio E2E Tests - All Scenarios."""

import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


TEST_DISCORD_ID = "test_e2e_user_999"


class TestPortfolioFullFlow:
    """Test complete portfolio lifecycle."""
    
    @pytest.mark.anyio
    async def test_01_create_portfolio(self):
        """Scenario 1: Create new portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Cleanup first
            await client.delete(f"/api/portfolio/{TEST_DISCORD_ID}")
            
            # Create
            response = await client.post("/api/portfolio/create", json={
                "discord_id": TEST_DISCORD_ID,
                "username": "E2ETestUser",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "draft"
            assert data["discord_id"] == TEST_DISCORD_ID
    
    @pytest.mark.anyio
    async def test_02_get_portfolio(self):
        """Scenario 2: Get existing portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/portfolio/{TEST_DISCORD_ID}")
            assert response.status_code == 200
            data = response.json()
            assert data["discord_id"] == TEST_DISCORD_ID
    
    @pytest.mark.anyio
    async def test_03_save_portfolio(self):
        """Scenario 3: Save portfolio data."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/portfolio/save?discord_id={TEST_DISCORD_ID}",
                json={
                    "bio": "Test bio for E2E",
                    "twitter_handle": "testhandle",
                    "achievements": "Test achievements",
                    "target_role": "Current",
                    "tweets": [
                        {"tweet_url": "https://x.com/test/status/123", "tweet_id": "123"},
                        {"tweet_url": "https://x.com/test/status/456", "tweet_id": "456"},
                    ]
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["bio"] == "Test bio for E2E"
            assert data["twitter_handle"] == "testhandle"
            assert len(data["tweets"]) == 2
    
    @pytest.mark.anyio
    async def test_04_submit_portfolio(self):
        """Scenario 4: Submit portfolio for review."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/portfolio/submit", json={
                "discord_id": TEST_DISCORD_ID,
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "submitted"
    
    @pytest.mark.anyio
    async def test_05_review_reject(self):
        """Scenario 5: Reject portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/portfolio/review", json={
                "discord_id": TEST_DISCORD_ID,
                "reviewer_id": "reviewer_123",
                "action": "reject",
                "feedback": "Need more content",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "rejected"
    
    @pytest.mark.anyio
    async def test_06_resubmit_after_reject(self):
        """Scenario 6: Edit and resubmit after rejection."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Save updated data (should change status back to draft)
            save_response = await client.post(
                f"/api/portfolio/save?discord_id={TEST_DISCORD_ID}",
                json={
                    "bio": "Updated bio after rejection",
                    "achievements": "More achievements added",
                }
            )
            assert save_response.status_code == 200
            assert save_response.json()["status"] == "draft"
            
            # Submit again
            submit_response = await client.post("/api/portfolio/submit", json={
                "discord_id": TEST_DISCORD_ID,
            })
            assert submit_response.status_code == 200
            assert submit_response.json()["status"] == "submitted"
    
    @pytest.mark.anyio
    async def test_07_review_approve(self):
        """Scenario 7: Approve portfolio for voting."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/portfolio/review", json={
                "discord_id": TEST_DISCORD_ID,
                "reviewer_id": "reviewer_123",
                "action": "approve",
                "feedback": "Looks good!",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending_vote"
    
    @pytest.mark.anyio
    async def test_08_cast_votes(self):
        """Scenario 8: Cast votes on portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Vote 1 - approve
            v1 = await client.post(
                f"/api/portfolio/vote?discord_id={TEST_DISCORD_ID}&voter_discord_id=voter1&vote_type=approve"
            )
            assert v1.status_code == 200
            
            # Vote 2 - approve
            v2 = await client.post(
                f"/api/portfolio/vote?discord_id={TEST_DISCORD_ID}&voter_discord_id=voter2&vote_type=approve"
            )
            assert v2.status_code == 200
            
            # Vote 3 - reject
            v3 = await client.post(
                f"/api/portfolio/vote?discord_id={TEST_DISCORD_ID}&voter_discord_id=voter3&vote_type=reject"
            )
            assert v3.status_code == 200
            
            # Duplicate vote should fail
            v_dup = await client.post(
                f"/api/portfolio/vote?discord_id={TEST_DISCORD_ID}&voter_discord_id=voter1&vote_type=approve"
            )
            assert v_dup.status_code == 400
    
    @pytest.mark.anyio
    async def test_09_check_vote_status(self):
        """Scenario 9: Check vote status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/portfolio/vote-check/{TEST_DISCORD_ID}")
            assert response.status_code == 200
            data = response.json()
            assert data["approve_count"] == 2
            assert data["reject_count"] == 1
    
    @pytest.mark.anyio
    async def test_10_delete_portfolio(self):
        """Scenario 10: Delete portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/portfolio/{TEST_DISCORD_ID}")
            assert response.status_code == 200
            
            # Verify deleted
            get_response = await client.get(f"/api/portfolio/{TEST_DISCORD_ID}")
            assert get_response.status_code == 404
    
    @pytest.mark.anyio
    async def test_11_recreate_after_delete(self):
        """Scenario 11: Create new portfolio after deletion."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/portfolio/create", json={
                "discord_id": TEST_DISCORD_ID,
                "username": "E2ETestUser",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "draft"
            assert data["tweets"] == []  # New portfolio has no tweets
    
    @pytest.mark.anyio
    async def test_12_cleanup(self):
        """Cleanup test data."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.delete(f"/api/portfolio/{TEST_DISCORD_ID}")


class TestPortfolioEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.anyio
    async def test_create_duplicate(self):
        """Cannot create duplicate portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create first
            await client.post("/api/portfolio/create", json={
                "discord_id": "edge_case_user",
                "username": "EdgeUser",
            })
            
            # Try duplicate
            response = await client.post("/api/portfolio/create", json={
                "discord_id": "edge_case_user",
                "username": "EdgeUser",
            })
            assert response.status_code == 400
            
            # Cleanup
            await client.delete("/api/portfolio/edge_case_user")
    
    @pytest.mark.anyio
    async def test_submit_without_required_fields(self):
        """Cannot submit without bio and twitter."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create
            await client.post("/api/portfolio/create", json={
                "discord_id": "incomplete_user",
                "username": "IncompleteUser",
            })
            
            # Try submit without required fields
            response = await client.post("/api/portfolio/submit", json={
                "discord_id": "incomplete_user",
            })
            assert response.status_code == 400
            
            # Cleanup
            await client.delete("/api/portfolio/incomplete_user")
    
    @pytest.mark.anyio
    async def test_review_nonexistent(self):
        """Cannot review non-existent portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/portfolio/review", json={
                "discord_id": "nonexistent_12345",
                "reviewer_id": "reviewer",
                "action": "approve",
            })
            assert response.status_code == 404
    
    @pytest.mark.anyio
    async def test_vote_on_non_pending(self):
        """Cannot vote on non-pending portfolio."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create and save (draft status)
            await client.post("/api/portfolio/create", json={
                "discord_id": "vote_test_user",
                "username": "VoteTestUser",
            })
            
            # Try to vote on draft
            response = await client.post(
                "/api/portfolio/vote?discord_id=vote_test_user&voter_discord_id=v1&vote_type=approve"
            )
            assert response.status_code == 404
            
            # Cleanup
            await client.delete("/api/portfolio/vote_test_user")
    
    @pytest.mark.anyio
    async def test_list_all_portfolios(self):
        """List all portfolios."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/portfolio/list/all")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    @pytest.mark.anyio
    async def test_list_by_status(self):
        """List portfolios by status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for status in ["draft", "submitted", "pending_vote", "rejected", "promoted"]:
                response = await client.get(f"/api/portfolio/list/all?status={status}")
                assert response.status_code == 200


class TestPortfolioHistory:
    """Test portfolio history and resubmission."""
    
    @pytest.mark.anyio
    async def test_can_resubmit_new_user(self):
        """New user can always submit."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/portfolio/new_user_999/can-resubmit")
            assert response.status_code == 200
            assert response.json()["can_resubmit"] == True
    
    @pytest.mark.anyio
    async def test_history_empty(self):
        """New user has no history."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/portfolio/new_user_999/history")
            assert response.status_code == 200
            assert response.json() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

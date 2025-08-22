import pytest
from httpx import AsyncClient

# Since the tests directory is at the root, we need to adjust the python path
# to import the 'app' module. A better solution would be to structure this as a
# proper package, but for now, this allows pytest to find the app.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """
    Tests the /health endpoint to ensure it returns a 200 OK status and the correct response body.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200

    response_json = response.json()
    assert response_json["status"] == "ok"
    assert "time" in response_json

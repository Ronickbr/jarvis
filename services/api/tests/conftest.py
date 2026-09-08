from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jarvis_api.config import Settings, get_settings
from jarvis_api.main import app, get_store
from jarvis_api.storage import Store


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_path=tmp_path / "test.db")
    store = Store(settings.database_path)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

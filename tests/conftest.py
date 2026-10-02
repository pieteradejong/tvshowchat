import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The app resolves app/data and app/logging_config.json relative to the cwd.
os.chdir(ROOT)


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.api.main import app

    with TestClient(app) as c:
        yield c

import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_support_ops.db"
os.environ["CHROMA_PATH"] = "./test_chroma"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["AI_PROVIDER"] = "heuristic"

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def clean_artifacts():
    yield
    engine.dispose()
    db_path = Path("test_support_ops.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass
    chroma_path = Path("test_chroma")
    if chroma_path.exists():
        shutil.rmtree(chroma_path, ignore_errors=True)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client

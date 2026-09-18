import pytest

from app import create_app

@pytest.fixture
def app():
    aplication = create_app()
    aplication.config.update(TESTING=True)
    return aplication

@pytest.fixture
def client(app):
    return app.test_client()


import pytest
from src.api.main import create_app

@pytest.fixture
def app():
    app = create_app()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_process_endpoint(client):
    # Add your API tests here
    pass

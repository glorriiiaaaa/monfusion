import pytest
import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_utils import db, init_db

@pytest.fixture
def client():
    """Create a test client for the app."""
    # Use a temporary database for testing
    test_db = tempfile.mktemp(suffix='.db')
    
    # Override the database path
    import db_utils as db_module
    original_db = db_module.DB
    db_module.DB = test_db
    
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    db_module.DB = original_db

@pytest.fixture
def auth_headers(client):
    """Create authenticated user headers."""
    # Register a test user
    response = client.post('/api/register', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'phone': '9876543210'
    })
    
    # Login
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'Test@1234'
    })
    
    # Get session cookie
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'
    
    return client

@pytest.fixture
def admin_headers(client):
    """Create authenticated admin headers."""
    # Create admin session manually
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_user'] = 'ParabStore'
    
    return client

import pytest

def test_tc001_register_valid_data(client):
    """TC001: Valid user registration data"""
    response = client.post('/api/signup', json={
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'Test@1234',
        'phone': '9876543210'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_tc002_register_duplicate_email(client):
    """TC002: Duplicate email registration"""
    # First registration
    client.post('/api/signup', json={
        'name': 'Test User',
        'email': 'duplicate@example.com',
        'password': 'Test@1234',
        'phone': '9876543210'
    })
    
    # Second registration with same email
    response = client.post('/api/signup', json={
        'name': 'Another User',
        'email': 'duplicate@example.com',
        'password': 'Test@5678',
        'phone': '9876543211'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_tc003_register_invalid_email(client):
    """TC003: Invalid email format"""
    response = client.post('/api/signup', json={
        'name': 'Test User',
        'email': 'invalidemail',
        'password': 'Test@1234',
        'phone': '9876543210'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_tc004_login_valid_credentials(client):
    """TC004: Valid login credentials"""
    # Register first
    client.post('/api/signup', json={
        'name': 'Login User',
        'email': 'login@example.com',
        'password': 'Login@1234',
        'phone': '9876543210'
    })
    
    # Login
    response = client.post('/api/login', json={
        'email': 'login@example.com',
        'password': 'Login@1234'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'user' in data

def test_tc005_login_invalid_credentials(client):
    """TC005: Invalid login credentials"""
    response = client.post('/api/login', json={
        'email': 'nonexistent@example.com',
        'password': 'Wrong@1234'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data

def test_tc027_deactivated_user_login(client):
    """TC027: Deactivated customer login attempt"""
    # Register and deactivate user
    client.post('/api/signup', json={
        'name': 'Deactivated User',
        'email': 'deactivated@example.com',
        'password': 'Deactivated@1234',
        'phone': '9876543210'
    })
    
    # Manually deactivate in database
    from db_utils import db
    c = db()
    c.execute("UPDATE users SET active=0 WHERE email=?", ('deactivated@example.com',))
    c.commit()
    c.close()
    
    # Try login
    response = client.post('/api/login', json={
        'email': 'deactivated@example.com',
        'password': 'Deactivated@1234'
    })
    assert response.status_code == 403
    data = response.get_json()
    assert 'deactivated' in data['error'].lower()

def test_tc028_password_reset_valid_email(client):
    """TC028: Password reset with valid email"""
    # Register user first
    client.post('/api/register', json={
        'name': 'Reset User',
        'email': 'reset@example.com',
        'password': 'Reset@1234',
        'phone': '9876543210'
    })
    
    # Request password reset
    response = client.post('/api/forgot-password', json={
        'email': 'reset@example.com'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_tc029_password_reset_invalid_email(client):
    """TC029: Password reset with invalid email"""
    response = client.post('/api/forgot-password', json={
        'email': 'nonexistent@example.com'
    })
    # Should still return success for security
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

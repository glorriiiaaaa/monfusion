import pytest

def test_tc018_admin_login_valid_credentials(client):
    """TC018: Admin login with valid credentials"""
    response = client.post('/api/admin/login', json={
        'username': 'ParabStore',
        'password': 'Parab@29'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_admin_login_invalid_credentials(client):
    """Admin login with invalid credentials"""
    response = client.post('/api/admin/login', json={
        'username': 'WrongUser',
        'password': 'WrongPassword'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data

def test_admin_session_check(client, admin_headers):
    """Check admin session"""
    response = admin_headers.get('/api/admin/session')
    assert response.status_code == 200
    data = response.get_json()
    assert data['logged_in'] == True

def test_admin_logout(client, admin_headers):
    """Admin logout"""
    response = admin_headers.post('/api/admin/logout')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

import pytest

def test_get_states(client):
    """Get Indian states"""
    response = client.get('/api/location/states')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # Check if Maharashtra is in the list (it returns objects with code field)
    assert any(state['code'] == 'MH' for state in data)

def test_get_cities(client):
    """Get cities for a state"""
    response = client.get('/api/location/cities/MH')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # Cities might be empty for some states in test data

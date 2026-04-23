import pytest

def test_tc025_admin_view_analytics(client, admin_headers):
    """TC025: Admin view analytics"""
    response = admin_headers.get('/api/admin/analytics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_orders' in data
    assert 'total_revenue' in data
    assert 'total_customers' in data
    assert 'total_products' in data
    assert 'monthly' in data
    assert isinstance(data['monthly'], list)

def test_tc024_admin_create_coupon(client, admin_headers):
    """TC024: Admin create coupon"""
    response = admin_headers.post('/api/admin/coupons', json={
        'code': 'TESTCOUPON',
        'discount_type': 'percent',
        'discount_value': 15,
        'free_delivery': 0,
        'expiry': '2027-12-31'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_admin_get_coupons(client, admin_headers):
    """Get all coupons"""
    response = admin_headers.get('/api/admin/coupons')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_admin_get_customers(client, admin_headers):
    """Get customer list"""
    response = admin_headers.get('/api/admin/customers')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_admin_get_categories(client, admin_headers):
    """Get categories"""
    response = admin_headers.get('/api/admin/categories')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_admin_get_reviews(client, admin_headers):
    """Get all reviews"""
    response = admin_headers.get('/api/admin/reviews')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_admin_get_contact_messages(client, admin_headers):
    """Get contact messages"""
    response = admin_headers.get('/api/admin/contact-messages')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

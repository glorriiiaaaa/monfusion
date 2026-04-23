import pytest

def test_tc008_add_to_cart(client, auth_headers):
    """TC008: Add product to cart"""
    # Get a product ID
    products = auth_headers.get('/api/products').get_json()
    product_id = products[0]['id']
    
    response = auth_headers.post('/api/cart/add', json={
        'product_id': product_id,
        'quantity': 1
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_tc009_update_cart_quantity(client, auth_headers):
    """TC009: Update cart quantity"""
    # Add to cart first
    products = auth_headers.get('/api/products').get_json()
    product_id = products[0]['id']
    auth_headers.post('/api/cart/add', json={'product_id': product_id, 'quantity': 1})
    
    # Update quantity
    response = auth_headers.post('/api/cart/update', json={
        'product_id': product_id,
        'quantity': 2
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_tc010_remove_from_cart(client, auth_headers):
    """TC010: Remove item from cart"""
    # Add to cart first
    products = auth_headers.get('/api/products').get_json()
    product_id = products[0]['id']
    auth_headers.post('/api/cart/add', json={'product_id': product_id, 'quantity': 1})
    
    # Remove
    response = auth_headers.post('/api/cart/remove', json={
        'product_id': product_id
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_get_cart(client, auth_headers):
    """Get cart items"""
    response = auth_headers.get('/api/cart')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_get_cart_count(client, auth_headers):
    """Get cart item count"""
    # Add to cart first
    products = auth_headers.get('/api/products').get_json()
    product_id = products[0]['id']
    auth_headers.post('/api/cart/add', json={'product_id': product_id, 'quantity': 1})
    
    response = auth_headers.get('/api/cart/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] > 0

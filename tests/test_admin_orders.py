import pytest

def test_tc022_admin_update_order_status(client, admin_headers):
    """TC022: Admin update order status"""
    # Get orders
    orders = admin_headers.get('/api/admin/orders').get_json()
    if orders:
        order_id = orders[0]['order_id']
        
        response = admin_headers.put(f'/api/admin/orders/{order_id}/status', json={
            'status': 'shipped'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

def test_tc023_admin_delete_order(client, admin_headers):
    """TC023: Admin delete order"""
    # Create a test order first
    from db_utils import db, gen_oid
    c = db()
    order_id = gen_oid()
    c.execute(
        "INSERT INTO orders(user_id, order_id, total_price, status, address, customer_name, phone, email, payment_method) VALUES(?,?,?,?,?,?,?,?,?)",
        (1, order_id, 500, 'pending', 'Test Address', 'Test Customer', '9876543210', 'test@example.com', 'UPI')
    )
    c.commit()
    c.close()
    
    # Delete the order
    response = admin_headers.delete(f'/api/admin/orders/{order_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_admin_get_orders(client, admin_headers):
    """Get all orders"""
    response = admin_headers.get('/api/admin/orders')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_admin_get_orders_by_status(client, admin_headers):
    """Get orders by status"""
    response = admin_headers.get('/api/admin/orders?status=pending')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_tc026_deactivate_customer(client, admin_headers):
    """TC026: Deactivate customer account"""
    # Get a customer
    from db_utils import db
    c = db()
    user = c.execute("SELECT id FROM users LIMIT 1").fetchone()
    c.close()
    
    if user:
        user_id = user['id']
        response = admin_headers.post(f'/api/admin/customers/{user_id}/deactivate')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

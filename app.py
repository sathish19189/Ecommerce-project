# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# In-memory database
users = {}
products = {
    1: {'id': 1, 'name': 'Classic Cotton T-Shirt', 'category': 'mens', 'price': 29.99, 
        'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400', 
        'description': 'Comfortable cotton t-shirt perfect for everyday wear'},
    2: {'id': 2, 'name': 'Slim Fit Jeans', 'category': 'mens', 'price': 79.99, 
        'image': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400', 
        'description': 'Modern slim fit denim jeans'},
    3: {'id': 3, 'name': 'Casual Button Shirt', 'category': 'mens', 'price': 49.99, 
        'image': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400', 
        'description': 'Versatile button-down shirt for any occasion'},
    4: {'id': 4, 'name': 'Summer Floral Dress', 'category': 'womens', 'price': 89.99, 
        'image': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400', 
        'description': 'Beautiful floral dress perfect for summer'},
    5: {'id': 5, 'name': 'Elegant Blouse', 'category': 'womens', 'price': 59.99, 
        'image': 'https://images.unsplash.com/photo-1564257631407-2bb59f8e0b81?w=400', 
        'description': 'Sophisticated blouse for professional settings'},
    6: {'id': 6, 'name': 'High-Waist Trousers', 'category': 'womens', 'price': 69.99, 
        'image': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400', 
        'description': 'Stylish high-waist trousers'},
}
next_product_id = 7
orders = []

# Routes
@app.route('/')
def home():
    return render_template('home.html', products=list(products.values()))

@app.route('/products/<category>')
def product_list(category):
    if category not in ['mens', 'womens']:
        return redirect('/')
    filtered = [p for p in products.values() if p['category'] == category]
    return render_template('products.html', products=filtered, category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = products.get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect('/')
    return render_template('product_detail.html', product=product)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = products.get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect('/')
    
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    
    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
    
    session['cart'] = cart
    flash(f'Added {product["name"]} to cart!', 'success')
    return redirect('/cart')

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for pid, qty in cart.items():
        product = products.get(int(pid))
        if product:
            item = product.copy()
            item['quantity'] = qty
            cart_items.append(item)
            total += product['price'] * qty
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        flash('Item removed from cart', 'success')
    return redirect('/cart')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not session.get('user'):
        flash('Please login to checkout', 'error')
        return redirect('/login')
    
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty', 'error')
        return redirect('/cart')
    
    if request.method == 'POST':
        order = {
            'user': session['user'],
            'items': cart,
            'total': sum(products[int(pid)]['price'] * qty for pid, qty in cart.items()),
            'shipping': request.form.to_dict(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        orders.append(order)
        session['cart'] = {}
        flash('Order placed successfully!', 'success')
        return redirect('/')
    
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = products.get(int(pid))
        if product:
            item = product.copy()
            item['quantity'] = qty
            cart_items.append(item)
            total += product['price'] * qty
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            session['is_admin'] = user.get('is_admin', False)
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if username in users:
            flash('Username already exists', 'error')
        elif password != confirm:
            flash('Passwords do not match', 'error')
        else:
            users[username] = {
                'email': email,
                'password': generate_password_hash(password),
                'is_admin': len(users) == 0
            }
            flash('Account created! Please login.', 'success')
            return redirect('/login')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/')

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Access denied', 'error')
        return redirect('/')
    return render_template('admin.html', products=list(products.values()))

@app.route('/admin/add', methods=['POST'])
def admin_add():
    global next_product_id
    if not session.get('is_admin'):
        return redirect('/')
    
    products[next_product_id] = {
        'id': next_product_id,
        'name': request.form.get('name'),
        'category': request.form.get('category'),
        'price': float(request.form.get('price')),
        'image': request.form.get('image'),
        'description': request.form.get('description')
    }
    next_product_id += 1
    flash('Product added successfully!', 'success')
    return redirect('/admin')

@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit(product_id):
    if not session.get('is_admin'):
        return redirect('/')
    
    product = products.get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect('/admin')
    
    if request.method == 'POST':
        products[product_id].update({
            'name': request.form.get('name'),
            'category': request.form.get('category'),
            'price': float(request.form.get('price')),
            'image': request.form.get('image'),
            'description': request.form.get('description')
        })
        flash('Product updated successfully!', 'success')
        return redirect('/admin')
    
    return render_template('admin_edit.html', product=product)

@app.route('/admin/delete/<int:product_id>')
def admin_delete(product_id):
    if not session.get('is_admin'):
        return redirect('/')
    
    if product_id in products:
        del products[product_id]
        flash('Product deleted successfully!', 'success')
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from flask import Flask, render_template, request, redirect, session,  flash
import sqlite3
from functools import wraps

app = Flask(__name__, static_folder='path_to_static')
app.secret_key = 'waduh waduh'  # Ganti 'your_secret_key_here' dengan string unik dan rahasia

# Daftar menu makanan dan minuman
FOOD_ITEMS = {
    'Nasi Goreng': 15000,
    'Mie Goreng': 15000,
    'Mie Rebus': 15000,
    'Cap Cay': 16000,
    'Soto': 8000,
    'Gorengan (6 pcs)': 5000
}

DRINK_ITEMS = {
    'Teh': 2000,
    'Jeruk': 2000,
    'Goodday Coklat': 2000,
    'Goodday Coolin': 2000,
    'Goodday Carabian': 2000
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def bypass_static_files():
    if request.path.startswith('/static/'):
        return  # Izinkan Flask melayani file statis tanpa login
def before_request():
    if not session.get('logged_in') and request.endpoint != 'login':
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Proses login
        username = request.form['username']
        password = request.form['password']

        # Cek kredensial di database
        conn = sqlite3.connect('restaurant_orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            # Login berhasil
            session['admin_logged_in'] = True
            return redirect('/admin_dashboard')
        else:
            # Login gagal
            return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return redirect('/')


@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

#Halaman home utama
@app.route('/')
def home():
    return render_template('home.html')


# Route: Form Tambah Pesanan
@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        total_price = 0
        ordered_items = []

        # Ambil item makanan yang dipilih dan jumlahnya
        for menu_item, price in FOOD_ITEMS.items():
            quantity = request.form.get(menu_item, type=int)
            if quantity:  # Jika ada yang dipilih
                ordered_items.append((menu_item, quantity))
                total_price += price * quantity

        # Ambil item minuman yang dipilih dan jumlahnya
        for menu_item, price in DRINK_ITEMS.items():
            quantity = request.form.get(menu_item, type=int)
            if quantity:  # Jika ada yang dipilih
                ordered_items.append((menu_item, quantity))
                total_price += price * quantity

                # Tambahkan biaya untuk minuman es
                if 'Es' in request.form.get(menu_item, ''):
                    total_price += 1000

        # Simpan pesanan ke database
        conn = sqlite3.connect('restaurant_orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (customer_name, menu_item, quantity, total_price, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            customer_name, 
            ', '.join([item[0] for item in ordered_items]),  # Gabungkan nama item
            ', '.join([str(item[1]) for item in ordered_items]),  # Gabungkan jumlah
            total_price,
            'pending'  # Status awal adalah 'pending'
        ))
        conn.commit()
        conn.close()

        # Redirect ke halaman riwayat pesanan pelanggan
        return redirect(f'/customer_orders?name={customer_name}')
    
    return render_template('add_order.html', food_items=FOOD_ITEMS, drink_items=DRINK_ITEMS)

#Route: konfirmasi customer
@app.route('/customer_orders', methods=['GET'])
def customer_orders():
    customer_name = request.args.get('name')  # Nama pelanggan dari query parameter
    conn = sqlite3.connect('restaurant_orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE customer_name = ?', (customer_name,))
    orders = cursor.fetchall()
    conn.close()

    return render_template('customer_orders.html', orders=orders, customer_name=customer_name)

# Route: Daftar Pesanan
@app.route('/orders', methods=['GET'])
@login_required
def orders():
    conn = sqlite3.connect('restaurant_orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders')
    orders = cursor.fetchall()
    conn.close()

    return render_template('orders.html', orders=orders)

# Route: Pesanan yang sedang diproses (pending)
@app.route('/pending_orders', methods=['GET'])
@login_required
def pending_orders():
    conn = sqlite3.connect('restaurant_orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE status="pending"')  # Pesanan yang sedang diproses
    orders = cursor.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/transaction_history', methods=['GET'])
def transaction_history():
    conn = sqlite3.connect('restaurant_orders.db')
    cursor = conn.cursor()

    # Ambil semua transaksi yang sudah selesai
    cursor.execute('''
        SELECT id, customer_name, menu_item, quantity, total_price, date(created_at)
        FROM orders
        WHERE status = 'completed'
    ''')
    completed_orders = cursor.fetchall()

    # Hitung pendapatan per hari
    cursor.execute('''
        SELECT date(created_at) AS order_date, SUM(total_price) AS daily_income
        FROM orders
        WHERE status = 'completed'
        GROUP BY order_date
        ORDER BY order_date DESC
    ''')
    daily_income = cursor.fetchall()

    conn.close()

    return render_template('transaction_history.html', 
                           completed_orders=completed_orders, 
                           daily_income=daily_income)


@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form['status']
    conn = sqlite3.connect('restaurant_orders.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect('/pending_orders')  # Kembali ke daftar pesanan yang sedang diproses

@app.after_request
def log_request(response):
    print(f"{request.method} {request.path} -> {response.status_code}")
    return response



if __name__ == '__main__':
    app.run(debug=True)

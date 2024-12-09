import sqlite3

def create_db():
    # Connect ke database SQLite (akan membuat file baru jika belum ada)
    conn = sqlite3.connect('restaurant_orders.db')
    cursor = conn.cursor()

    # Membuat tabel orders jika belum ada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            menu_item TEXT,
            quantity TEXT,
            total_price INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Membuat tabel admin jika belum ada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        );
    ''')

    # Tambahkan admin default jika belum ada
    cursor.execute("SELECT * FROM admin WHERE username = 'admin'")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO admin (username, password) VALUES ('admin', 'admin123')")

    # Commit perubahan dan tutup koneksi
    conn.commit()
    conn.close()

# Panggil fungsi untuk membuat database dan tabel
create_db()

print("Database baru 'restaurant_orders.db' telah dibuat dengan sukses!")

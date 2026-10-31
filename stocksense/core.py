"""StockSense database transactions and transparent moving-average estimates."""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 sku TEXT NOT NULL UNIQUE,
 supplier TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity >= 0),
 reorder_point INTEGER NOT NULL CHECK(reorder_point >= 0),
 unit_price REAL NOT NULL CHECK(unit_price >= 0)
);
CREATE TABLE IF NOT EXISTS sales (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL REFERENCES products(id),
 sold_on TEXT NOT NULL,
 units INTEGER NOT NULL CHECK(units > 0)
);
CREATE TABLE IF NOT EXISTS stock_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL REFERENCES products(id),
 change_units INTEGER NOT NULL,
 reason TEXT NOT NULL,
 occurred_on TEXT NOT NULL
);
"""

def connect(db_path):
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    connection.executescript(DB_SCHEMA)
    return connection

def add_product(conn, name, sku, supplier, quantity, reorder_point, unit_price):
    if not all(str(x).strip() for x in (name, sku, supplier)) or min(quantity, reorder_point, unit_price) < 0:
        raise ValueError('Provide valid product information and nonnegative quantities.')
    with conn:
        cur=conn.execute('INSERT INTO products(name,sku,supplier,quantity,reorder_point,unit_price) VALUES (?,?,?,?,?,?)',
            (name.strip(),sku.strip(),supplier.strip(),int(quantity),int(reorder_point),float(unit_price)))
    return cur.lastrowid

def list_products(conn):
    return [dict(row) for row in conn.execute('SELECT * FROM products ORDER BY name')]

def record_sale(conn, product_id, units, sold_on=None):
    if units<=0:raise ValueError('Sales units must be positive.')
    sold_on=sold_on or date.today().isoformat()
    with conn:
        item=conn.execute('SELECT quantity FROM products WHERE id=?',(product_id,)).fetchone()
        if item is None:raise ValueError('Unknown product.')
        if units>item['quantity']:raise ValueError('Insufficient inventory for this sale.')
        conn.execute('UPDATE products SET quantity=quantity-? WHERE id=?',(units,product_id))
        conn.execute('INSERT INTO sales(product_id,sold_on,units) VALUES (?,?,?)',(product_id,sold_on,units))
        conn.execute('INSERT INTO stock_events(product_id,change_units,reason,occurred_on) VALUES (?,?,?,?)',(product_id,-units,'Sale',sold_on))

def restock(conn,product_id,units):
    if units<=0:raise ValueError('Restock units must be positive.')
    with conn:
        cur=conn.execute('UPDATE products SET quantity=quantity+? WHERE id=?',(units,product_id))
        if not cur.rowcount:raise ValueError('Unknown product.')
        conn.execute('INSERT INTO stock_events(product_id,change_units,reason,occurred_on) VALUES (?,?,?,?)',(product_id,units,'Restock',date.today().isoformat()))

def daily_sales(conn,product_id,days=14,today=None):
    today=today or date.today()
    start=today-timedelta(days=days-1)
    rows=conn.execute('SELECT sold_on,SUM(units) AS units FROM sales WHERE product_id=? AND sold_on BETWEEN ? AND ? GROUP BY sold_on',
        (product_id,start.isoformat(),today.isoformat())).fetchall()
    values={r['sold_on']:r['units'] for r in rows}
    return [{'date':(start+timedelta(days=i)).isoformat(),'units':values.get((start+timedelta(days=i)).isoformat(),0)} for i in range(days)]

def forecast(conn,product_id,days=7,history_days=14,today=None):
    values=daily_sales(conn,product_id,history_days,today)
    avg=sum(x['units'] for x in values)/history_days
    product=conn.execute('SELECT * FROM products WHERE id=?',(product_id,)).fetchone()
    if product is None:raise ValueError('Unknown product.')
    target=max(product['reorder_point'],round(avg*days))
    return {'avg_daily_units':round(avg,2),'estimated_demand':round(avg*days,1),
            'suggested_reorder':max(0,target-product['quantity']),'current_quantity':product['quantity'],
            'history_days':history_days,'forecast_days':days}

def seed(conn):
    if conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]:return
    items=[('Notebook A5','NOTE-001','Campus Supplies',24,12,3.5),('Blue Pen','PEN-002','Office Mart',15,20,0.8),('Water Bottle','BOT-003','GreenSource',35,10,7.0)]
    ids=[add_product(conn,*item) for item in items]
    for i, pid in enumerate(ids):
        for d in range(1,12):
            sold_on=(date.today()-timedelta(days=d)).isoformat()
            # Historical demand examples: do not subtract from current demo snapshot.
            conn.execute('INSERT INTO sales(product_id,sold_on,units) VALUES (?,?,?)',(pid,sold_on,(d+i)%4+1))
    conn.commit()

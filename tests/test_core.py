import sqlite3
import pytest
from datetime import date
from stocksense.core import connect,add_product,record_sale,restock,forecast,daily_sales

def test_inventory_transaction(tmp_path):
    c=connect(tmp_path/'test.db')
    p=add_product(c,'Pencils','P1','Vendor',10,4,1.25)
    record_sale(c,p,3)
    assert c.execute('SELECT quantity FROM products WHERE id=?',(p,)).fetchone()[0]==7
    restock(c,p,5)
    assert c.execute('SELECT quantity FROM products WHERE id=?',(p,)).fetchone()[0]==12
    c.close()

def test_cannot_oversell(tmp_path):
    c=connect(tmp_path/'test.db');p=add_product(c,'Pencils','P1','Vendor',2,1,1)
    with pytest.raises(ValueError):record_sale(c,p,3)
    assert c.execute('SELECT quantity FROM products WHERE id=?',(p,)).fetchone()[0]==2
    c.close()

def test_forecast_and_zero_days(tmp_path):
    c=connect(tmp_path/'test.db');p=add_product(c,'Pencils','P1','Vendor',3,5,1)
    record_sale(c,p,2,date.today().isoformat())
    f=forecast(c,p,days=7,history_days=14)
    assert f['avg_daily_units']==round(2/14,2)
    assert len(daily_sales(c,p))==14
    assert f['suggested_reorder']>=2
    c.close()

def test_unique_sku(tmp_path):
    c=connect(tmp_path/'test.db');add_product(c,'Pencils','P1','Vendor',2,1,1)
    with pytest.raises(sqlite3.IntegrityError):add_product(c,'Pens','P1','Vendor',2,1,1)
    c.close()

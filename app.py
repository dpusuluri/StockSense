from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
from stocksense.core import connect, seed, add_product, list_products, record_sale, restock, daily_sales, forecast

st.set_page_config(page_title='StockSense',page_icon='📦',layout='wide')
st.title('📦 StockSense')
st.caption('Academic inventory and demand-estimate simulator • Fictional products and sales • Estimates are not reliable business forecasts')
conn=connect(Path(__file__).with_name('stocksense.db'))
seed(conn)
products=list_products(conn)
tabs=st.tabs(['Overview','Products','Sales & Restock','Demand estimate'])
with tabs[0]:
    c1,c2,c3=st.columns(3)
    c1.metric('Products',len(products));c2.metric('Units in stock',sum(p['quantity'] for p in products))
    c3.metric('At or below reorder point',sum(p['quantity']<=p['reorder_point'] for p in products))
    st.dataframe(pd.DataFrame(products),use_container_width=True,hide_index=True)
    st.info('Low stock: '+(', '.join(p['name'] for p in products if p['quantity']<=p['reorder_point']) or 'None'))
with tabs[1]:
    with st.form('new_product'):
        name=st.text_input('Product name');sku=st.text_input('Unique SKU');supplier=st.text_input('Supplier')
        qty=st.number_input('Opening quantity',0,100000,10);point=st.number_input('Reorder point',0,100000,5)
        price=st.number_input('Unit price',min_value=0.0,value=1.0)
        if st.form_submit_button('Add product'):
            try:
                add_product(conn,name,sku,supplier,int(qty),int(point),float(price));st.success('Product added.');st.rerun()
            except (ValueError,sqlite3.IntegrityError) as e:st.error(str(e))
with tabs[2]:
    if products:
        options={f"{p['name']} (#{p['id']})":p['id'] for p in products}
        selected=st.selectbox('Product',list(options),key='inventoryproduct');pid=options[selected]
        units=st.number_input('Units',min_value=1,step=1,value=1)
        c1,c2=st.columns(2)
        if c1.button('Record sale'):
            try:record_sale(conn,pid,int(units));st.success('Sale recorded.');st.rerun()
            except ValueError as e:st.error(str(e))
        if c2.button('Receive stock'):
            try:restock(conn,pid,int(units));st.success('Stock received.');st.rerun()
            except ValueError as e:st.error(str(e))
with tabs[3]:
    if products:
        choices={p['name']:p['id'] for p in products}
        product=st.selectbox('Choose product',list(choices),key='forecastproduct')
        pid=choices[product];estimate=forecast(conn,pid)
        c1,c2,c3=st.columns(3)
        c1.metric('Average daily units',estimate['avg_daily_units'])
        c2.metric('Est. next 7 days',estimate['estimated_demand'])
        c3.metric('Suggested reorder units',estimate['suggested_reorder'])
        df=pd.DataFrame(daily_sales(conn,pid));st.line_chart(df.set_index('date')['units'])
        st.caption('Method: total units sold over last 14 calendar days / 14. The 7-day estimate multiplies this average by 7. Days with no sales count as zero. Sample historical data is generated for learning.')
conn.close()

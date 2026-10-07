import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="บันทึกรายรับ-รายจ่าย", page_icon="💰", layout="wide")

def get_db():
    conn = sqlite3.connect('finance_db.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('รายรับ','รายจ่าย')),
        item TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def get_all_transactions():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM transactions ORDER BY date DESC, id DESC", conn)
    conn.close()
    return df

def add_transaction(date, typ, item, amount, note):
    conn = get_db()
    conn.execute("INSERT INTO transactions (date,type,item,amount,note) VALUES (?,?,?,?,?)",
                 (date, typ, item, amount, note))
    conn.commit()
    conn.close()

def delete_transaction(tid):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit()
    conn.close()

st.title("💰 บันทึกรายรับ-รายจ่าย")
st.markdown("---")

df = get_all_transactions()
if not df.empty:
    total_income = df[df['type']=='รายรับ']['amount'].sum()
    total_expense = df[df['type']=='รายจ่าย']['amount'].sum()
    balance = total_income - total_expense
else:
    total_income = total_expense = balance = 0

col1, col2, col3 = st.columns(3)
col1.metric("💵 รวมรายรับ", f"{total_income:,.2f} บาท")
col2.metric("💸 รวมรายจ่าย", f"{total_expense:,.2f} บาท")
col3.metric("💳 ยอดคงเหลือ", f"{balance:,.2f} บาท")

st.markdown("---")
menu = st.sidebar.radio("เมนู", ["เพิ่มรายการ", "ดูรายการทั้งหมด", "ค้นหา", "ลบรายการ", "ส่งออกข้อมูล"])

if menu == "เพิ่มรายการ":
    st.subheader("➕ เพิ่มรายการใหม่")
    with st.form("add_form"):
        date = st.date_input("วันที่", datetime.today())
        typ = st.radio("ประเภท", ["รายรับ", "รายจ่าย"])
        item = st.text_input("รายการ")
        amount = st.number_input("จำนวนเงิน", min_value=0.0, step=1.0)
        note = st.text_input("หมายเหตุ (ถ้ามี)")
        if st.form_submit_button("บันทึก"):
            if not item or amount<=0:
                st.error("กรอกรายการและจำนวนเงินให้ครบ")
            else:
                add_transaction(date.strftime("%Y-%m-%d"), typ, item, amount, note)
                st.success("✅ บันทึกสำเร็จ!")
                st.rerun()

elif menu == "ดูรายการทั้งหมด":
    st.subheader("📋 รายการทั้งหมด")
    st.dataframe(df if not df.empty else "ยังไม่มีรายการ", use_container_width=True, hide_index=True)

elif menu == "ค้นหา":
    st.subheader("🔍 ค้นหา")
    kw = st.text_input("ค้นหา")
    if kw:
        res = df[df['item'].str.contains(kw, case=False) | df['note'].str.contains(kw, case=False, na=False)]
        st.dataframe(res if not res.empty else "ไม่พบ", use_container_width=True, hide_index=True)

elif menu == "ลบรายการ":
    st.subheader("🗑️ ลบรายการ")
    if df.empty:
        st.info("ไม่มีรายการ")
    else:
        sel = st.selectbox("เลือกรายการ", [f"{r['id']} | {r['date']} | {r['item']} | {r['amount']} บาท" for _, r in df.iterrows()])
        del_id = int(sel.split("|")[0].strip())
        if st.button("ยืนยันลบ", type="primary"):
            delete_transaction(del_id)
            st.success("✅ ลบสำเร็จ")
            st.rerun()

elif menu == "ส่งออกข้อมูล":
    st.subheader("📤 ส่งออก")
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("ดาวน์โหลด CSV", csv, "บันทึกรายรับรายจ่าย.csv", "text/csv")
  

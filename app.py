import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ตั้งค่าหน้าแอป
st.set_page_config(
    page_title="บันทึกรายรับรายจ่าย",
    page_icon="💰",
    layout="wide"
)

# เชื่อมต่อฐานข้อมูล
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

if not supabase:
    st.error("❌ ตั้งค่า Secrets ไม่ครบ")
    st.stop()

# ---------- ตรวจสอบการเข้าสู่ระบบ + จดจำไว้ ----------
if "user" not in st.session_state:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass

if "user" not in st.session_state:
    st.title("💰 บันทึกรายรับรายจ่าย")
    
    tab1, tab2 = st.tabs(["เข้าสู่ระบบ", "ลงทะเบียน"])
    
    with tab1:
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("เข้าสู่ระบบ", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email":email, "password":password})
                st.session_state.user = res.user
                st.success("✅ เข้าสู่ระบบสำเร็จ! ครั้งหน้าจำไว้ให้เลย")
                st.rerun()
            except:
                st.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    
    with tab2:
        email2 = st.text_input("อีเมล", key="reg_email")
        password2 = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        if st.button("สร้างบัญชี", type="primary"):
            try:
                supabase.auth.sign_up({"email":email2, "password":password2})
                st.success("✅ สร้างบัญชีสำเร็จ! ตรวจสอบอีเมลแล้วเข้าสู่ระบบ")
            except Exception as e:
                st.error(f"❌ ผิดพลาด: {e}")
    st.stop()

user = st.session_state.user

# ---------- เมนูหลัก เหมือนเดิมทุกประการ ----------
st.title(f"💰 บันทึกรายรับรายจ่าย")
st.write(f"👤 คุณ: {user.email}")

if st.button("ออกจากระบบ"):
    del st.session_state.user
    st.rerun()

st.divider()

menu = st.sidebar.radio("เมนู", ["เพิ่มรายการ", "ดูรายการทั้งหมด", "ค้นหา"])

# ---------- เมนู 1: เพิ่มรายการ ----------
if menu == "เพิ่มรายการ":
    st.subheader("➕ เพิ่มรายการใหม่")
    with st.form("add_form"):
        date = st.date_input("วันที่")
        typ = st.radio("ประเภท", ["รายรับ", "รายจ่าย"])
        item = st.text_input("รายการ")
        amount = st.number_input("จำนวนเงิน", min_value=0.0)
        note = st.text_input("หมายเหตุ (ถ้ามี)")
        
        if st.form_submit_button("บันทึก"):
            if not item or amount <= 0:
                st.error("❌ กรอกรายการและจำนวนเงินให้ครบ")
            else:
                supabase.table("entries").insert({
                    "user_id": user.id,
                    "date": date.isoformat(),
                    "title": item + (f" ({note})" if note else ""),
                    "type": typ,
                    "amount": amount
                }).execute()
                st.success("✅ บันทึกสำเร็จ!")
                st.rerun()

# ---------- เมนู 2: ดูรายการทั้งหมด + สรุป ----------
elif menu == "ดูรายการทั้งหมด":
    st.subheader("📋 รายการทั้งหมด")
    
    # ดึงข้อมูลของคนนี้เท่านั้น
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df = df[["date", "title", "type", "amount"]]
        df.columns = ["วันที่", "รายการ", "ประเภท", "จำนวนเงิน"]
        
        # คำนวณสรุป
        total_income = df[df["ประเภท"] == "รายรับ"]["จำนวนเงิน"].sum()
        total_expense = df[df["ประเภท"] == "รายจ่าย"]["จำนวนเงิน"].sum()
        balance = total_income - total_expense
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 รวมรายรับ", f"{total_income:,.2f} บาท")
        col2.metric("📤 รวมรายจ่าย", f"{total_expense:,.2f} บาท")
        col3.metric("💵 คงเหลือ", f"{balance:,.2f} บาท")
        
        st.divider()
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีข้อมูล เริ่มบันทึกกันเลย!")

# ---------- เมนู 3: ค้นหา ----------
elif menu == "ค้นหา":
    st.subheader("🔍 ค้นหารายการ")
    kw = st.text_input("พิมพ์คำที่ต้องการค้นหา")
    
    if kw:
        res = supabase.table("entries").select("*").eq("user_id", user.id).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df[df["title"].str.contains(kw, case=False) | 
                     df["type"].str.contains(kw, case=False)]
            df = df[["date", "title", "type", "amount"]]
            df.columns = ["วันที่", "รายการ", "ประเภท", "จำนวนเงิน"]
            
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("ไม่พบรายการที่ตรงกับคำค้นหา")
        else:
            st.info("ยังไม่มีข้อมูลในระบบ")

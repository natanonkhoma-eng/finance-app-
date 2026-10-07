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
    st.error("❌ ยังไม่ได้ตั้งค่า Secrets ที่ Streamlit")
    st.stop()

# ถ้ายังไม่ล็อกอิน → แสดงหน้าเข้าสู่ระบบ
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
                st.success("✅ เข้าสู่ระบบสำเร็จ!")
                st.rerun()
            except Exception as e:
                st.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    
    with tab2:
        email2 = st.text_input("อีเมล", key="reg_email")
        password2 = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        if st.button("สร้างบัญชี", type="primary"):
            try:
                supabase.auth.sign_up({"email":email2, "password":password2})
                st.success("✅ สร้างบัญชีสำเร็จ! กรุณาเข้าสู่ระบบ")
            except Exception as e:
                st.error(f"❌ ผิดพลาด: {e}")
    
    st.stop()

# ---------- หน้าหลักหลังล็อกอิน ----------
user = st.session_state.user
st.title(f"💰 บันทึกรายรับรายจ่าย")
st.write(f"👤 คุณ: {user.email}")

if st.button("ออกจากระบบ"):
    del st.session_state.user
    st.rerun()

st.divider()

# ฟอร์มบันทึก
with st.form("บันทึก", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        วันที่ = st.date_input("วันที่")
        รายการ = st.text_input("รายการ")
    with col2:
        ประเภท = st.selectbox("ประเภท", ["รายรับ", "รายจ่าย"])
        จำนวนเงิน = st.number_input("จำนวนเงิน", min_value=0.0, step=1.0)
    
    if st.form_submit_button("บันทึก", type="primary"):
        supabase.table("entries").insert({
            "user_id": user.id,
            "date": วันที่.isoformat(),
            "title": รายการ,
            "type": ประเภท,
            "amount": จำนวนเงิน
        }).execute()
        st.success("✅ บันทึกสำเร็จ!")
        st.rerun()

st.divider()

# แสดงข้อมูลเฉพาะของคนนี้
res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()

if res.data:
    df = pd.DataFrame(res.data)
    df = df[["date", "title", "type", "amount"]]
    df.columns = ["วันที่", "รายการ", "ประเภท", "จำนวนเงิน"]
    
    รวมรับ = df[df["ประเภท"] == "รายรับ"]["จำนวนเงิน"].sum()
    รวมจ่าย = df[df["ประเภท"] == "รายจ่าย"]["จำนวนเงิน"].sum()
    คงเหลือ = รวมรับ - รวมจ่าย
    
    col1, col2, col3 = st.columns(3)
    col1.metric("รวมรายรับ", f"{รวมรับ:,.2f} บาท")
    col2.metric("รวมรายจ่าย", f"{รวมจ่าย:,.2f} บาท")
    col3.metric("คงเหลือ", f"{คงเหลือ:,.2f} บาท")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("📋 ยังไม่มีข้อมูล เริ่มบันทึกกันเลย!")
                              

import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(
    page_title="บันทึกรายรับ-รายจ่าย",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }
    .stButton>button, .stFormSubmitButton>button {
        border-radius: 14px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    button[kind="primary"] {
        background: linear-gradient(90deg, #22c55e, #16a34a) !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(90deg, #16a34a, #15803d) !important;
        transform: translateY(-2px);
    }
    button[kind="secondary"] {
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important;
    }
    button[kind="secondary"]:hover {
        background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
        transform: translateY(-2px);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a, #1e40af) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    label {
        font-weight: 600;
        color: #1e40af;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()
if not supabase:
    st.error("ตั้งค่า Secrets ไม่ครบ")
    st.stop()

if "user" not in st.session_state:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except Exception:
        pass

if "user" not in st.session_state:
    st.title("บันทึกรายรับ-รายจ่าย")
    tab1, tab2 = st.tabs(["เข้าสู่ระบบ", "ลงทะเบียน"])
    with tab1:
        st.subheader("เข้าสู่ระบบ")
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    with tab2:
        st.subheader("ลงทะเบียน")
        email2 = st.text_input("อีเมล", key="reg_email")
        password2 = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        if st.button("ลงทะเบียน", type="primary", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": email2, "password": password2})
                st.success("สำเร็จ! ตรวจสอบอีเมลของคุณ")
            except Exception as e:
                st.error(f"ไม่สำเร็จ: {e}")
    st.stop()

user = st.session_state.user
st.title(f"ยินดีต้อนรับ {user.email}")

menu = st.sidebar.radio("เมนู", [
    "เพิ่มรายการ",
    "ดูรายการทั้งหมด",
    "ค้นหา",
    "ส่งออกข้อมูล",
    "แก้ไขและลบรายการ",
    "จัดการบัญชี"
])

if st.sidebar.button("ออกจากระบบ", type="secondary"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

if menu == "เพิ่มรายการ":
    st.subheader("เพิ่มรายการใหม่")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("วันที่", value=datetime.today())
        with col2:
            typ = st.radio("ประเภท", ["รายรับ", "รายจ่าย"])
        title = st.text_input("ชื่อรายการ")
        amount = st.number_input("จำนวนเงิน", min_value=0.0, step=1.0)
        if st.form_submit_button("บันทึก", type="primary"):
            if not title or amount <= 0:
                st.error("กรอกข้อมูลให้ครบถ้วน")
            else:
                supabase.table("entries").insert({
                    "user_id": user.id,
                    "date": date.isoformat(),
                    "title": title,
                    "type": typ,
                    "amount": amount
                }).execute()
                st.success("บันทึกสำเร็จ!")
                st.rerun()

elif menu == "ดูรายการทั้งหมด":
    st.subheader("รายการทั้งหมด")
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        income = df[df["type"]=="รายรับ"]["amount"].sum()
        expense = df[df["type"]=="รายจ่าย"]["amount"].sum()
        balance = income - expense
        st.write(f"รายรับรวม: {income:,.2f} บาท")
        st.write(f"รายจ่ายรวม: {expense:,.2f} บาท")
        st.write(f"คงเหลือ: {balance:,.2f} บาท")
        st.dataframe(df[["date", "title", "type", "amount"]], use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีรายการ")

elif menu == "ค้นหา":
    st.subheader("ค้นหารายการ")
    keyword = st.text_input("พิมพ์คำที่ต้องการค้นหา")
    if keyword:
        res = supabase.table("entries").select("*").eq("user_id", user.id).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            mask = df["title"].str.contains(keyword, case=False, na=False)
            df = df[mask]
            if df.empty:
                st.info("ไม่พบรายการ")
            else:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
                st.dataframe(df[["date", "title", "type", "amount"]], use_container_width=True, hide_index=True)

elif menu == "ส่งออกข้อมูล":
    st.subheader("ส่งออกข้อมูล")
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("ดาวน์โหลด CSV", data=csv, file_name="รายรับรายจ่าย.csv", mime="text/csv")
    else:
        st.info("ไม่มีข้อมูล")

elif menu == "แก้ไขและลบรายการ":
    st.subheader("แก้ไขหรือลบรายการ")
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if not res.data:
        st.info("ไม่มีรายการ")
        st.stop()
    df = pd.DataFrame(res.data)
    selected_title = st.selectbox("เลือกรายการ", ["-- เลือก --"] + list(df["title"]))
    if selected_title != "-- เลือก --":
        row = df[df["title"] == selected_title].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("แก้ไข")
            with st.form("edit_form"):
                new_date = st.date_input("วันที่", value=pd.to_datetime(row["date"]))
                new_type = st.radio("ประเภท", ["รายรับ", "รายจ่าย"],
                    index=0 if row["type"]=="รายรับ" else 1)
                new_title = st.text_input("ชื่อรายการ", value=row["title"])
                new_amount = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]))
                if st.form_submit_button("บันทึกการแก้ไข", type="primary"):
                    supabase.table("entries").update({
                        "date": new_date.isoformat(),
                        "type": new_type,
                        "title": new_title,
                        "amount": new_amount
                    }).eq("id", row["id"]).execute()
                    st.success("อัปเดตสำเร็จ!")
                    st.rerun()
        with col2:
            st.subheader("ลบ")
            if "delete_id" not in st.session_state or st.session_state.delete_id != row["id"]:
                if st.button("ลบรายการนี้", type="secondary"):
                    st.session_state.delete_id = row["id"]
                    st.warning("กดยืนยันอีกครั้ง")
            else:
                if st.button("ยืนยันการลบ", type="primary"):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    del st.session_state.delete_id
                    st.success("ลบสำเร็จ!")
                    st.rerun()

elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    st.write(f"อีเมล: {user.email}")
    st.write(f"รหัสผู้ใช้: {user.id}")
        

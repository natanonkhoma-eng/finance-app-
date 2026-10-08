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

# --- ล้างข้อมูลทันทีเมื่อออกจากระบบ ---
if "_LOGOUT" in st.session_state and st.session_state._LOGOUT:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.markdown("""
<style>
    .stApp { background: #f0f6ff; }
    .block-container { padding: 1.5rem 1rem 2rem; }
    h1, h2, h3 { color: #002b80 !important; font-weight: 700; }
    p, label, div { color: #001a4d !important; line-height: 1.5; }
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input, 
    .stDateInput>div>div>input {
        background: #ffffff !important; color: #000000 !important;
        border: 2px solid #99c2ff !important; border-radius: 10px;
        padding: 0.75rem 1rem; font-size: 1rem;
    }
    .stButton>button, .stFormSubmitButton>button {
        border-radius: 12px; font-weight: 600;
        padding: 0.75rem 1.5rem; min-height: 3rem;
    }
    button[kind="primary"] { background: #0066ff !important; color: #fff !important; }
    button[kind="secondary"] { background: #dc2626 !important; color: #fff !important; }
    section[data-testid="stSidebar"] { background: #002b80 !important; }
    section[data-testid="stSidebar"] * { color: #fff !important; }
    label { font-weight: 600; color: #002b80 !important; }
    div[data-testid="stForm"] {
        background: #fff; border-radius: 16px; padding: 1.5rem;
        border: 2px solid #99c2ff;
    }
    .card {
        background: #fff; padding: 1.5rem; border-radius: 20px;
        border: 2px solid #99c2ff; margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
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

# --- ตรวจสอบผู้ใช้ใหม่ทุกครั้ง ไม่เชื่อค่าเก่า ---
def get_current_user():
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user
    except Exception:
        pass
    return None

user = get_current_user()

# --- ยังไม่เข้าสู่ระบบ ---
if not user:
    st.title("💰 บันทึกรายรับ-รายจ่าย")
    tab1, tab2 = st.tabs(["เข้าสู่ระบบ", "ลงทะเบียน"])
    
    with tab1:
        st.subheader("เข้าสู่ระบบ")
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
            if not email or not password:
                st.error("กรอกอีเมลและรหัสผ่าน")
            else:
                try:
                    supabase.auth.sign_out()
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.rerun()
                except Exception:
                    st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    
    with tab2:
        st.subheader("ลงทะเบียน")
        email2 = st.text_input("อีเมล", key="reg_email")
        password2 = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        if st.button("สร้างบัญชี", type="primary", use_container_width=True):
            if not email2 or not password2:
                st.error("กรอกข้อมูลให้ครบ")
            else:
                try:
                    supabase.auth.sign_up({"email": email2, "password": password2})
                    st.success("สำเร็จ! ตรวจสอบอีเมลของคุณ")
                except Exception as e:
                    st.error(f"ไม่สำเร็จ: {e}")
    st.stop()

# --- แสดงข้อมูลผู้ใช้ ---
st.markdown(f"""
<div class="card">
    <h2 style="margin:0;">👋 ยินดีต้อนรับ</h2>
    <p style="margin:0.5rem 0 0;">📧 {user.email}</p>
    <p style="margin:0.25rem 0 0; font-size:0.9rem; color:#666;">🆔 รหัสผู้ใช้ของฉัน: {user.id}</p>
    <p style="margin:0.5rem 0 0; color:#008040; font-weight:600;">✅ ข้อมูลของคุณแยกอิสระ — เข้าพร้อมกันก็ไม่ปนกัน</p>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("เมนู", [
    "เพิ่มรายการ",
    "ดูรายการทั้งหมด",
    "ค้นหา",
    "ส่งออกข้อมูล",
    "แก้ไขและลบรายการ",
    "จัดการบัญชี"
])

# --- ปุ่มออกจากระบบ ---
if st.sidebar.button("🚪 ออกจากระบบ", type="secondary", use_container_width=True):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state._LOGOUT = True
    st.rerun()

# ==================================================
# ทุกคำสั่งมี .eq("user_id", user.id) — กรองเฉพาะของเรา
# ==================================================

if menu == "เพิ่มรายการ":
    st.subheader("เพิ่มรายการใหม่")
    st.markdown("---")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("วันที่", value=datetime.today())
        with col2:
            typ = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        title = st.text_input("ชื่อรายการ")
        amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=1.0, format="%.2f")
        if st.form_submit_button("บันทึก", type="primary", use_container_width=True):
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
    st.subheader("รายการของฉัน")
    st.markdown("---")
    # ✅ ดึงเฉพาะของเรา
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        income = df[df["type"]=="รายรับ"]["amount"].sum()
        expense = df[df["type"]=="รายจ่าย"]["amount"].sum()
        balance = income - expense
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div style="background:#e6fff2; padding:1.2rem; border-radius:16px; border:2px solid #99ffcc;">
                <p style="margin:0; color:#006633; font-weight:600;">รายรับรวม</p>
                <h3 style="margin:0; color:#008040;">+{income:,.2f} บาท</h3>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:#ffe6e6; padding:1.2rem; border-radius:16px; border:2px solid #ffb3b3;">
                <p style="margin:0; color:#800000; font-weight:600;">รายจ่ายรวม</p>
                <h3 style="margin:0; color:#cc0000;">-{expense:,.2f} บาท</h3>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            bal_color = "#008040" if balance >= 0 else "#cc0000"
            st.markdown(f"""
            <div style="background:#e6f0ff; padding:1.2rem; border-radius:16px; border:2px solid #99c2ff;">
                <p style="margin:0; color:#002b80; font-weight:600;">คงเหลือ</p>
                <h3 style="margin:0; color:{bal_color};">{balance:,.2f} บาท</h3>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df[["date", "title", "type", "amount"]], use_container_width=True, hide_index=True)
    else:
        st.info("📭 ยังไม่มีรายการของคุณ — คนอื่นมองไม่เห็นส่วนนี้")

elif menu == "ค้นหา":
    st.subheader("ค้นหาในรายการของฉัน")
    st.markdown("---")
    keyword = st.text_input("พิมพ์คำที่ต้องการค้นหา")
    if keyword:
        res = supabase.table("entries").select("*").eq("user_id", user.id).execute()  # ✅
        if res.data:
            df = pd.DataFrame(res.data)
            mask = df["title"].str.contains(keyword, case=False, na=False)
            df = df[mask]
            if df.empty:
                st.info("🔍 ไม่พบรายการของคุณ")
            else:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
                st.dataframe(df[["date", "title", "type", "amount"]], use_container_width=True, hide_index=True)

elif menu == "ส่งออกข้อมูล":
    st.subheader("ส่งออกข้อมูลของฉัน")
    st.markdown("---")
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()  # ✅
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("ดาวน์โหลด CSV", data=csv, file_name="รายรับรายจ่าย.csv", type="primary")
    else:
        st.info("📭 ไม่มีข้อมูล")

elif menu == "แก้ไขและลบรายการ":
    st.subheader("แก้ไขหรือลบรายการของฉัน")
    st.markdown("---")
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()  # ✅
    if not res.data:
        st.info("📭 ไม่มีรายการ")
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
                    index=0 if row["type"]=="รายรับ" else 1, horizontal=True)
                new_title = st.text_input("ชื่อรายการ", value=row["title"])
                new_amount = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]), format="%.2f")
                if st.form_submit_button("บันทึกการแก้ไข", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": new_date.isoformat(),
                        "type": new_type,
                        "title": new_title,
                        "amount": new_amount
                    }).eq("id", row["id"]).eq("user_id", user.id).execute()  # ✅ ป้องกันแก้ของคนอื่น
                    st.success("อัปเดตสำเร็จ!")
                    st.rerun()
        with col2:
            st.subheader("ลบ")
            if "del_confirm" not in st.session_state or st.session_state.del_confirm != row["id"]:
                if st.button("ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_confirm = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยัน")
            else:
                if st.button("ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).eq("user_id", user.id).execute()  # ✅
                    del st.session_state.del_confirm
                    st.success("ลบสำเร็จ!")
                    st.rerun()

elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชีของฉัน")
    st.markdown("---")
    st.markdown(f"""
    <div class="card">
        <p><strong>📧 อีเมล:</strong> {user.email}</p>
        <p><strong>🆔 รหัสผู้ใช้:</strong> {user.id}</p>
        <p style="color:#008040; font-weight:600;">🔒 ระบบแยกข้อมูลอัตโนมัติ — เข้าพร้อมกันก็ไม่ปนกัน</p>
    </div>
    """, unsafe_allow_html=True)
    

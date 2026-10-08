import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ========== ล้างค่าเก่าทิ้งก่อนเริ่ม ==========
for key in list(st.session_state.keys()):
    del st.session_state[key]
# =============================================

st.set_page_config(
    page_title="บันทึกรายรับ-รายจ่าย",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background: #f0f6ff; }
    .block-container { padding: 1.5rem 1rem 2rem; }
    h1, h2, h3 { color: #002b80 !important; font-weight: 700; }
    p, label, div { color: #001a4d !important; line-height: 1.5; }
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input, 
    .stDateInput>div>div>input {
        background: #fff !important; color: #000 !important;
        border: 2px solid #99c2ff !important; border-radius: 10px;
        padding: 0.75rem 1rem; font-size: 1rem;
    }
    .stButton>button {
        border-radius: 12px; font-weight: 600;
        padding: 0.75rem 1.5rem; min-height: 3rem;
    }
    button[kind="primary"] { background: #0066ff !important; color: #fff !important; }
    button[kind="secondary"] { background: #dc2626 !important; color: #fff !important; }
    section[data-testid="stSidebar"] { background: #002b80 !important; }
    section[data-testid="stSidebar"] * { color: #fff !important; }
    label { font-weight: 600; color: #002b80 !important; }
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

def get_user():
    try:
        s = supabase.auth.get_session()
        if s and s.user:
            return s.user
    except:
        pass
    return None

user = get_user()

if not user:
    try: supabase.auth.sign_out()
    except: pass

    st.markdown("# 💰 บันทึกรายรับ-รายจ่าย")
    tab1, tab2 = st.tabs(["🔐 เข้าสู่ระบบ", "✨ ลงทะเบียน"])
    
    with tab1:
        st.subheader("เข้าสู่ระบบ")
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        
        if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
            e = email.strip() if email else ""
            p = password.strip() if password else ""
            
            if not e or not p:
                st.error("❌ กรอกอีเมลและรหัสผ่าน")
            else:
                try:
                    supabase.auth.sign_out()
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.success("✅ เข้าสู่ระบบสำเร็จ!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"❌ เข้าไม่ได้: {str(ex)}")
    
    with tab2:
        st.subheader("ลงทะเบียน")
        reg_email = st.text_input("อีเมล", key="reg_email")
        reg_pass = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        
        if st.button("สร้างบัญชี", type="primary", use_container_width=True):
            re = reg_email.strip() if reg_email else ""
            rp = reg_pass.strip() if reg_pass else ""
            if not re or not rp:
                st.error("กรอกข้อมูลให้ครบ")
            else:
                try:
                    supabase.auth.sign_up({"email": re, "password": rp})
                    st.success("✅ สมัครสำเร็จ! ตรวจสอบอีเมล")
                except Exception as ex:
                    st.error(f"❌ ไม่สำเร็จ: {str(ex)}")
    st.stop()

# ========== หน้าหลัก ==========
st.markdown(f"""
<div class="card">
    <h2 style="margin:0;">👋 ยินดีต้อนรับ</h2>
    <p>📧 {user.email}</p>
    <p>🆔 {user.id}</p>
    <p style="color:green; font-weight:bold;">✅ เข้าสู่ระบบสำเร็จ — ข้อมูลแยกกัน</p>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("เมนู", [
    "เพิ่มรายการ", "ดูรายการทั้งหมด", "ค้นหา",
    "ส่งออกข้อมูล", "แก้ไขและลบรายการ", "จัดการบัญชี"
])

if st.sidebar.button("🚪 ออกจากระบบ", type="secondary"):
    try: supabase.auth.sign_out()
    except: pass
    st.rerun()

if menu == "เพิ่มรายการ":
    st.subheader("เพิ่มรายการใหม่")
    with st.form("add", clear_on_submit=True):
        d = st.date_input("วันที่")
        t = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        n = st.text_input("ชื่อรายการ")
        a = st.number_input("จำนวนเงิน", min_value=0.0, format="%.2f")
        if st.form_submit_button("บันทึก", type="primary"):
            if not n or a <= 0: st.error("กรอกข้อมูลให้ครบ")
            else:
                supabase.table("entries").insert({
                    "user_id": user.id, "date": d.isoformat(),
                    "title": n, "type": t, "amount": a
                }).execute()
                st.success("✅ บันทึกสำเร็จ!")
                st.rerun()

elif menu == "ดูรายการทั้งหมด":
    st.subheader("รายการของฉัน")
    res = supabase.table("entries").select("*").order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        inc = df[df["type"]=="รายรับ"]["amount"].sum()
        exp = df[df["type"]=="รายจ่าย"]["amount"].sum()
        bal = inc - exp
        c1,c2,c3 = st.columns(3)
        with c1: st.info(f"รายรับรวม\n\n**+{inc:,.2f} บาท**")
        with c2: st.error(f"รายจ่ายรวม\n\n**-{exp:,.2f} บาท**")
        with c3: st.success(f"คงเหลือ\n\n**{bal:,.2f} บาท**")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 ยังไม่มีรายการของคุณ")

elif menu == "ค้นหา":
    kw = st.text_input("ค้นหารายการ")
    if kw:
        res = supabase.table("entries").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df[df["title"].str.contains(kw, case=False, na=False)]
            if df.empty: st.info("ไม่พบ")
            else: st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "ส่งออกข้อมูล":
    res = supabase.table("entries").select("*").order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 ดาวน์โหลด CSV", data=csv, file_name="รายรับรายจ่าย.csv", type="primary")
    else:
        st.info("ไม่มีข้อมูล")

elif menu == "แก้ไขและลบรายการ":
    res = supabase.table("entries").select("*").order("date", desc=True).execute()
    if not res.data: st.info("ไม่มีรายการ"); st.stop()
    df = pd.DataFrame(res.data)
    sel = st.selectbox("เลือกรายการ", ["-- เลือก --"] + list(df["title"]))
    if sel != "-- เลือก --":
        row = df[df["title"]==sel].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("แก้ไข")
            with st.form("edit"):
                nd = st.date_input("วันที่", value=pd.to_datetime(row["date"]))
                nt = st.radio("ประเภท", ["รายรับ","รายจ่าย"], 0 if row["type"]=="รายรับ" else 1)
                nn = st.text_input("ชื่อรายการ", value=row["title"])
                na = st.number_input("จำนวนเงิน", value=float(row["amount"]), format="%.2f")
                if st.form_submit_button("บันทึก", type="primary"):
                    supabase.table("entries").update({
                        "date": nd.isoformat(), "type": nt, "title": nn, "amount": na
                    }).eq("id", row["id"]).execute()
                    st.success("✅ อัปเดตสำเร็จ"); st.rerun()
        with col2:
            st.subheader("ลบ")
            if "del_ok" not in st.session_state or st.session_state.del_ok != row["id"]:
                if st.button("ลบรายการนี้", type="secondary"):
                    st.session_state.del_ok = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยัน")
            else:
                if st.button("ยืนยันการลบ", type="primary"):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    del st.session_state.del_ok
                    st.success("✅ ลบสำเร็จ"); st.rerun()

elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชีของฉัน")
    st.markdown(f"""
    <div class="card">
        <p><strong>📧 อีเมล:</strong> {user.email}</p>
        <p><strong>🆔 รหัสผู้ใช้:</strong> {user.id}</p>
        <p style="color:green; font-weight:bold;">🔒 ปลอดภัย — ข้อมูลแยกกัน</p>
    </div>
    """, unsafe_allow_html=True)
        

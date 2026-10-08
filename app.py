import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ─────────────────── ตั้งค่าหน้าเว็บ ───────────────────
st.set_page_config(
    page_title="💰 บันทึกรายรับ-รายจ่าย",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────── ปรับแต่งสีและสไตล์ ───────────────────
st.markdown("""
<style>
    /* พื้นหลังหลัก */
    .stApp {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    }
    
    /* กล่องเนื้อหา */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    
    /* การ์ด */
    .css-1r6slb0, .css-keje6w, div[data-testid="stVerticalBlock"] > div {
        background: #ffffff;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.1);
    }
    
    /* หัวข้อ */
    h1, h2, h3 {
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }
    
    /* ปุ่มทั่วไป */
    .stButton>button, .stFormSubmitButton>button {
        border-radius: 14px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    
    /* ปุ่มหลัก — สีเขียวสด */
    button[kind="primary"] {
        background: linear-gradient(90deg, #22c55e, #16a34a) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
    }
    button[kind="primary"]:hover {
        background: linear-gradient(90deg, #16a34a, #15803d) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
    }
    
    /* ปุ่มรอง — สีฟ้า */
    button[kind="secondary"] {
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important;
    }
    button[kind="secondary"]:hover {
        background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
        transform: translateY(-2px);
    }
    
    /* แถบด้านข้าง */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a, #1e40af) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* กล่องข้อมูล */
    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    
    /* กล่องแจ้งเตือน */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    
    /* ป้ายอินพุต */
    label {
        font-weight: 600;
        color: #1e40af;
    }
    
    /* กล่องอินพุต */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input {
        border-radius: 10px !important;
        border: 1px solid #bfdbfe !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────── เชื่อมต่อฐานข้อมูล ───────────────────
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()
if not supabase:
    st.error("⚠️ ตั้งค่า Secrets ไม่ครบ")
    st.stop()

# ─────────────────── ตรวจสอบการเข้าสู่ระบบ ───────────────────
if "user" not in st.session_state:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except Exception:
        pass

if "user" not in st.session_state:
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 2.4rem;'>💰 บันทึกรายรับ-รายจ่าย</h1>
        <p style='font-size: 1.1rem; color: #64748b;'>จัดการเงินของคุณให้เป็นระเบียบ สวยงาม และง่ายต่อการใช้งาน</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 เข้าสู่ระบบ", "✨ ลงทะเบียน"])
    with tab1:
        st.subheader("เข้าสู่ระบบบัญชีของคุณ")
        email = st.text_input("📧 อีเมล", key="login_email")
        password = st.text_input("🔒 รหัสผ่าน", type="password", key="login_pass")
        if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception:
                st.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    with tab2:
        st.subheader("สร้างบัญชีใหม่")
        e2 = st.text_input("📧 อีเมล", key="reg_email")
        p2 = st.text_input("🔒 รหัสผ่าน", type="password", key="reg_pass")
        if st.button("สร้างบัญชี", type="primary", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": e2, "password": p2})
                st.success("✅ สำเร็จ! กรุณาตรวจสอบอีเมลเพื่อยืนยันบัญชี")
            except Exception as e:
                st.error(f"❌ ไม่สำเร็จ: {e}")
    st.stop()

# ─────────────────── หน้าหลัก ───────────────────
user = st.session_state.user

st.markdown(f"""
<div style='background: white; padding: 1.5rem; border-radius: 20px; box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08); margin-bottom: 2rem;'>
    <h2 style='margin: 0;'>👋 ยินดีต้อนรับ</h2>
    <p style='color: #64748b; margin: 0.5rem 0 0 0; font-size: 1.05rem;'>{user.email}</p>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("📋 เมนูหลัก", [
    "➕ เพิ่มรายการ",
    "📋 ดูรายการทั้งหมด",
    "🔍 ค้นหา",
    "📤 ส่งออกข้อมูล",
    "✏️ แก้ไขและลบรายการ",
    "⚙️ จัดการบัญชี"
])

if st.sidebar.button("🚪 ออกจากระบบ", type="secondary", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ─────────────────── เพิ่มรายการ ───────────────────
if menu == "➕ เพิ่มรายการ":
    st.subheader("➕ เพิ่มรายการใหม่")
    st.markdown("---")
    
    with st.form("add", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            d = st.date_input("📅 วันที่", value=datetime.today())
        with col2:
            t = st.radio("💵 ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        
        n = st.text_input("📝 ชื่อรายการ")
        a = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, step=1.0, format="%.2f")
        
        if st.form_submit_button("✅ บันทึก", type="primary", use_container_width=True):
            if not n or a <= 0:
                st.error("❌ กรอกข้อมูลให้ครบถ้วน")
            else:
                supabase.table("entries").insert({
                    "user_id": user.id,
                    "date": d.isoformat(),
                    "title": n,
                    "type": t,
                    "amount": a
                }).execute()
                st.success("✅ บันทึกสำเร็จ! ข้อมูลถูกบันทึกเรียบร้อยแล้ว 🎉")
                st.rerun()

# ─────────────────── ดูรายการทั้งหมด ───────────────────
elif menu == "📋 ดูรายการทั้งหมด":
    st.subheader("📋 รายการทั้งหมด")
    st.markdown("---")
    
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
            <div style='background: #dcfce7; padding: 1.2rem; border-radius: 16px; text-align: center;'>
                <p style='margin:0; color:#166534; font-weight:600;'>📈 รายรับรวม</p>
                <h3 style='margin:0; color:#15803d;'>+{income:,.2f} บาท</h3>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style='background: #fee2e2; padding: 1.2rem; border-radius: 16px; text-align: center;'>
                <p style='margin:0; color:#991b1b; font-weight:600;'>📉 รายจ่ายรวม</p>
                <h3 style='margin:0; color:#dc2626;'>-{expense:,.2f} บาท</h3>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            bal_color = "#15803d" if balance >= 0 else "#dc2626"
            st.markdown(f"""
            <div style='background: #dbeafe; padding: 1.2rem; border-radius: 16px; text-align: center;'>
                <p style='margin:0; color:#1e40af; font-weight:600;'>💰 คงเหลือ</p>
                <h3 style='margin:0; color:{bal_color};'>{balance:,.2f} บาท</h3>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(
            df[["date", "title", "type", "amount"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📭 ยังไม่มีรายการ")

# ─────────────────── ค้นหา ───────────────────
elif menu == "🔍 ค้นหา":
    st.subheader("🔍 ค้นหารายการ")
    st.markdown("---")
    
    kw = st.text_input("พิมพ์คำที่ต้องการค้นหา...", placeholder="เช่น ค่าอาหาร, เงินเดือน")
    if kw:
        res = supabase.table("entries").select("*").eq("user_id", user.id).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            mask = df["title"].str.contains(kw, case=False, na=False) | df["type"].str.contains(kw, case=False, na=False)
            df = df[mask]
            if df.empty:
                st.info("🔍 ไม่พบรายการที่ตรงกับคำค้น")
            else:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
                st.dataframe(df[["date", "title", "type", "amount"]], use_container_width=True, hide_index=True)
        else:
            st.info("📭 ยังไม่มีข้อมูล")

# ─────────────────── ส่งออกข้อมูล ───────────────────
elif menu == "📤 ส่งออกข้อมูล":
    st.subheader("📤 ส่งออกข้อมูล")
    st.markdown("---")
    
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ CSV",
            data=csv,
            file_name=f"บันทึกรายรับรายจ่าย_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
    else:
        st.info("📭 ยังไม่มีข้อมูลสำหรับส่งออก")

# ─────────────────── แก้ไขและลบ ───────────────────
elif menu == "✏️ แก้ไขและลบรายการ":
    st.subheader("✏️ แก้ไขหรือลบรายการ")
    st.markdown("---")
    
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if not res.data:
        st.info("📭 ไม่มีรายการ")
        st.stop()
    
    df = pd.DataFrame(res.data)
    sel = st.selectbox("เลือกรายการ...", ["-- เลือก --"] + list(df["title"]))
    
    if sel != "-- เลือก --":
        row = df[df["title"] == sel].iloc[0]
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✏️ แก้ไข")
            with st.form("edit"):
                ed = st.date_input("📅 วันที่", value=pd.to_datetime(row["date"]))
                et = st.radio("💵 ประเภท", ["รายรับ", "รายจ่าย"],
                    index=0 if row["type"] == "รายรับ" else 1, horizontal=True)
                en = st.text_input("📝 ชื่อรายการ", value=row["title"])
                ea = st.number_input("💰 จำนวนเงิน", min_value=0.0, value=float(row["amount"]), format="%.2f")
                
                if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": ed.isoformat(),
                        "type": et,
                        "title": en,
                        "amount": ea
                    }).eq("id", row["id"]).execute()
                    st.success("✅ บันทึกสำเร็จ! ข้อมูลถูกอัปเดตเรียบร้อยแล้ว 🎉")
                    st.rerun()
        
        with col2:
            st.subheader("🗑️ ลบ")
            if "del_id" not in st.session_state or st.session_state.del_id != row["id"]:
                if st.button("🗑️ ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_id = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยันการลบ")
            else:
                if st.button("✅ ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    del st.session_state.del_id
                    st.success("✅ ลบสำเร็จ! ข้อมูลถูกลบเรียบร้อยแล้ว 🎉")
                    st.rerun()

# ─────────────────── จัดการบัญชี ───────────────────
elif menu == "⚙️ จัดการบัญชี":
    st.subheader("⚙️ ข้อมูลบัญชี")
    st.markdown("---")
    
    st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 20px; box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08);'>
        <p style='font-size: 1.1rem;'><strong>📧 อีเมล:</strong> {user.email}</p>
        <p style='font-size: 1.1rem;'><strong>🆔 รหัสผู้ใช้:</strong> {user.id}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("🚧 ฟีเจอร์อื่นๆ จะมาเร็วๆ นี้นะครับ!")
if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ CSV",
            data=csv,
            file_name=f"บันทึกรายรับรายจ่าย_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
    else:
        st.info("📭 ยังไม่มีข้อมูลสำหรับส่งออก")

# ─────────────────── แก้ไขและลบ ───────────────────
elif menu == "✏️ แก้ไขและลบรายการ":
    st.subheader("✏️ แก้ไขหรือลบรายการ")
    st.markdown("---")
    
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if not res.data:
        st.info("📭 ไม่มีรายการ")
        st.stop()
    
    df = pd.DataFrame(res.data)
    sel = st.selectbox("เลือกรายการ...", ["-- เลือก --"] + list(df["title"]))
    
    if sel != "-- เลือก --":
        row = df[df["title"] == sel].iloc[0]
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✏️ แก้ไข")
            with st.form("edit"):
                ed = st.date_input("📅 วันที่", value=pd.to_datetime(row["date"]))
                et = st.radio("💵 ประเภท", ["รายรับ", "รายจ่าย"],
                    index=0 if row["type"] == "รายรับ" else 1, horizontal=True)
                en = st.text_input("📝 ชื่อรายการ", value=row["title"])
                ea = st.number_input("💰 จำนวนเงิน", min_value=0.0, value=float(row["amount"]), format="%.2f")
                
                if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": ed.isoformat(),
                        "type": et,
                        "title": en,
                        "amount": ea
                    }).eq("id", row["id"]).execute()
                    st.success("✅ แก้ไขเรียบร้อย!")
                    st.rerun()
        
        with col2:
            st.subheader("🗑️ ลบ")
            if "del_id" not in st.session_state or st.session_state.del_id != row["id"]:
                if st.button("🗑️ ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_id = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยันการลบ")
            else:
                if st.button("✅ ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    del st.session_state.del_id
                    st.success("✅ ลบเรียบร้อย!")
                    st.rerun()

# ─────────────────── จัดการบัญชี ───────────────────
elif menu == "⚙️ จัดการบัญชี":
    st.subheader("⚙️ ข้อมูลบัญชี")
    st.markdown("---")
    
    st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);'>
        <p style='font-size: 1.1rem;'><strong>📧 อีเมล:</strong> {user.email}</p>
        <p style='font-size: 1.1rem;'><strong>🆔 รหัสผู้ใช้:</strong> {user.id}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("🚧 ฟีเจอร์อื่นๆ จะมาเร็วๆ นี้นะครับ!")
                

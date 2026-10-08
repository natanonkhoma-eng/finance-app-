import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ล้างค่าเก่าทิ้งก่อนเริ่ม
for key in list(st.session_state.keys()):
    del st.session_state[key]

st.set_page_config(
    page_title="บันทึกรายรับ-รายจ่าย",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { 
        background: #d4f8d4 !important;  /* พื้นหลังเขียวอ่อน */
    }
    .block-container { padding: 1.5rem 1rem 2rem; }
    
    /* ข้อความทั้งหมดสีดำเหมือนเดิม */
    p, label, div, span, h1, h2, h3, h4, h5, h6 { 
        color: #000000 !important; 
    }
    
    /* กล่องกรอกข้อมูล */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input, 
    .stDateInput>div>div>input,
    .stPasswordInput>div>div>input {
        background: #ffffff !important; 
        color: #000000 !important;
        border: 2px solid #90ee90 !important; 
        border-radius: 10px;
        padding: 0.75rem 1rem; 
        font-size: 1rem;
    }
    
    /* ปุ่ม */
    .stButton>button {
        border-radius: 12px; 
        font-weight: 600;
        padding: 0.75rem 1.5rem; 
        min-height: 3rem;
    }
    button[kind="primary"] { 
        background: #22a822 !important; 
        color: #ffffff !important; 
    }
    button[kind="secondary"] { 
        background: #444444 !important; 
        color: #ffffff !important; 
    }
    
    /* แถบข้าง */
    section[data-testid="stSidebar"] { 
        background: #228822 !important; 
    }
    section[data-testid="stSidebar"] * { 
        color: #ffffff !important; 
    }
    
    label { 
        font-weight: 600; 
        color: #000000 !important; 
    }
    
    .card {
        background: rgba(255,255,255,0.7); 
        padding: 1.5rem; 
        border-radius: 20px;
        border: 2px solid #90ee90; 
        margin-bottom: 2rem;
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
    try: 
        supabase.auth.sign_out()
    except: 
        pass

    st.markdown("# 💰 บันทึกรายรับ-รายจ่าย")
    tab1, tab2, tab3 = st.tabs(["🔐 เข้าสู่ระบบ", "✨ ลงทะเบียน", "❓ ลืมรหัสผ่าน"])
    
    with tab1:
        st.subheader("เข้าสู่ระบบ")
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        
        if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
            e = email.strip() if email else ""
            p = password.strip() if password else ""
            
            # บอกชัดเจนว่าผิดตรงไหน
            if not e and not p:
                st.error("❌ ผิดทั้งคู่ — กรอกอีเมล และ รหัสผ่าน")
            elif not e:
                st.error("❌ ผิด — ยังไม่ได้กรอกอีเมล")
            elif not p:
                st.error("❌ ผิด — ยังไม่ได้กรอกรหัสผ่าน")
            else:
                try:
                    supabase.auth.sign_out()
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.success("✅ เข้าสู่ระบบสำเร็จ!")
                    st.rerun()
                except Exception as ex:
                    err_text = str(ex).lower()
                    # บอกสาเหตุที่แท้จริง
                    if "email not confirmed" in err_text:
                        st.error("❌ เข้าไม่ได้ เพราะ: ยังไม่ยืนยันอีเมล → ไปเปิดอีเมล กดลิงก์ที่ส่งไป")
                    elif "invalid login credentials" in err_text or "credentials" in err_text:
                        st.error("❌ เข้าไม่ได้ เพราะ: อีเมลหรือรหัสผ่านไม่ถูกต้อง → เช็คตัวสะกด ดูตัวใหญ่-เล็ก อย่ามีช่องว่างติด")
                    elif "too many requests" in err_text or "rate limit" in err_text:
                        st.error("❌ เข้าไม่ได้ เพราะ: กดผิดบ่อยเกินไป → รอ 15-30 นาทีแล้วลองใหม่")
                    elif "email not found" in err_text:
                        st.error("❌ เข้าไม่ได้ เพราะ: ไม่มีบัญชีนี้ → กดแท็บ 'ลงทะเบียน' สมัครก่อน")
                    else:
                        st.error(f"❌ เข้าไม่ได้ เพราะ: {str(ex)}")
    
    with tab2:
        st.subheader("ลงทะเบียน")
        reg_email = st.text_input("อีเมล", key="reg_email")
        reg_pass = st.text_input("ตั้งรหัสผ่าน (อย่างน้อย 6 ตัว)", type="password", key="reg_pass")
        
        if st.button("สร้างบัญชี", type="primary", use_container_width=True):
            re = reg_email.strip() if reg_email else ""
            rp = reg_pass.strip() if reg_pass else ""
            
            if not re and not rp:
                st.error("❌ กรอกอีเมล และ ตั้งรหัสผ่าน")
            elif not re:
                st.error("❌ ยังไม่ได้กรอกอีเมล")
            elif not rp:
                st.error("❌ ยังไม่ได้ตั้งรหัสผ่าน")
            elif len(rp) < 6:
                st.error(f"❌ รหัสผ่านสั้นไป — ต้อง 6 ตัวขึ้นไป (ตอนนี้มี {len(rp)} ตัว)")
            else:
                try:
                    supabase.auth.sign_up({"email": re, "password": rp})
                    st.success("✅ สมัครสำเร็จ! → ไปเปิดอีเมล กดลิงก์ยืนยัน กลับมาเข้าสู่ระบบ")
                except Exception as ex:
                    err_text = str(ex).lower()
                    if "email already registered" in err_text or "already exists" in err_text:
                        st.error("❌ มีบัญชีนี้แล้ว → ไปที่แท็บ 'เข้าสู่ระบบ' หรือ 'ลืมรหัสผ่าน'")
                    elif "invalid email" in err_text:
                        st.error("❌ รูปแบบอีเมลไม่ถูกต้อง → เช็คให้มี @ และ ชื่อเว็บต่อท้าย")
                    else:
                        st.error(f"❌ ไม่สำเร็จ: {str(ex)}")
    
    with tab3:
        st.subheader("ลืมรหัสผ่าน")
        reset_email = st.text_input("กรอกอีเมลที่ใช้สมัคร", key="reset_email")
        if st.button("ส่งลิงก์ตั้งรหัสผ่านใหม่", type="primary", use_container_width=True):
            re = reset_email.strip() if reset_email else ""
            if not re:
                st.error("❌ กรอกอีเมลที่ใช้สมัคร")
            else:
                try:
                    supabase.auth.reset_password_email(re)
                    st.success("✅ ส่งแล้ว! → ไปเปิดอีเมล กดลิงก์ ตั้งรหัสใหม่ แล้วกลับมาเข้า")
                except Exception as ex:
                    st.error(f"❌ ส่งไม่ได้: {str(ex)}")
    st.stop()

# ========== หน้าหลัก — ครบเหมือนเดิม ==========
st.markdown(f"""
<div class="card">
    <h2 style="margin:0;">👋 ยินดีต้อนรับ</h2>
    <p>📧 {user.email}</p>
    <p>🆔 {user.id}</p>
    <p style="font-weight:bold;">✅ ข้อมูลของคุณคนเดียว — ไม่มีใครเห็น</p>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("เมนู", [
    "เพิ่มรายการ", "ดูรายการทั้งหมด", "ค้นหา",
    "ส่งออกข้อมูล", "แก้ไขและลบรายการ", "จัดการบัญชี"
])

if st.sidebar.button("🚪 ออกจากระบบ", type="secondary"):
    try: 
        supabase.auth.sign_out()
    except: 
        pass
    st.rerun()

if menu == "เพิ่มรายการ":
    st.subheader("เพิ่มรายการใหม่")
    with st.form("add_form", clear_on_submit=True):
        d = st.date_input("วันที่")
        t = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        n = st.text_input("ชื่อรายการ", key="add_title")
        a = st.number_input("จำนวนเงิน", min_value=0.0, format="%.2f")
        if st.form_submit_button("บันทึก", type="primary"):
            if not n:
                st.error("❌ ยังไม่ได้กรอกชื่อรายการ")
            elif a <= 0:
                st.error("❌ จำนวนเงินต้องมากกว่า 0")
            else:
                supabase.table("entries").insert({
                    "user_id": user.id, 
                    "date": d.isoformat(),
                    "title": n, 
                    "type": t, 
                    "amount": a
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
        c1, c2, c3 = st.columns(3)
        with c1: 
            st.info(f"รายรับรวม\n\n**+{inc:,.2f} บาท**")
        with c2: 
            st.error(f"รายจ่ายรวม\n\n**-{exp:,.2f} บาท**")
        with c3: 
            st.success(f"คงเหลือ\n\n**{bal:,.2f} บาท**")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 ยังไม่มีรายการของคุณ")

elif menu == "ค้นหา":
    kw = st.text_input("พิมพ์เพื่อค้นหา", key="search_keyword")
    if kw:
        res = supabase.table("entries").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df[df["title"].str.contains(kw, case=False, na=False)]
            if df.empty: 
                st.info("🔍 ไม่พบรายการที่ตรงกับคำค้น")
            else: 
                st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "ส่งออกข้อมูล":
    res = supabase.table("entries").select("*").order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 ดาวน์โหลดไฟล์ CSV", data=csv, 
                           file_name="รายรับรายจ่าย.csv", type="primary")
    else:
        st.info("ไม่มีข้อมูลที่จะส่งออก")

elif menu == "แก้ไขและลบรายการ":
    res = supabase.table("entries").select("*").order("date", desc=True).execute()
    if not res.data: 
        st.info("ไม่มีรายการ")
        st.stop()
    df = pd.DataFrame(res.data)
    sel = st.selectbox("เลือกรายการที่ต้องการ", ["-- เลือก --"] + list(df["title"]), key="select_edit")
    
    if sel != "-- เลือก --":
        row = df[df["title"]==sel].iloc[0]
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("แก้ไข")
            with st.form("edit_form"):
                nd = st.date_input("วันที่", value=pd.to_datetime(row["date"]))
                nt = st.radio("ประเภท", ["รายรับ","รายจ่าย"], 
                             0 if row["type"]=="รายรับ" else 1)
                nn = st.text_input("ชื่อรายการ", value=row["title"], key="edit_title")
                na = st.number_input("จำนวนเงิน", value=float(row["amount"]), format="%.2f")
                if st.form_submit_button("บันทึกการแก้ไข", type="primary"):
                    supabase.table("entries").update({
                        "date": nd.isoformat(), 
                        "type": nt, 
                        "title": nn, 
                        "amount": na
                    }).eq("id", row["id"]).execute()
                    st.success("✅ อัปเดตสำเร็จ!")
                    st.rerun()
        
        with col2:
            st.subheader("ลบ")
            if "del_confirm" not in st.session_state or st.session_state.del_confirm != row["id"]:
                if st.button("ลบรายการนี้", type="secondary", key=f"del_btn_{row['id']}"):
                    st.session_state.del_confirm = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยันการลบ — กู้คืนไม่ได้")
            else:
                if st.button("ยืนยันการลบ", type="primary", key=f"del_ok_{row['id']}"):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    del st.session_state.del_confirm
                    st.success("✅ ลบสำเร็จ!")
                    st.rerun()

elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชีของฉัน")
    st.markdown(f"""
    <div class="card">
        <p><strong>📧 อีเมล:</strong> {user.email}</p>
        <p><strong>🆔 รหัสผู้ใช้:</strong> {user.id}</p>
        <p style="font-weight:bold;">🔒 ปลอดภัย — ข้อมูลคนเดียว</p>
    </div>
    """, unsafe_allow_html=True)
            

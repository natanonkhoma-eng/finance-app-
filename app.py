import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ล้างค่าค้างทั้งหมด
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
    .stApp { background: #d4f8d4 !important; }
    p, label, div, span, h1, h2, h3 { color: #000000 !important; }
    .stTextInput>div>div>input {
        background: #fff !important; color: #000 !important;
        border: 2px solid #90ee90 !important; border-radius: 10px;
        padding: 0.75rem 1rem; font-size: 1rem;
    }
    .stButton>button { border-radius: 12px; font-weight: 600; min-height: 3rem; }
    button[kind="primary"] { background: #22a822 !important; color: #fff !important; }
    button[kind="secondary"] { background: #444 !important; color: #fff !important; }
    section[data-testid="stSidebar"] { background: #228822 !important; color: #fff !important; }
    label { color: #000 !important; font-weight: 600; }
    .card { background: rgba(255,255,255,0.7); padding: 1.5rem; border-radius: 20px; border: 2px solid #90ee90; margin-bottom: 2rem; }
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
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user
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
        
        # ✅ เก็บค่าลงตัวแปรโดยตรงทันที ไม่ทับซ้อน
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_password")
        
        # ✅ อ่านค่าจากตัวแปรโดยตรง ไม่ใช่จากการประมวลผลซ้ำ
        e = email.strip()
        p = password.strip()
        
        st.write(f"📋 ตรวจสอบ: อีเมล=`{e}` | รหัส={len(p)} ตัว")
        
        if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
            if not e:
                st.error("❌ กรอกอีเมล")
            elif not p:
                st.error("❌ กรอกรหัสผ่าน")
            else:
                try:
                    supabase.auth.sign_out()
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.success("✅ เข้าสู่ระบบสำเร็จ! กำลังโหลด...")
                    st.rerun()
                except Exception as ex:
                    err = str(ex).lower()
                    if "email not confirmed" in err:
                        st.error("❌ ยังไม่ยืนยันอีเมล → เปิดอีเมล กดลิงก์ที่ส่งมา")
                    elif "invalid credential" in err or "login failed" in err:
                        st.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง → กด 'ลืมรหัสผ่าน' ตั้งใหม่")
                    elif "email not found" in err:
                        st.error("❌ ไม่มีบัญชีนี้ → ไปลงทะเบียน")
                    else:
                        st.error(f"❌ สาเหตุ: {str(ex)}")
    
    with tab2:
        st.subheader("ลงทะเบียน")
        reg_email = st.text_input("อีเมล", key="reg_email")
        reg_pass = st.text_input("รหัสผ่าน (6 ตัวขึ้นไป)", type="password", key="reg_pass")
        
        if st.button("สร้างบัญชี", type="primary", use_container_width=True):
            re = reg_email.strip()
            rp = reg_pass.strip()
            if not re or not rp:
                st.error("กรอกข้อมูลให้ครบ")
            elif len(rp) < 6:
                st.error("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")
            else:
                try:
                    supabase.auth.sign_up({"email": re, "password": rp})
                    st.success("✅ สมัครสำเร็จ! ไปเปิดอีเมล กดยืนยัน แล้วกลับมาเข้า")
                except Exception as ex:
                    st.error(f"❌ {str(ex)}")
    
    with tab3:
        st.subheader("ลืมรหัสผ่าน")
        reset_email = st.text_input("อีเมลที่ใช้สมัคร", key="reset_email")
        if st.button("ส่งลิงก์ตั้งรหัสใหม่", type="primary", use_container_width=True):
            re = reset_email.strip()
            if not re:
                st.error("กรอกอีเมล")
            else:
                try:
                    supabase.auth.reset_password_email(re)
                    st.success("✅ ส่งแล้ว! ไปเช็คอีเมล ตั้งรหัสใหม่ แล้วเข้าได้เลย")
                except Exception as ex:
                    st.error(f"❌ {str(ex)}")
    st.stop()

# ========== หน้าหลัก ==========
st.markdown(f"""
<div class="card">
    <h2 style="margin:0;">👋 ยินดีต้อนรับ</h2>
    <p>📧 {user.email}</p>
    <p>🆔 {user.id}</p>
    <p style="font-weight:bold; color:green;">✅ เข้าสู่ระบบสำเร็จ — ข้อมูลปลอดภัยแยกกัน</p>
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
                st.error("กรอกชื่อรายการ")
            elif a <= 0:
                st.error("จำนวนเงินต้องมากกว่า 0")
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
        c1, c2, c3 = st.columns(3)
        with c1: st.info(f"รายรับรวม\n\n**+{inc:,.2f} บาท**")
        with c2: st.error(f"รายจ่ายรวม\n\n**-{exp:,.2f} บาท**")
        with c3: st.success(f"คงเหลือ\n\n**{bal:,.2f} บาท**")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 ยังไม่มีรายการ")

elif menu == "ค้นหา":
    kw = st.text_input("ค้นหารายการ", key="search_kw")
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
    sel = st.selectbox("เลือกรายการ", ["-- เลือก --"] + list(df["title"]), key="select_item")
    if sel != "-- เลือก --":
        row = df[df["title"]==sel].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("แก้ไข")
            with st.form("edit_form"):
                nd = st.date_input("วันที่", value=pd.to_datetime(row["date"]))
                nt = st.radio("ประเภท", ["รายรับ","รายจ่าย"], 0 if row["type"]=="รายรับ" else 1)
                nn = st.text_input("ชื่อรายการ", value=row["title"], key="edit_title")
                na = st.number_input("จำนวนเงิน", value=float(row["amount"]), format="%.2f")
                if st.form_submit_button("บันทึก", type="primary"):
                    supabase.table("entries").update({
                        "date": nd.isoformat(), "type": nt, "title": nn, "amount": na
                    }).eq("id", row["id"]).execute()
                    st.success("✅ อัปเดตสำเร็จ"); st.rerun()
        with col2:
            st.subheader("ลบ")
            if "del_ok" not in st.session_state or st.session_state.del_ok != row["id"]:
                if st.button("ลบ", type="secondary", key=f"del_{row['id']}"):
                    st.session_state.del_ok = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยัน")
            else:
                if st.button("ยืนยัน", type="primary", key=f"del2_{row['id']}"):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    del st.session_state.del_ok
                    st.success("✅ ลบสำเร็จ"); st.rerun()

elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    st.markdown(f"""
    <div class="card">
        <p><strong>📧 อีเมล:</strong> {user.email}</p>
        <p><strong>🆔 รหัสผู้ใช้:</strong> {user.id}</p>
        <p style="color:green; font-weight:bold;">🔒 ปลอดภัย — ข้อมูลคนเดียว</p>
    </div>
    """, unsafe_allow_html=True)
        

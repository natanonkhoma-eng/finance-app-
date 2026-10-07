import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ---------- ตั้งค่าหน้าแอป ----------
st.set_page_config(
    page_title="บันทึกรายรับรายจ่าย",
    page_icon="💰",
    layout="wide"
)

# ---------- เชื่อมต่อ Supabase ----------
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

# ---------- ตรวจสอบผู้ใช้ ----------
if "user" not in st.session_state:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except Exception:
        pass

if "user" not in st.session_state:
    st.title("💰 บันทึกรายรับรายจ่าย")
    
    tab1, tab2 = st.tabs(["เข้าสู่ระบบ", "ลงทะเบียน"])
    
    with tab1:
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("เข้าสู่ระบบ", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("✅ เข้าสู่ระบบสำเร็จ!")
                st.rerun()
            except Exception:
                st.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    
    with tab2:
        email2 = st.text_input("อีเมล", key="reg_email")
        password2 = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        if st.button("สร้างบัญชี", type="primary"):
            try:
                supabase.auth.sign_up({"email": email2, "password": password2})
                st.success("✅ สร้างบัญชีสำเร็จ! ตรวจสอบอีเมลแล้วเข้าสู่ระบบ")
            except Exception as e:
                st.error(f"❌ ผิดพลาด: {e}")
    st.stop()

user = st.session_state.user

# ---------- หัวข้อ + ข้อมูลผู้ใช้ ----------
st.title(f"💰 บันทึกรายรับรายจ่าย")
st.write(f"👤 คุณ: {user.email}")

# ---------- เมนูด้านข้าง — เพิ่มครบทุกส่วน ----------
st.sidebar.header("เมนูหลัก")
menu = st.sidebar.radio(
    "เลือกทำงาน",
    [
        "เพิ่มรายการ",
        "ดูรายการทั้งหมด",
        "ค้นหา",
        "ส่งออกข้อมูล",
        "จัดการบัญชี"
    ]
)

st.sidebar.divider()

# ---------- ออกจากระบบ — แยกชัดเจน ----------
if st.sidebar.button("🚪 ออกจากระบบ", type="secondary"):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    del st.session_state.user
    st.rerun()

st.divider()

# ==================================================
# 1️⃣ เพิ่มรายการ
# ==================================================
if menu == "เพิ่มรายการ":
    st.subheader("➕ เพิ่มรายการใหม่")
    with st.form("add_form"):
        date = st.date_input("วันที่", value=datetime.today())
        typ = st.radio("ประเภท", ["รายรับ", "รายจ่าย"])
        item = st.text_input("รายการ")
        amount = st.number_input("จำนวนเงิน", min_value=0.0, step=1.0)
        note = st.text_input("หมายเหตุ (ถ้ามี)")
        
        if st.form_submit_button("บันทึก", type="primary"):
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

# ==================================================
# 2️⃣ ดูรายการทั้งหมด + สรุป
# ==================================================
elif menu == "ดูรายการทั้งหมด":
    st.subheader("📋 รายการทั้งหมด")
    
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df[["date", "title", "type", "amount"]]
        df.columns = ["วันที่", "รายการ", "ประเภท", "จำนวนเงิน"]
        
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

# ==================================================
# 3️⃣ ค้นหา
# ==================================================
elif menu == "ค้นหา":
    st.subheader("🔍 ค้นหารายการ")
    kw = st.text_input("พิมพ์คำที่ต้องการค้นหา")
    
    if kw:
        res = supabase.table("entries").select("*").eq("user_id", user.id).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            mask = (
                df["title"].str.contains(kw, case=False, na=False) |
                df["type"].str.contains(kw, case=False, na=False)
            )
            df = df[mask].copy()
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
                df = df[["date", "title", "type", "amount"]]
                df.columns = ["วันที่", "รายการ", "ประเภท", "จำนวนเงิน"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("ไม่พบรายการที่ตรงกับคำค้นหา")
        else:
            st.info("ยังไม่มีข้อมูลในระบบ")

# ==================================================
# 4️⃣ ส่งออกข้อมูล — ส่วนที่หายไป!
# ==================================================
elif menu == "ส่งออกข้อมูล":
    st.subheader("📤 ส่งออกข้อมูลสำรอง")
    
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df_export = df[["date", "title", "type", "amount"]]
        df_export.columns = ["วันที่", "รายการ", "ประเภท", "จำนวนเงิน"]
        
        st.dataframe(df_export, use_container_width=True, hide_index=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        
        # ส่งออก CSV
        csv = df_export.to_csv(index=False, encoding="utf-8-sig")
        col1.download_button(
            label="📥 ดาวน์โหลดไฟล์ CSV",
            data=csv,
            file_name=f"บันทึกการเงิน_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # ส่งออก JSON
        json_data = df_export.to_json(orient="records", force_ascii=False, indent=2)
        col2.download_button(
            label="📥 ดาวน์โหลดไฟล์ JSON",
            data=json_data,
            file_name=f"บันทึกการเงิน_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        st.success(f"✅ พบรายการทั้งหมด {len(df_export)} รายการ พร้อมส่งออกแล้ว")
    else:
        st.info("ยังไม่มีข้อมูล ไม่มีอะไรส่งออกครับ")

# ==================================================
# 5️⃣ จัดการบัญชี
# ==================================================
elif menu == "จัดการบัญชี":
    st.subheader("⚙️ จัดการบัญชี & ข้อมูล")
    
    st.write(f"📧 อีเมล: {user.email}")
    st.write(f"🆔 รหัสผู้ใช้: `{user.id}`")
    st.divider()
    
    # ล้างข้อมูล
    if st.button("🗑️ ล้างข้อมูลทั้งหมดของฉัน", type="secondary"):
        if "confirm_clear" not in st.session_state:
            st.session_state.confirm_clear = True
            st.warning("⚠️ กดอีกครั้งเพื่อยืนยัน — ข้อมูลจะหายไปตลอดกาล!")
        else:
            # ลบทุกรายการของผู้ใช้
            supabase.table("entries").delete().eq("user_id", user.id).execute()
            st.success("✅ ล้างข้อมูลเรียบร้อย")
            del st.session_state.confirm_clear
            st.rerun()
    
    st.divider()
    
    # ออกจากระบบ
    if st.button("🚪 ออกจากระบบทันที", type="primary"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

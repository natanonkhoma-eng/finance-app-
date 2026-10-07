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
                st.balloons()
                st.success("✅ เข้าสู่ระบบสำเร็จ! ยินดีต้อนรับกลับมา", icon="✅")
                st.rerun()
            except Exception:
                st.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง", icon="❌")
    
    with tab2:
        email2 = st.text_input("อีเมล", key="reg_email")
        password2 = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        if st.button("สร้างบัญชี", type="primary"):
            try:
                supabase.auth.sign_up({"email": email2, "password": password2})
                st.balloons()
                st.success("🎉 สมัครสมาชิกสำเร็จ!", icon="✅")
                st.info("📧 กรุณาตรวจสอบอีเมลเพื่อยืนยันบัญชี แล้วเข้าสู่ระบบ", icon="📧")
            except Exception as e:
                st.error(f"❌ สมัครไม่สำเร็จ: {e}", icon="❌")
    st.stop()

user = st.session_state.user

# ---------- หัวข้อ + ข้อมูลผู้ใช้ ----------
st.title(f"💰 บันทึกรายรับรายจ่าย")
st.write(f"👤 คุณ: {user.email}")

# ---------- เมนูด้านข้าง — ครบทุกส่วน ----------
st.sidebar.header("เมนูหลัก")
menu = st.sidebar.radio(
    "เลือกทำงาน",
    [
        "เพิ่มรายการ",
        "ดูรายการทั้งหมด",
        "ค้นหา",
        "ส่งออกข้อมูล",
        "แก้ไข & ลบรายการ",
        "จัดการบัญชี"
    ]
)

st.sidebar.divider()

if st.sidebar.button("🚪 ออกจากระบบ", type="secondary"):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
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
                st.error("❌ กรอกรายการและจำนวนเงินให้ครบ", icon="❌")
            else:
                supabase.table("entries").insert({
                    "user_id": user.id,
                    "date": date.isoformat(),
                    "title": item + (f" ({note})" if note else ""),
                    "type": typ,
                    "amount": amount
                }).execute()
                st.balloons()
                st.success("✅ บันทึกข้อมูลสำเร็จ!", icon="✅")
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
# 4️⃣ ส่งออกข้อมูล
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
        
        csv = df_export.to_csv(index=False, encoding="utf-8-sig")
        col1.download_button(
            label="📥 ดาวน์โหลดไฟล์ CSV",
            data=csv,
            file_name=f"บันทึกการเงิน_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        json_data = df_export.to_json(orient="records", force_ascii=False, indent=2)
        col2.download_button(
            label="📥 ดาวน์โหลดไฟล์ JSON",
            data=json_data,
            file_name=f"บันทึกการเงิน_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        st.success(f"✅ พบรายการทั้งหมด {len(df_export)} รายการ พร้อมส่งออกแล้ว", icon="✅")
    else:
        st.info("ยังไม่มีข้อมูล ไม่มีอะไรส่งออกครับ")

# ==================================================
# 5️⃣ แก้ไข & ลบรายการ
# ==================================================
elif menu == "แก้ไข & ลบรายการ":
    st.subheader("🔧 แก้ไขหรือลบรายการ")
    
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    
    if not res.data:
        st.info("ยังไม่มีรายการที่จะแก้ไข")
        st.stop()
    
    df = pd.DataFrame(res.data)
    df["display_date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["label"] = df["display_date"] + " | " + df["type"] + " | " + df["title"] + " | " + df["amount"].astype(str) + " บาท"
    
    selected_label = st.selectbox("เลือกรายการที่ต้องการแก้ไข/ลบ", ["-- เลือก --"] + list(df["label"]))
    
    if selected_label != "-- เลือก --":
        row = df[df["label"] == selected_label].iloc[0]
        st.divider()
        st.subheader(f"จัดการ: {row['title']}")
        
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            st.subheader("✏️ แก้ไขข้อมูล")
            with st.form("edit_form"):
                edit_date = st.date_input("วันที่", value=pd.to_datetime(row["date"]))
                edit_type = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], 
                                     index=0 if row["type"] == "รายรับ" else 1)
                edit_title = st.text_input("รายการ", value=row["title"])
                edit_amount = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]))
                
                if st.form_submit_button("✅ บันทึกการแก้ไข"):
                    supabase.table("entries").update({
                        "date": edit_date.isoformat(),
                        "type": edit_type,
                        "title": edit_title,
                        "amount": edit_amount
                    }).eq("id", row["id"]).execute()
                    st.success("✅ แก้ไขข้อมูลเรียบร้อยแล้ว", icon="✅")
                    st.rerun()
        
        with col_del:
            st.subheader("🗑️ ลบรายการนี้")
            if "del_conf" not in st.session_state or st.session_state.del_conf != row["id"]:
                if st.button("🗑️ ลบรายการนี้", type="secondary"):
                    st.session_state.del_conf = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยันลบ — กู้คืนไม่ได้!", icon="⚠️")
            else:
                if st.button("✅ ยืนยันลบ", type="primary"):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    st.success("✅ ลบรายการสำเร็จ!", icon="✅")
                    del st.session_state.del_conf
                    st.rerun()

# ==================================================
# 6️⃣ จัดการบัญชี
# ==================================================
elif menu == "จัดการบัญชี":
    st.subheader("⚙️ จัดการบัญชี & ข้อมูล")
    
    st.write(f"📧 อีเมล: {user.email}")
    st.write(f"🆔 รหัสผู้ใช้: `{user.id}`")
    st.divider()
    
    if st.button("🗑️ ล้างข้อมูลทั้งหมดของฉัน", type="secondary"):
        if "clear_all_conf" not in st.session_state:
            st.session_state.clear_all_conf = True
            st.warning("⚠️ กดอีกครั้งเพื่อยืนยัน — ข้อมูลทั้งหมดจะหายไป!", icon="⚠️")
        else:
            supabase.table("entries").delete().eq("user_id", user.id).execute()
            st.success("✅ ล้างข้อมูลทั้งหมดเรียบร้อย", icon="✅")
            del st.session_state.clear_all_conf
            st.rerun()
    
    st.divider()
    
    if st.button("🚪 ออกจากระบบทันที", type="primary"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

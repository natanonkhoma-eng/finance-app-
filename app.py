import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(
    page_title="บันทึกรายรับรายจ่าย",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.title("บันทึกรายรับรายจ่าย")
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
        st.subheader("สร้างบัญชีใหม่")
        e2 = st.text_input("อีเมล", key="reg_email")
        p2 = st.text_input("รหัสผ่าน", type="password", key="reg_pass")
        if st.button("สร้างบัญชี", type="primary", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": e2, "password": p2})
                st.success("สำเร็จ กรุณาตรวจสอบอีเมล")
            except Exception as e:
                st.error(f"ไม่สำเร็จ: {e}")
    st.stop()

user = st.session_state.user
st.title("บันทึกรายรับรายจ่าย")
st.write(f"ยินดีต้อนรับ: {user.email}")

menu = st.sidebar.radio("เมนู", [
    "เพิ่มรายการ",
    "ดูรายการทั้งหมด",
    "ค้นหา",
    "ส่งออกข้อมูล",
    "แก้ไขและลบรายการ",
    "จัดการบัญชี"
])

if st.sidebar.button("ออกจากระบบ", type="secondary", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

if menu == "เพิ่มรายการ":
    st.subheader("เพิ่มรายการใหม่")
    with st.form("add"):
        d = st.date_input("วันที่", value=datetime.today())
        t = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], horizontal=True)
        n = st.text_input("ชื่อรายการ")
        a = st.number_input("จำนวนเงิน", min_value=0.0, step=1.0)
        if st.form_submit_button("บันทึก", type="primary", use_container_width=True):
            if not n or a <= 0:
                st.error("กรอกข้อมูลให้ครบ")
            else:
                supabase.table("entries").insert({
                    "user_id": user.id,
                    "date": d.isoformat(),
                    "title": n,
                    "type": t,
                    "amount": a
                }).execute()
                st.rerun()

elif menu == "ดูรายการทั้งหมด":
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(df[["date", "title", "type", "amount"]], use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูล")

elif menu == "ค้นหา":
    kw = st.text_input("ค้นหา")
    if kw:
        res = supabase.table("entries").select("*").eq("user_id", user.id).execute()
        df = pd.DataFrame(res.data)
        mask = df["title"].str.contains(kw, case=False, na=False) | df["type"].str.contains(kw, case=False, na=False)
        df = df[mask]
        st.dataframe(df[["date", "title", "type", "amount"]], use_container_width=True)

elif menu == "ส่งออกข้อมูล":
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    df = pd.DataFrame(res.data)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("ดาวน์โหลด", data=csv, file_name="data.csv")

elif menu == "แก้ไขและลบรายการ":
    res = supabase.table("entries").select("*").eq("user_id", user.id).order("date", desc=True).execute()
    if not res.data:
        st.info("ไม่มีรายการ")
        st.stop()
    df = pd.DataFrame(res.data)
    sel = st.selectbox("เลือกรายการ", ["-- เลือก --"] + list(df["title"]))
    if sel != "-- เลือก --":
        row = df[df["title"] == sel].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("แก้ไข")
            with st.form("edit"):
                ed = st.date_input("วันที่", value=pd.to_datetime(row["date"]))
                et = st.radio("ประเภท", ["รายรับ", "รายจ่าย"],
                    index=0 if row["type"] == "รายรับ" else 1, horizontal=True)
                en = st.text_input("ชื่อรายการ", value=row["title"])
                ea = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]))
                if st.form_submit_button("บันทึก", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": ed.isoformat(),
                        "type": et,
                        "title": en,
                        "amount": ea
                    }).eq("id", row["id"]).execute()
                    st.rerun()
        with col2:
            st.subheader("ลบ")
            if "del_id" not in st.session_state or st.session_state.del_id != row["id"]:
                if st.button("ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_id = row["id"]
                    st.warning("กดอีกครั้งเพื่อยืนยัน")
            else:
                if st.button("ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    del st.session_state.del_id
                    st.rerun()

elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    st.info(f"อีเมล: {user.email}")
n_state.del_conf = row["id"]
                    st.warning("กดอีกครั้งเพื่อยืนยันลบ ข้อมูลจะกู้คืนไม่ได้")
            else:
                if st.button("ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    st.session_state.show_success = "ลบรายการสำเร็จ"
                    del st.session_state.del_conf
                    st.rerun()

# ==================================================
# 6 จัดการบัญชี
# ==================================================
elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    st.info(f"อีเมล: {user.email}  \nรหัสผู้ใช้: {user.id}")

    st.divider()
    st.subheader("ล้างข้อมูลทั้งหมด")

    if "clear_all_conf" not in st.session_state or not st.session_state.clear_all_conf:
        if st.button("ลบข้อมูลทั้งหมดของฉัน", type="secondary", use_container_width=True):
            st.session_state.clear_all_conf = True
            st.warning("กดอีกครั้งเพื่อยืนยัน ข้อมูลทั้งหมดจะหายไป")
    else:
        if st.button("ยืนยันลบทั้งหมด", type="primary", use_container_width=True):
            supabase.table("entries").delete().eq("user_id", user.id).execute()
            st.session_state.show_success = "ล้างข้อมูลทั้งหมดเรียบร้อย"
            st.session_state.clear_all_conf = False
            st.rerun()
pe = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], 
                                     index=0 if row["type"] == "รายรับ" else 1, horizontal=True)
                edit_title = st.text_input("ชื่อรายการ", value=row["title"])
                edit_amount = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]))
                
                if st.form_submit_button("บันทึกการแก้ไข", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": edit_date.isoformat(),
                        "type": edit_type,
                        "title": edit_title,
                        "amount": edit_amount
                    }).eq("id", row["id"]).execute()
                    st.session_state.show_success = "แก้ไขข้อมูลเรียบร้อยแล้ว"
                    st.rerun()
        
        with col_del:
            st.subheader("ลบรายการ")
            if "del_conf" not in st.session_state or st.session_state.del_conf != row["id"]:
                if st.button("ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_conf = row["id"]
                    st.warning("กดอีกครั้งเพื่อยืนยันลบ ข้อมูลจะกู้คืนไม่ได้")
            else:
                if st.button("ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    st.session_state.show_success = "ลบรายการสำเร็จ"
                    del st.session_state.del_conf
                    st.rerun()

# ==================================================
# 6 จัดการบัญชี
# ==================================================
elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    st.info(f"อีเมล: {user.email}  \nรหัสผู้ใช้: {user.id}")
    
    st.divider()
    st.subheader("ล้างข้อมูลทั้งหมด")
    
    if "clear_all_conf" not in st.session_state or not st.session_state.clear_all_conf:
        if st.button("ลบข้อมูลทั้งหมดของฉัน", type="secondary", use_container_width=True):
            st.session_state.clear_all_conf = True
            st.warning("กดอีกครั้งเพื่อยืนยัน ข้อมูลทั้งหมดจะหายไป")
    else:
        if st.button("ยืนยันลบทั้งหมด", type="primary", use_container_width=True):
            supabase.table("entries").delete().eq("user_id", user.id).execute()
            st.session_state.show_success = "ล้างข้อมูลทั้งหมดเรียบร้อย"
            st.session_state.clear_all_conf = False
            st.rerun()
pe = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], 
                                     index=0 if row["type"] == "รายรับ" else 1, horizontal=True)
                edit_title = st.text_input("ชื่อรายการ", value=row["title"])
                edit_amount = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]))
                
                if st.form_submit_button("บันทึกการแก้ไข", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": edit_date.isoformat(),
                        "type": edit_type,
                        "title": edit_title,
                        "amount": edit_amount
                    }).eq("id", row["id"]).execute()
                    st.session_state.show_success = "แก้ไขข้อมูลเรียบร้อยแล้ว"
                    st.rerun()
        
        with col_del:
            st.subheader("ลบรายการ")
            if "del_conf" not in st.session_state or st.session_state.del_conf != row["id"]:
                if st.button("ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_conf = row["id"]
                    st.warning("กดอีกครั้งเพื่อยืนยันลบ ข้อมูลจะกู้คืนไม่ได้")
            else:
                if st.button("ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    st.session_state.show_success = "ลบรายการสำเร็จ"
                    del st.session_state.del_conf
                    st.rerun()

# ==================================================
# 6 จัดการบัญชี
# ==================================================
elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    st.info(f"อีเมล: {user.email}  \nรหัสผู้ใช้: {user.id}")
    
    st.divider()
    st.subheader("ล้างข้อมูลทั้งหมด")
    
    if "clear_all_conf" not in st.session_state or not st.session_state.clear_all_conf:
        if st.button("ลบข้อมูลทั้งหมดของฉัน", type="secondary", use_container_width=True):
            st.session_state.clear_all_conf = True
            st.warning("กดอีกครั้งเพื่อยืนยัน ข้อมูลทั้งหมดจะหายไป")
    else:
        if st.button("ยืนยันลบทั้งหมด", type="primary", use_container_width=True):
            supabase.table("entries").delete().eq("user_id", user.id).execute()
            st.session_state.show_success = "ล้างข้อมูลทั้งหมดเรียบร้อย"
            st.session_state.clear_all_conf = False
            st.rerun()
pe = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], 
                                     index=0 if row["type"] == "รายรับ" else 1, horizontal=True)
                edit_title = st.text_input("ชื่อรายการ", value=row["title"])
                edit_amount = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]))
                
                if st.form_submit_button("บันทึกการแก้ไข", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": edit_date.isoformat(),
                        "type": edit_type,
                        "title": edit_title,
                        "amount": edit_amount
                    }).eq("id", row["id"]).execute()
                    st.session_state.show_success = "แก้ไขข้อมูลเรียบร้อยแล้ว"
                    st.rerun()
        
        with col_del:
            st.subheader("ลบรายการ")
            if "del_conf" not in st.session_state or st.session_state.del_conf != row["id"]:
                if st.button("ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_conf = row["id"]
                    st.warning("กดอีกครั้งเพื่อยืนยันลบ ข้อมูลจะกู้คืนไม่ได้")
            else:
                if st.button("ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    st.session_state.show_success = "ลบรายการสำเร็จ"
                    del st.session_state.del_conf
                    st.rerun()

# ==================================================
# 6 จัดการบัญชี
# ==================================================
elif menu == "จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    st.info(f"อีเมล: {user.email}  \nรหัสผู้ใช้: {user.id}")
    
    st.divider()
    st.subheader("ล้างข้อมูลทั้งหมด")
    
    if "clear_all_conf" not in st.session_state or not st.session_state.clear_all_conf:
        if st.button("ลบข้อมูลทั้งหมดของฉัน", type="secondary", use_container_width=True):
            st.session_state.clear_all_conf = True
            st.warning("กดอีกครั้งเพื่อยืนยัน ข้อมูลทั้งหมดจะหายไป")
    else:
        if st.button("ยืนยันลบทั้งหมด", type="primary", use_container_width=True):
            supabase.table("entries").delete().eq("user_id", user.id).execute()
            st.session_state.show_success = "ล้างข้อมูลทั้งหมดเรียบร้อย"
            st.session_state.clear_all_conf = False
            st.rerun()
.columns(2)
        
        with col_edit:
            st.subheader("แก้ไขข้อมูล")
            with st.form("edit_form"):
                edit_date = st.date_input("วันที่", value=pd.to_datetime(row["date"]))
                edit_type = st.radio("ประเภท", ["รายรับ", "รายจ่าย"], 
                                     index=0 if row["type"] == "รายรับ" else 1, horizontal=True)
                edit_title = st.text_input("ชื่อรายการ", value=row["title"])
                edit_amount = st.number_input("จำนวนเงิน", min_value=0.0, value=float(row["amount"]))
                
                if st.form_submit_button("บันทึกการแก้ไข", type="primary", use_container_width=True):
                    supabase.table("entries").update({
                        "date": edit_date.isoformat(),
                        "type": edit_type,
                        "title": edit_title,
                        "amount": edit_amount
                    }).eq("id", row["id"]).execute()
                    st.session_state.show_success = "แก้ไขข้อมูลเรียบร้อยแล้ว"
                    st.rerun()
        
        with col_del:
            st.subheader("ลบรายการ")
            if "del_conf" not in st.session_state or st.session_state.del_conf != row["id"]:
                if st.button("ลบรายการนี้", type="secondary", use_container_width=True):
                    st.session_state.del_conf = row["id"]
                    st.warning("กดอีกครั้งเพื่อยืนยันลบ ข้อมูลจะกู้คืนไม่ได้")
            else:
                if st.button("ยืนยันการลบ", type="primary", use_container_width=True):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    st.session_state.show_success = "ลบรายการสำเร็จ"
                    del st.session_state.del_conf
                    st.rerun()

# ==================================================
# 6 จัดการบัญชี
# ==================================================
elif menu == "⚙️ จัดการบัญชี":
    st.subheader("ข้อมูลบัญชี")
    
    st.info(f"""
    📧 อีเมล: {user.email}  
    🆔 รหัสผู้ใช้: `{user.id}`
    """)
    
    st.markdown("---")
    st.subheader("ล้างข้อมูลทั้งหมด")
    
    if st.button("ลบข้อมูลทั้งหมดของฉัน", type="secondary", use_container_width=True):
        if "clear_all_conf" not in st.session_state:
            st.session_state.clear_all_conf = True
            st.warning("กดอีกครั้งเพื่อยืนยัน ข้อมูลทั้งหมดจะหายไป")
        else:
            supabase.table("entries").delete().eq("user_id", user.id).execute()
            st.session_state.show_success = "ล้างข้อมูลทั้งหมดเรียบร้อย"
            del st.session_state.clear_all_conf
            st.rerun()
l_conf != row["id"]:
                if st.button("🗑️ ลบรายการนี้", type="secondary"):
                    st.session_state.del_conf = row["id"]
                    st.warning("⚠️ กดอีกครั้งเพื่อยืนยันลบ — กู้คืนไม่ได้!", icon="⚠️")
            else:
                if st.button("✅ ยืนยันลบ", type="primary"):
                    supabase.table("entries").delete().eq("id", row["id"]).execute()
                    st.session_state.show_success = "✅ ลบรายการสำเร็จ!"
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
            st.session_state.show_success = "✅ ล้างข้อมูลทั้งหมดเรียบร้อย"
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
้งเพื่อยืนยันลบ — กู้คืนไม่ได้!", icon="⚠️")
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

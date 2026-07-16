import streamlit as st
import pandas as pd
from datetime import datetime
from utils.config import inject_custom_css
from utils.helpers import require_auth, custom_banner
from utils.database import load_json, USERS_FILE, load_attendance, mark_attendance
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.footer import render_footer

# Page Setup
st.set_page_config(page_title="SmartCampusAI - Attendance Portal", page_icon="📅", layout="wide")

# Check Auth
require_auth(allowed_roles=["Admin", "Faculty", "Student"])

# Inject Styles
inject_custom_css()

# Navigation
render_sidebar("Attendance")
render_navbar("Attendance Records")

# Load DB records
users = load_json(USERS_FILE, [])
attendance = load_attendance()
role = st.session_state.role
user_id = st.session_state.user_id

# Faculty or Admin View
if role in ["Faculty", "Admin"]:
    custom_banner("Attendance Administration", "Mark student attendance logs and review campus compliance records.")
    
    students = [u for u in users if u["role"] == "Student"]
    
    if not students:
        st.info("No registered students found in the database. Add students to record attendance.")
    else:
        tab_mark, tab_log = st.tabs(["📝 Record Attendance", "📋 Attendance Records Board"])
        
        with tab_mark:
            st.markdown("### Record Today's Log")
            selected_date = st.date_input("Target Date", value=datetime.today())
            date_str = selected_date.strftime("%Y-%m-%d")
            
            # Form to register grades
            with st.form("mark_attendance_form", clear_on_submit=False):
                st.write(f"Marking attendance status for **{date_str}**:")
                
                # Check for existing logs for this date to pre-populate options
                existing_record = next((a for a in attendance if a["date"] == date_str), None)
                existing_records = existing_record.get("records", {}) if existing_record else {}
                
                records = {}
                
                # Render table for students
                st.markdown(
                    """
                    <table style='width:100%; border-collapse:collapse; margin-bottom:1rem;'>
                        <thead>
                            <tr style='background-color:#f3f4f6;'>
                                <th style='padding:8px; text-align:left;'>Student Name</th>
                                <th style='padding:8px; text-align:left;'>Email</th>
                                <th style='padding:8px; text-align:left;'>Status Options</th>
                            </tr>
                        </thead>
                        <tbody>
                    """,
                    unsafe_allow_html=True
                )
                
                for s in students:
                    saved_status = existing_records.get(s["id"], "Present")
                    default_idx = 0 if saved_status == "Present" else 1
                    
                    st.write(f"**{s['name']}** ({s['email']})")
                    status_select = st.radio(
                        "Status", 
                        ["Present", "Absent"], 
                        index=default_idx, 
                        key=f"att_radio_{s['id']}", 
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    records[s["id"]] = status_select
                    st.markdown("<hr style='margin:0.2rem 0;'>", unsafe_allow_html=True)
                
                submit_att = st.form_submit_button("Publish Attendance Log")
                
                if submit_att:
                    mark_attendance(date_str, st.session_state.name, records)
                    st.success(f"Attendance for {date_str} recorded successfully!")
                    st.rerun()
                    
        with tab_log:
            st.markdown("### Historical Audit Board")
            if not attendance:
                st.info("No attendance records have been marked yet.")
            else:
                # Let user choose a date to filter
                date_options = sorted(list(set(a["date"] for a in attendance)), reverse=True)
                view_date = st.selectbox("Select Date to View", date_options)
                
                selected_log = next((a for a in attendance if a["date"] == view_date), None)
                
                if selected_log:
                    st.write(f"Logged by: **{selected_log.get('marked_by', 'System')}**")
                    
                    recs = selected_log.get("records", {})
                    log_data = []
                    present_c = 0
                    absent_c = 0
                    
                    for s in students:
                        status = recs.get(s["id"], "Absent")
                        log_data.append({
                            "Student Name": s["name"],
                            "Username": f"@{s['username']}",
                            "Status": status
                        })
                        if status == "Present":
                            present_c += 1
                        else:
                            absent_c += 1
                            
                    df_log = pd.DataFrame(log_data)
                    
                    # Highlight cards
                    c_col1, c_col2, c_col3 = st.columns(3)
                    with c_col1:
                        st.metric("Present", str(present_c), delta_color="normal")
                    with c_col2:
                        st.metric("Absent", str(absent_c), delta_color="inverse")
                    with c_col3:
                        tot = present_c + absent_c
                        pct = (present_c / tot * 100) if tot > 0 else 0
                        st.metric("Compliance Rate", f"{round(pct,1)}%")
                        
                    st.dataframe(df_log, use_container_width=True, hide_index=True)
                else:
                    st.warning("Logs missing for the selected date.")

# Student View
else:
    custom_banner("Attendance Audit Card", "Review class attendance records and logs.")
    
    # Calculate attendance logs
    att_rows = []
    present_count = 0
    absent_count = 0
    for record in attendance:
        date_val = record["date"]
        recs = record.get("records", {})
        if user_id in recs:
            status = recs[user_id]
            att_rows.append({
                "Date": date_val,
                "Status": status,
                "Logged By": record.get("marked_by", "Instructor")
            })
            if status == "Present":
                present_count += 1
            else:
                absent_count += 1
                
    total_marked = present_count + absent_count
    attendance_rate = (present_count / total_marked) * 100 if total_marked > 0 else 100.0
    
    col_g1, col_g2 = st.columns([1, 2])
    
    with col_g1:
        st.markdown("### Cumulative Average")
        st.markdown(
            f"""
            <div class="gradient-card-purple" style="text-align: center;">
                <span style="font-size:0.8rem; text-transform:uppercase; color:white; font-weight:700;">Rate</span>
                <div style="font-size: 3rem; font-weight: 800; color: white; margin: 0.5rem 0;">{round(attendance_rate,1)}%</div>
                <p style="color:rgba(255,255,255,0.9); font-size:0.85rem; margin:0;">
                    Present: {present_count} / Total Class: {total_marked}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_g2:
        st.markdown("### Date-wise Logs")
        if att_rows:
            df_stud_att = pd.DataFrame(att_rows).sort_values("Date", ascending=False)
            
            # Render styled logs
            for idx, row in df_stud_att.iterrows():
                badge_style = "color:#10b981; font-weight:bold;" if row['Status'] == "Present" else "color:#ef4444; font-weight:bold;"
                st.markdown(
                    f"""
                    <div style="background-color:white; padding:0.8rem 1.2rem; border-radius:8px; border:1px solid #e5e7eb; margin-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <strong style="color:#1e3a8a;">{row['Date']}</strong><br>
                            <span style="font-size:0.75rem; color:#6b7280;">Marked by: {row['Logged By']}</span>
                        </div>
                        <span style="{badge_style}">{row['Status']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No attendance records have been registered for your profile yet.")

# Footer
render_footer()

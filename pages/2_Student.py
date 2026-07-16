import streamlit as st
import pandas as pd
from utils.config import inject_custom_css
from utils.helpers import require_auth, custom_banner
from utils.database import load_json, USERS_FILE, load_assignments, load_attendance
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.footer import render_footer

# Page Setup
st.set_page_config(page_title="SmartCampusAI - Student Portal", page_icon="🎓", layout="wide")

# Check Auth - Admin, Faculty, and Students can view this page
require_auth(allowed_roles=["Admin", "Faculty", "Student"])

# Inject Styles
inject_custom_css()

# Render Navigation
render_sidebar("Students")
render_navbar("Student Directory & Profiles")

# Load DB records
users = load_json(USERS_FILE, [])
assignments = load_assignments()
attendance = load_attendance()

role = st.session_state.role
user_id = st.session_state.user_id

# Student Role View
if role == "Student":
    custom_banner("My Academic Profile", "Track your attendance, assignments status, and check grades.")
    
    col_prof, col_stats = st.columns([1, 2])
    
    # 1. Profile details card
    with col_prof:
        st.markdown("### Profile Card")
        st.markdown(
            f"""
            <div class="gradient-card-blue" style="text-align: center;">
                <div style="width: 80px; height: 80px; border-radius: 50%; background-color: rgba(255,255,255,0.25); 
                            display: flex; align-items: center; justify-content: center; font-size: 2.2rem; font-weight: 700; color: white; margin: 0 auto 1rem auto;">
                    {st.session_state.name[0].upper()}
                </div>
                <h4 style="margin:0; color:white; font-size:1.3rem;">{st.session_state.name}</h4>
                <p style="margin:0.2rem 0 0.8rem 0; color:rgba(255,255,255,0.8); font-size:0.85rem;">@{st.session_state.username}</p>
                <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top:0.8rem; font-size:0.85rem; text-align:left;">
                    <strong>Email:</strong> {st.session_state.email}<br>
                    <strong>ID:</strong> <code style="color:white; font-size:0.75rem;">{st.session_state.user_id}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("### Quick Navigation")
        if st.button("🤖 AI Study Assistant", use_container_width=True):
            st.switch_page("pages/6_AI_Assistant.py")
        if st.button("👤 Edit Profile Details", use_container_width=True):
            st.switch_page("pages/7_Profile.py")
            
    # 2. Detailed statistics (attendance log, assignments)
    with col_stats:
        # Calculate individual attendance
        att_rows = []
        present_count = 0
        absent_count = 0
        for record in attendance:
            date_val = record["date"]
            recs = record.get("records", {})
            if user_id in recs:
                status = recs[user_id]
                att_rows.append({"Date": date_val, "Status": status, "Marked By": record.get("marked_by", "System")})
                if status == "Present":
                    present_count += 1
                else:
                    absent_count += 1
                    
        total_marked = present_count + absent_count
        attendance_rate = (present_count / total_marked) * 100 if total_marked > 0 else 100.0
        
        att_tab, ass_tab = st.tabs(["📅 Attendance Log", "📝 Assignments & Grades"])
        
        with att_tab:
            st.markdown(f"### Attendance Record: **{round(attendance_rate, 1)}%**")
            st.write(f"Days Present: **{present_count}** | Days Absent: **{absent_count}** | Total Classes Logged: **{total_marked}**")
            
            if att_rows:
                df_att = pd.DataFrame(att_rows).sort_values("Date", ascending=False)
                # Color code status
                def style_status(val):
                    color = "#e6fffa" if val == "Present" else "#fff5f5"
                    txt_color = "#319795" if val == "Present" else "#e53e3e"
                    return f'background-color: {color}; color: {txt_color}; font-weight: bold; border-radius: 4px; padding: 2px 6px;'
                
                # HTML table renderer for customized styling
                html_table = "<table style='width:100%; border-collapse:collapse;'><thead><tr style='background-color:#f3f4f6;'><th style='padding:8px; text-align:left;'>Date</th><th style='padding:8px; text-align:left;'>Status</th><th style='padding:8px; text-align:left;'>Marked By</th></tr></thead><tbody>"
                for idx, r in df_att.iterrows():
                    color = "color:#10b981; font-weight:600;" if r['Status'] == "Present" else "color:#ef4444; font-weight:600;"
                    html_table += f"<tr style='border-bottom:1px solid #e5e7eb;'><td style='padding:8px;'>{r['Date']}</td><td style='padding:8px; {color}'>{r['Status']}</td><td style='padding:8px;'>{r['Marked By']}</td></tr>"
                html_table += "</tbody></table>"
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.info("No attendance sessions have been logged yet for your profile.")
                
        with ass_tab:
            st.markdown("### Submission Records")
            sub_rows = []
            for a in assignments:
                submissions = a.get("submissions", [])
                sub_record = next((s for s in submissions if s["student_id"] == user_id), None)
                
                if sub_record:
                    sub_rows.append({
                        "Assignment": a["title"],
                        "Due Date": a["due_date"],
                        "Submitted At": sub_record["submitted_at"],
                        "Grade": sub_record.get("grade") if sub_record.get("grade") else "Pending Grade",
                        "Feedback": sub_record.get("feedback") if sub_record.get("feedback") else "No feedback yet."
                    })
                else:
                    sub_rows.append({
                        "Assignment": a["title"],
                        "Due Date": a["due_date"],
                        "Submitted At": "❌ Not Submitted",
                        "Grade": "N/A",
                        "Feedback": "N/A"
                    })
                    
            if sub_rows:
                df_sub = pd.DataFrame(sub_rows)
                for idx, r in df_sub.iterrows():
                    badge_style = "color:#ef4444; font-weight:bold;" if r['Submitted At'].startswith("❌") else "color:#10b981;"
                    grade_badge = f"<span style='background-color:#dcfce7; color:#15803d; padding:2px 8px; border-radius:4px; font-weight:bold;'>{r['Grade']}</span>" if r['Grade'] != "Pending Grade" and r['Grade'] != "N/A" else f"<span style='color:#6b7280;'>{r['Grade']}</span>"
                    
                    st.markdown(
                        f"""
                        <div class="dashboard-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h4 style="margin:0; color:#1e3a8a;">{r['Assignment']}</h4>
                                <span style="font-size:0.9rem; font-weight:600;">Grade: {grade_badge}</span>
                            </div>
                            <p style="margin:0.2rem 0; color:#6b7280; font-size:0.8rem;">Due Date: {r['Due Date']} | Status: <span style="{badge_style}">{r['Submitted At']}</span></p>
                            <p style="margin:0.4rem 0 0 0; color:#4b5563; font-size:0.85rem; border-top: 1px dashed #e5e7eb; padding-top:0.4rem;"><strong>Feedback:</strong> {r['Feedback']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("No assignments are currently posted on the system.")

# Faculty/Admin Student Roster View
else:
    custom_banner("Student Directory", "Roster listing of all registered student accounts on the platform.")
    
    students_list = [u for u in users if u["role"] == "Student"]
    
    if not students_list:
        st.info("There are no registered students in the system database.")
    else:
        st.markdown("### Search Students")
        search_query = st.text_input("🔍 Search Student by name or username", "").strip().lower()
        
        # Filter students
        filtered_students = [
            s for s in students_list
            if search_query in s["name"].lower() or search_query in s["username"].lower() or search_query in s["email"].lower()
        ]
        
        col_list, col_det = st.columns([1.2, 1.8])
        
        with col_list:
            st.markdown(f"### Student Accounts ({len(filtered_students)})")
            if filtered_students:
                sel_student_name = st.selectbox(
                    "Select Student Profile to Review",
                    options=[s["name"] for s in filtered_students]
                )
                sel_student = next((s for s in filtered_students if s["name"] == sel_student_name), None)
            else:
                st.warning("No students matched the query.")
                sel_student = None
                
        with col_det:
            if sel_student:
                st.markdown(f"### Detailed Roster Profile: **{sel_student['name']}**")
                
                # Fetch statistics
                present_count = 0
                absent_count = 0
                for record in attendance:
                    recs = record.get("records", {})
                    if sel_student["id"] in recs:
                        if recs[sel_student["id"]] == "Present":
                            present_count += 1
                        else:
                            absent_count += 1
                            
                total_marked = present_count + absent_count
                attendance_rate = (present_count / total_marked) * 100 if total_marked > 0 else 100.0
                
                # Renders styled card
                st.markdown(
                    f"""
                    <div class="dashboard-card" style="margin-bottom:1.5rem;">
                        <h4 style="margin:0 0 0.5rem 0; color:#1e3a8a;">Academic Summary</h4>
                        <div style="display:flex; justify-content:space-around; align-items:center; text-align:center;">
                            <div>
                                <span style="font-size:0.75rem; text-transform:uppercase; color:#6b7280; font-weight:600;">Attendance</span>
                                <div style="font-size:1.8rem; font-weight:800; color:#3b82f6;">{round(attendance_rate,1)}%</div>
                                <span style="font-size:0.8rem; color:#6b7280;">({present_count} Present / {total_marked} Classes)</span>
                            </div>
                            <div style="border-left:1px solid #e5e7eb; height:50px;"></div>
                            <div>
                                <span style="font-size:0.75rem; text-transform:uppercase; color:#6b7280; font-weight:600;">Contact Email</span>
                                <div style="font-size:1.1rem; font-weight:600; color:#4b5563; margin-top:0.4rem;">{sel_student['email']}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Render submissions
                st.markdown("#### Assignment Submissions & Grading")
                student_subs = []
                for a in assignments:
                    sub_record = next((s for s in a.get("submissions", []) if s["student_id"] == sel_student["id"]), None)
                    if sub_record:
                        student_subs.append({
                            "Assignment": a["title"],
                            "Status": "Submitted",
                            "Submitted At": sub_record["submitted_at"],
                            "Text": sub_record["submission_text"],
                            "Grade": sub_record.get("grade") if sub_record.get("grade") else "Un-graded"
                        })
                        
                if student_subs:
                    for s in student_subs:
                        grade_display = f"<span style='background-color:#dcfce7; color:#15803d; padding:2px 8px; border-radius:4px; font-weight:bold;'>{s['Grade']}</span>" if s['Grade'] != "Un-graded" else f"<span style='color:#ef4444; font-weight:600;'>{s['Grade']}</span>"
                        st.markdown(
                            f"""
                            <div style="background-color:white; border:1px solid #e5e7eb; border-radius:8px; padding:1rem; margin-bottom:0.8rem;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <strong style="color:#1e3a8a;">{s['Assignment']}</strong>
                                    <span>{grade_display}</span>
                                </div>
                                <div style="font-size:0.8rem; color:#6b7280; margin:0.2rem 0;">Submitted: {s['Submitted At']}</div>
                                <div style="font-size:0.85rem; color:#4b5563; background-color:#f9fafb; padding:0.5rem; border-radius:4px; border:1px solid #f3f4f6; margin-top:0.4rem;">
                                    <strong>Submission Content:</strong><br>{s['Text']}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.info("No submissions made by this student yet.")
            else:
                st.info("Select a student from the listing dropdown to display their profile details.")

# Footer
render_footer()

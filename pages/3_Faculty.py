import streamlit as st
import pandas as pd
from utils.config import inject_custom_css
from utils.helpers import require_auth, custom_banner
from utils.database import load_json, USERS_FILE, load_assignments, load_attendance
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.footer import render_footer

# Page Setup
st.set_page_config(page_title="SmartCampusAI - Faculty Hub", page_icon="👨‍🏫", layout="wide")

# Check Auth
require_auth(allowed_roles=["Admin", "Faculty", "Student"])

# Inject Styles
inject_custom_css()

# Navigation
render_sidebar("Faculty")
render_navbar("Faculty Workspace & Directory")

# Load DB records
users = load_json(USERS_FILE, [])
assignments = load_assignments()
attendance = load_attendance()

role = st.session_state.role
user_id = st.session_state.user_id

# Faculty Workspace View
if role == "Faculty":
    custom_banner("Faculty Cockpit & Analytics", "Monitor assignment grading lists, submission statistics, and access teaching shortcuts.")
    
    # Filter assignments created by this faculty member
    my_assignments = [a for a in assignments if a["created_by_id"] == user_id]
    
    # Calculate grading metrics
    total_submissions = 0
    graded_submissions = 0
    pending_grade_subs = []
    
    for a in my_assignments:
        subs = a.get("submissions", [])
        total_submissions += len(subs)
        for s in subs:
            if s.get("grade") is not None:
                graded_submissions += 1
            else:
                pending_grade_subs.append({
                    "assignment_id": a["id"],
                    "assignment_title": a["title"],
                    "student_id": s["student_id"],
                    "student_name": s["student_name"],
                    "submitted_at": s["submitted_at"],
                    "submission_text": s["submission_text"]
                })
                
    pending_grading = len(pending_grade_subs)
    
    col_fc1, col_fc2 = st.columns([2, 1])
    
    with col_fc1:
        st.markdown("### 📊 Performance Analytics")
        if not my_assignments:
            st.info("No assignments created yet. Post a new assignment to track submission performance analytics.")
        else:
            # Build submission dataset for displaying
            data = []
            for a in my_assignments:
                subs = a.get("submissions", [])
                total_class = len([u for u in users if u["role"] == "Student"])
                sub_count = len(subs)
                data.append({
                    "Assignment": a["title"],
                    "Submissions": sub_count,
                    "Not Submitted": max(0, total_class - sub_count),
                })
            df_analytics = pd.DataFrame(data)
            
            # Show interactive submission details
            st.dataframe(df_analytics, use_container_width=True, hide_index=True)
            
            # Grading Checklist
            st.markdown("### 📝 Grading Checklist")
            if pending_grade_subs:
                st.write(f"You have **{pending_grading}** submissions awaiting grade assignment:")
                
                # Dropdown choice to select submission to grade
                options_str = [f"{item['student_name']} - {item['assignment_title']}" for item in pending_grade_subs]
                selected_opt = st.selectbox("Select Submission to Grade", options_str)
                
                selected_idx = options_str.index(selected_opt)
                sub_to_grade = pending_grade_subs[selected_idx]
                
                # Render grading form
                with st.form("faculty_grading_form"):
                    st.info(f"Grading Submission from: **{sub_to_grade['student_name']}**")
                    st.markdown(
                        f"""
                        <div style="background-color:#f9fafb; padding:1rem; border-radius:8px; margin-bottom:1rem; border:1px solid #e5e7eb;">
                            <strong>Assignment:</strong> {sub_to_grade['assignment_title']}<br>
                            <strong>Submitted:</strong> {sub_to_grade['submitted_at']}<br><br>
                            <strong>Submission text:</strong><br>
                            <p style="color:#1f2937; margin:0.2rem 0 0 0;">{sub_to_grade['submission_text']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    g_score = st.selectbox("Select Grade", ["A+", "A", "B+", "B", "C+", "C", "D", "Fail"])
                    g_feedback = st.text_area("Feedback Comments (Optional)")
                    
                    submit_grade_btn = st.form_submit_button("Submit Grade")
                    
                    if submit_grade_btn:
                        # Import database grading utility
                        from utils.database import grade_submission
                        if grade_submission(sub_to_grade["assignment_id"], sub_to_grade["student_id"], g_score, g_feedback):
                            st.success(f"Graded successfully! {sub_to_grade['student_name']} received an {g_score}.")
                            st.rerun()
                        else:
                            st.error("Failed to save grade to database.")
            else:
                st.success("🎉 All submissions are graded!")
                
    with col_fc2:
        st.markdown("### ⚙️ Quick Actions")
        if st.button("➕ Post New Assignment", use_container_width=True):
            st.switch_page("pages/4_Assignments.py")
        if st.button("📅 Record Attendance Log", use_container_width=True):
            st.switch_page("pages/5_Attendance.py")
        if st.button("📢 Publish Announcement", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")
            
        st.markdown("### Course Enrollment")
        students = [u for u in users if u["role"] == "Student"]
        st.markdown(
            f"""
            <div class="dashboard-card" style="text-align: center;">
                <h4 style="margin: 0; color: #1e3a8a;">Total Active Class</h4>
                <div style="font-size: 3rem; font-weight: 800; color: #8b5cf6; margin: 0.5rem 0;">{len(students)}</div>
                <p style="color:#6b7280; font-size:0.85rem; margin:0;">Registered Campus Students</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# Faculty Directory View for Students / Admins
else:
    custom_banner("Faculty Directory", "Registered academic instructors and contact information.")
    
    faculty_list = [u for u in users if u["role"] == "Faculty"]
    
    if not faculty_list:
        st.info("No faculty profiles registered in the system database.")
    else:
        st.markdown("### Search Instructors")
        search_query = st.text_input("🔍 Search Faculty by name, username, or email", "").strip().lower()
        
        filtered_fac = [
            f for f in faculty_list
            if search_query in f["name"].lower() or search_query in f["username"].lower() or search_query in f["email"].lower()
        ]
        
        if not filtered_fac:
            st.warning("No instructors matched the search criteria.")
        else:
            # Display faculty member cards
            col_idx = 0
            cols = st.columns(3)
            for f in filtered_fac:
                with cols[col_idx % 3]:
                    st.markdown(
                        f"""
                        <div class="dashboard-card" style="height: 100%;">
                            <div style="display:flex; align-items:center; gap:12px; margin-bottom:0.8rem;">
                                <div style="width: 45px; height: 45px; border-radius:50%; background-color:#bfdbfe; color:#1e3a8a; display:flex; align-items:center; justify-content:center; font-weight:700;">
                                    {f['name'][0].upper()}
                                </div>
                                <div>
                                    <h4 style="margin:0; color:#1e3a8a;">{f['name']}</h4>
                                    <span style="font-size:0.75rem; color:#8b5cf6; font-weight:700; text-transform:uppercase;">Faculty Instructor</span>
                                </div>
                            </div>
                            <div style="font-size:0.85rem; color:#4b5563; border-top:1px solid #e5e7eb; padding-top:0.6rem;">
                                <strong>Username:</strong> @{f['username']}<br>
                                <strong>Contact:</strong> {f['email']}<br>
                                <strong>Roster ID:</strong> <code style="font-size:0.7rem;">{f['id']}</code>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                col_idx += 1
                
# Footer
render_footer()

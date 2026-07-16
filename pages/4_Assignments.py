import streamlit as st
import pandas as pd
from datetime import datetime
from utils.config import inject_custom_css
from utils.helpers import require_auth, custom_banner
from utils.database import load_json, USERS_FILE, load_assignments, add_assignment, delete_assignment, submit_assignment, grade_submission
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.footer import render_footer

# Page Setup
st.set_page_config(page_title="SmartCampusAI - Assignments Portal", page_icon="📝", layout="wide")

# Check Auth
require_auth(allowed_roles=["Admin", "Faculty", "Student"])

# Inject Styles
inject_custom_css()

# Navigation
render_sidebar("Assignments")
render_navbar("Assignments Dashboard")

# Load DB records
users = load_json(USERS_FILE, [])
assignments = load_assignments()
role = st.session_state.role
user_id = st.session_state.user_id

# Faculty or Admin View
if role in ["Faculty", "Admin"]:
    custom_banner("Assignment Administration", "Upload and distribute new coursework tasks, delete items, and grade student answers.")
    
    col_upload, col_manage = st.columns([1, 2])
    
    with col_upload:
        st.markdown("### ➕ Create Assignment")
        with st.form("create_assignment_form", clear_on_submit=True):
            a_title = st.text_input("Assignment Title", placeholder="e.g. Calculus Problem Set 1")
            a_class = st.selectbox("Target Class", ["Mathematics 101", "Computer Science 202", "Physics 301", "Global History", "Literature"])
            a_due = st.date_input("Due Date", min_value=datetime.today())
            a_desc = st.text_area("Task Description & Instructions")
            
            submit_create = st.form_submit_button("Distribute Assignment")
            
            if submit_create:
                if not a_title or not a_desc:
                    st.error("Please fill in the title and description.")
                else:
                    due_str = a_due.strftime("%Y-%m-%d")
                    add_assignment(a_title, a_desc, due_str, a_class, st.session_state.name, user_id)
                    st.success(f"Assignment '{a_title}' published successfully!")
                    st.rerun()
                    
    with col_manage:
        st.markdown("### 📋 Active Tasks")
        if not assignments:
            st.info("No coursework assignments have been distributed yet.")
        else:
            for a in assignments:
                # Filter if Faculty - only show assignments they created (Admins see all)
                if role == "Faculty" and a["created_by_id"] != user_id:
                    continue
                    
                subs_count = len(a.get("submissions", []))
                
                with st.container():
                    st.markdown(
                        f"""
                        <div class="dashboard-card" style="margin-bottom:1rem;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h4 style="margin:0; color:#1e3a8a;">{a['title']}</h4>
                                <span style="background-color:#eff6ff; color:#3b82f6; font-size:0.8rem; font-weight:700; padding:2px 8px; border-radius:4px;">
                                    {a['class_name']}
                                </span>
                            </div>
                            <p style="margin:0.2rem 0; color:#6b7280; font-size:0.8rem;">Due: {a['due_date']} | Created by: {a['created_by_name']}</p>
                            <p style="margin:0.5rem 0; color:#4b5563; font-size:0.9rem;">{a['description']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    col_b1, col_b2 = st.columns([1, 1])
                    with col_b1:
                        # Expand submissions details
                        with st.expander(f"Review Submissions ({subs_count})", expanded=False):
                            subs = a.get("submissions", [])
                            if not subs:
                                st.write("No students have submitted this assignment yet.")
                            else:
                                for s in subs:
                                    status_lbl = f"Grade: {s['grade']}" if s['grade'] else "⚠️ Un-graded"
                                    st.markdown(
                                        f"""
                                        <div style="background-color:#f9fafb; padding:0.6rem; border-radius:6px; border:1px solid #e5e7eb; margin-bottom:0.5rem; font-size:0.85rem;">
                                            <strong>{s['student_name']}</strong> <span style="color:#8b5cf6; font-weight:bold; float:right;">{status_lbl}</span><br>
                                            <span style="font-size:0.75rem; color:#6b7280;">Submitted: {s['submitted_at']}</span><br>
                                            <p style="margin:0.4rem 0 0 0; color:#374151;">{s['submission_text']}</p>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    
                                    # Form to grade this individual submission
                                    if not s['grade']:
                                        with st.form(f"grade_sub_form_{a['id']}_{s['student_id']}", clear_on_submit=False):
                                            st.write(f"Assign grade to {s['student_name']}:")
                                            sc = st.selectbox("Grade", ["A+", "A", "B+", "B", "C+", "C", "D", "Fail"], key=f"sel_gr_{a['id']}_{s['student_id']}")
                                            fb = st.text_input("Feedback", placeholder="Good work!", key=f"txt_fb_{a['id']}_{s['student_id']}")
                                            sub_g = st.form_submit_button("Grade Student")
                                            if sub_g:
                                                grade_submission(a["id"], s["student_id"], sc, fb)
                                                st.success("Grade recorded!")
                                                st.rerun()
                    with col_b2:
                        st.markdown("<div class='destructive-btn'>", unsafe_allow_html=True)
                        if st.button("Delete Assignment Profile", key=f"del_ass_{a['id']}", use_container_width=True):
                            delete_assignment(a["id"])
                            st.success("Assignment deleted.")
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

# Student View
else:
    custom_banner("My Assignments Workspace", "Submit assignments for courses and review grades.")
    
    tab_p, tab_c = st.tabs(["⚠️ Pending Assignments", "✅ Graded & Completed"])
    
    with tab_p:
        pending_list = []
        for a in assignments:
            submissions = a.get("submissions", [])
            submitted = any(sub["student_id"] == user_id for sub in submissions)
            if not submitted:
                pending_list.append(a)
                
        if not pending_list:
            st.success("🎉 You have completed all assignments!")
        else:
            # Let student choose an assignment to work on
            select_ass_title = st.selectbox("Choose assignment to submit:", [pa["title"] for pa in pending_list])
            selected_ass = next((pa for pa in pending_list if pa["title"] == select_ass_title), None)
            
            if selected_ass:
                st.markdown(
                    f"""
                    <div class="dashboard-card" style="margin-bottom:1.5rem;">
                        <h4 style="margin:0; color:#1e3a8a;">{selected_ass['title']}</h4>
                        <p style="margin:0.2rem 0; color:#6b7280; font-size:0.8rem;">Class: {selected_ass['class_name']} | Due Date: {selected_ass['due_date']} | Created By: {selected_ass['created_by_name']}</p>
                        <p style="margin:0.5rem 0; color:#4b5563; font-size:0.95rem; border-top:1px dashed #e5e7eb; padding-top:0.5rem;">
                            <strong>Description:</strong><br>{selected_ass['description']}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                with st.form("submit_coursework_form", clear_on_submit=True):
                    sub_text = st.text_area("Your Submission Answer / Links", placeholder="Paste your submission details, essays, or links here...")
                    submit_btn = st.form_submit_button("Submit Work")
                    
                    if submit_btn:
                        if not sub_text.strip():
                            st.error("Cannot submit blank coursework.")
                        else:
                            submit_assignment(selected_ass["id"], user_id, st.session_state.name, sub_text)
                            st.success("Assignment submitted successfully!")
                            st.rerun()
                            
    with tab_c:
        completed_list = []
        for a in assignments:
            submissions = a.get("submissions", [])
            submitted = next((sub for sub in submissions if sub["student_id"] == user_id), None)
            if submitted:
                completed_list.append((a, submitted))
                
        if not completed_list:
            st.info("You haven't completed any assignments yet.")
        else:
            for a, sub in completed_list:
                status_color = "color:#10b981; font-weight:bold;" if sub.get("grade") else "color:#f59e0b; font-weight:bold;"
                grade_display = f"<span style='background-color:#dcfce7; color:#15803d; padding:2px 8px; border-radius:4px; font-weight:bold;'>{sub['grade']}</span>" if sub.get("grade") else "Awaiting Grade"
                
                st.markdown(
                    f"""
                    <div class="dashboard-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:#1e3a8a;">{a['title']}</h4>
                            <span style="font-size:0.9rem;">{grade_display}</span>
                        </div>
                        <p style="margin:0.2rem 0; color:#6b7280; font-size:0.8rem;">Submitted: {sub['submitted_at']} | Class: {a['class_name']}</p>
                        <p style="margin:0.4rem 0; font-size:0.9rem; color:#4b5563; background-color:#f9fafb; padding:0.5rem; border-radius:4px; border:1px solid #f3f4f6;">
                            <strong>Your Answer:</strong><br>{sub['submission_text']}
                        </p>
                        <p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#8b5cf6;"><strong>Teacher Feedback:</strong> {sub.get('feedback', 'No feedback yet.')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# Footer
render_footer()

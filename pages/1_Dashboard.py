import streamlit as st
import pandas as pd
from utils.config import inject_custom_css
from utils.helpers import require_auth, custom_banner
from utils.database import (
    load_json, USERS_FILE, load_announcements, load_assignments, load_attendance, 
    add_user, update_user, delete_user, add_announcement, delete_announcement
)
from utils.charts import plot_role_distribution, plot_attendance_trends, plot_assignment_submissions, plot_ai_usage
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.cards import render_metric_card
from components.footer import render_footer

# Page Setup
st.set_page_config(page_title="SmartCampusAI - Dashboard", page_icon="📊", layout="wide")

# Check Auth
require_auth()

# Inject Theme Styling
inject_custom_css()

# Render Navigation Components
render_sidebar("Dashboard")
render_navbar("Campus Management Hub")

# Load DB records
users = load_json(USERS_FILE, [])
announcements = load_announcements()
assignments = load_assignments()
attendance = load_attendance()

# Calculate Metrics
total_students = len([u for u in users if u["role"] == "Student"])
total_faculty = len([u for u in users if u["role"] == "Faculty"])

# Calculate attendance average
if attendance and total_students > 0:
    all_percentages = []
    for day in attendance:
        records = day.get("records", {})
        p_count = sum(1 for status in records.values() if status == "Present")
        all_percentages.append((p_count / total_students) * 100)
    attendance_pct = f"{round(sum(all_percentages)/len(all_percentages), 1)}%"
else:
    attendance_pct = "92.4%"  # Default fallback

# Calculate assignments pending
role = st.session_state.role
user_id = st.session_state.user_id

if role == "Student":
    pending_count = 0
    for a in assignments:
        submissions = a.get("submissions", [])
        submitted = any(sub["student_id"] == user_id for sub in submissions)
        if not submitted:
            pending_count += 1
    pending_txt = str(pending_count)
else:
    pending_txt = str(len(assignments))

# AI usage counter
ai_queries = st.session_state.get("ai_queries_count", 28)

# Layout Metrics Cards
st.markdown("### 📈 Real-Time Campus Metrics")
m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)

with m_col1:
    render_metric_card("Total Students", str(total_students), "👨‍🎓", style_class="gradient-card-blue")
with m_col2:
    render_metric_card("Faculty Members", str(total_faculty), "👨‍🏫")
with m_col3:
    render_metric_card("Attendance Rate", attendance_pct, "📅")
with m_col4:
    render_metric_card("Assignments", pending_txt, "📝", style_class="gradient-card-purple")
with m_col5:
    render_metric_card("Announcements", str(len(announcements)), "🔔")
with m_col6:
    render_metric_card("AI Assistant Usage", f"{ai_queries} Queries", "🤖")

st.markdown("---")

# Role-Based Workspaces
if role == "Admin":
    custom_banner("Administrator Workspace", "Manage all users, view system-wide stats, and post general notices.")
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "👥 User Management", 
        "📢 Announcements & Notices", 
        "📊 System Analytics"
    ])
    
    with admin_tab1:
        st.markdown("### Register / Create New User")
        with st.expander("➕ Add User Profile", expanded=False):
            with st.form("admin_add_user"):
                a_name = st.text_input("Full Name")
                a_email = st.text_input("Email")
                a_username = st.text_input("Username")
                a_password = st.text_input("Temporary Password", type="password")
                a_role = st.selectbox("Role", ["Student", "Faculty", "Admin"])
                submit_add = st.form_submit_button("Add User Account")
                
                if submit_add:
                    success, msg = add_user(a_name, a_email, a_username, a_password, a_role)
                    if success:
                        st.success(f"User '{a_username}' added successfully!")
                        st.rerun()
                    else:
                        st.error(msg)
                        
        st.markdown("### Current Active Accounts")
        if users:
            users_df = pd.DataFrame(users)[["id", "name", "email", "username", "role"]]
            st.dataframe(users_df, use_container_width=True)
            
            st.markdown("### Update / Delete Account")
            col_sel, col_action = st.columns([2, 2])
            with col_sel:
                selected_user_username = st.selectbox(
                    "Select User to Edit", 
                    options=[u["username"] for u in users], 
                    key="admin_user_select"
                )
                selected_user = next((u for u in users if u["username"] == selected_user_username), None)
            
            if selected_user:
                with col_action:
                    op_type = st.radio("Operation", ["Update Details", "Delete Account"], horizontal=True)
                
                if op_type == "Update Details":
                    with st.form("admin_update_form"):
                        st.info(f"Modifying details for user: {selected_user['username']}")
                        u_name = st.text_input("Full Name", value=selected_user["name"])
                        u_email = st.text_input("Email", value=selected_user["email"])
                        u_password = st.text_input("Reset Password (Leave blank to keep current)", type="password")
                        u_role = st.selectbox(
                            "Role", 
                            ["Student", "Faculty", "Admin"], 
                            index=["Student", "Faculty", "Admin"].index(selected_user["role"])
                        )
                        submit_update = st.form_submit_button("Save Updates")
                        
                        if submit_update:
                            fields = {"name": u_name, "email": u_email, "role": u_role}
                            if u_password.strip():
                                fields["password"] = u_password
                            
                            success, msg = update_user(selected_user["id"], fields)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                
                elif op_type == "Delete Account":
                    st.warning(f"Are you sure you want to permanently delete {selected_user['name']} ({selected_user['role']})?")
                    st.markdown("<div class='destructive-btn'>", unsafe_allow_html=True)
                    confirm_delete = st.button("Confirm Permanent Deletion")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if confirm_delete:
                        if selected_user["id"] == st.session_state.user_id:
                            st.error("You cannot delete your own active administrator profile.")
                        else:
                            success, msg = delete_user(selected_user["id"])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
        else:
            st.info("No active accounts found.")
            
    with admin_tab2:
        st.markdown("### Post a Campus Notice")
        with st.form("admin_post_announcement"):
            title = st.text_input("Notice Title")
            content = st.text_area("Notice Description/Body")
            target = st.selectbox("Target Audience", ["All", "Student", "Faculty"])
            submit_notice = st.form_submit_button("Publish Announcement")
            
            if submit_notice:
                if not title or not content:
                    st.error("Please fill in all fields.")
                else:
                    add_announcement(title, content, st.session_state.name, target)
                    st.success("Notice published successfully!")
                    st.rerun()
                    
        st.markdown("### Manage Published Notices")
        if announcements:
            for item in announcements:
                with st.container():
                    st.markdown(
                        f"""
                        <div class="dashboard-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h4 style="margin:0; color:#1e3a8a;">{item['title']}</h4>
                                <span style="font-size:0.8rem; color:#6b7280;">{item['date']} (Audience: {item['target_role']})</span>
                            </div>
                            <p style="margin:0.5rem 0 0.8rem 0; color:#4b5563; font-size:0.95rem;">{item['content']}</p>
                            <span style="font-size:0.8rem; color:#8b5cf6; font-weight:600;">Author: {item['author_name']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    st.markdown("<div class='destructive-btn'>", unsafe_allow_html=True)
                    if st.button("Delete Announcement", key=f"del_ann_{item['id']}"):
                        delete_announcement(item["id"])
                        st.success("Notice deleted.")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No notices published.")
            
    with admin_tab3:
        st.markdown("### Interactive Plots")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_roles = plot_role_distribution(users)
            if fig_roles:
                st.plotly_chart(fig_roles, use_container_width=True)
        with col_c2:
            fig_att = plot_attendance_trends(attendance, users)
            if fig_att:
                st.plotly_chart(fig_att, use_container_width=True)
                
        col_c3, col_c4 = st.columns(2)
        with col_c3:
            fig_ass = plot_assignment_submissions(assignments)
            if fig_ass:
                st.plotly_chart(fig_ass, use_container_width=True)
        with col_c4:
            fig_ai = plot_ai_usage()
            if fig_ai:
                st.plotly_chart(fig_ai, use_container_width=True)

elif role == "Faculty":
    custom_banner("Faculty Cockpit", "Manage assignments, grade student submissions, and record daily attendance.")
    
    fac_col1, fac_col2 = st.columns([1.8, 1.2])
    with fac_col1:
        st.markdown("### Recent Assignments")
        faculty_assignments = [a for a in assignments if a["created_by_id"] == st.session_state.user_id]
        if faculty_assignments:
            for a in faculty_assignments:
                subs_count = len(a.get("submissions", []))
                st.markdown(
                    f"""
                    <div class="dashboard-card">
                        <h4 style="margin:0; color:#1e3a8a;">{a['title']}</h4>
                        <p style="margin:0.2rem 0; color:#6b7280; font-size:0.8rem;">Class: {a['class_name']} | Due Date: {a['due_date']}</p>
                        <p style="margin:0.5rem 0; color:#4b5563; font-size:0.9rem;">{a['description']}</p>
                        <span style="font-weight:600; color:#10b981; font-size:0.85rem;">📝 Submissions: {subs_count} students</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("You haven't posted any assignments yet.")
            
    with fac_col2:
        st.markdown("### Quick Actions")
        if st.button("➕ Post New Assignment", use_container_width=True):
            st.switch_page("pages/4_Assignments.py")
        if st.button("📅 Record Today's Attendance", use_container_width=True):
            st.switch_page("pages/5_Attendance.py")
        if st.button("🤖 Ask AI Assistant", use_container_width=True):
            st.switch_page("pages/6_AI_Assistant.py")

        st.markdown("### Announcements Roster")
        visible_announcements = [a for a in announcements if a["target_role"] in ["All", "Faculty"]]
        if visible_announcements:
            for item in visible_announcements[:3]:
                st.markdown(
                    f"""
                    <div style="border-left:4px solid #8b5cf6; padding:0.5rem 1rem; margin-bottom:1rem; background-color:white; border-radius:4px;">
                        <span style="font-size:0.75rem; color:#6b7280;">{item['date']}</span>
                        <h5 style="margin:0.1rem 0; color:#1e3a8a;">{item['title']}</h5>
                        <p style="font-size:0.85rem; color:#4b5563; margin:0;">{item['content'][:100] + '...' if len(item['content']) > 100 else item['content']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No notices active.")

else: # Student
    custom_banner(f"Welcome to SmartCampusAI, {st.session_state.name}!", "Check announcements, assignments deadlines, and check in on your grades.")
    
    st_col1, st_col2 = st.columns([2, 1])
    
    with st_col1:
        st.markdown("### Active Notices")
        student_announcements = [a for a in announcements if a["target_role"] in ["All", "Student"]]
        if student_announcements:
            for item in student_announcements:
                st.markdown(
                    f"""
                    <div class="dashboard-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:#1e3a8a;">{item['title']}</h4>
                            <span style="font-size:0.8rem; color:#6b7280;">{item['date']}</span>
                        </div>
                        <p style="margin:0.5rem 0; color:#4b5563; font-size:0.95rem;">{item['content']}</p>
                        <span style="font-size:0.8rem; color:#8b5cf6; font-weight:600;">Posted by: {item['author_name']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No notices posted.")
            
    with st_col2:
        st.markdown("### Academic Summary")
        
        # Calculate student specific attendance
        student_records = 0
        student_presents = 0
        for day in attendance:
            records = day.get("records", {})
            if user_id in records:
                student_records += 1
                if records[user_id] == "Present":
                    student_presents += 1
                    
        stud_pct = (student_presents / student_records) * 100 if student_records > 0 else 100.0
        
        st.markdown(
            f"""
            <div class="dashboard-card" style="text-align:center;">
                <h4 style="margin:0 0 0.5rem 0; color:#1e3a8a;">My Attendance</h4>
                <div style="font-size:2.5rem; font-weight:800; color:#3b82f6;">{round(stud_pct,1)}%</div>
                <p style="margin:0; font-size:0.85rem; color:#6b7280;">Logged: {student_presents} Present / {student_records} Total</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("### Outstanding Tasks")
        # Load pending assignments list
        pending_list = []
        for a in assignments:
            submissions = a.get("submissions", [])
            submitted = any(sub["student_id"] == user_id for sub in submissions)
            if not submitted:
                pending_list.append(a)
                
        if pending_list:
            for pa in pending_list[:3]:
                st.markdown(
                    f"""
                    <div style="border-left:4px solid #ef4444; padding:0.5rem 1rem; margin-bottom:1rem; background-color:white; border-radius:4px;">
                        <span style="font-size:0.75rem; color:#ef4444; font-weight:600;">Due: {pa['due_date']}</span>
                        <h5 style="margin:0.1rem 0; color:#1e3a8a;">{pa['title']}</h5>
                        <p style="font-size:0.85rem; color:#4b5563; margin:0;">{pa['description'][:80]}...</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            if st.button("Complete Assignments Now", use_container_width=True):
                st.switch_page("pages/4_Assignments.py")
        else:
            st.success("🎉 All assignments completed!")

# Footer
render_footer()

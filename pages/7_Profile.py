import streamlit as st
from utils.config import inject_custom_css
from utils.helpers import require_auth, custom_banner
from utils.database import update_user, load_json, USERS_FILE
from utils.auth import validate_email
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.footer import render_footer

# Page Setup
st.set_page_config(page_title="SmartCampusAI - User Profile", page_icon="👤", layout="wide")

# Check Auth
require_auth()

# Inject Styles
inject_custom_css()

# Navigation
render_sidebar("Profile")
render_navbar("User Account Settings")

custom_banner("My Account Profile", "View and update your student/staff credentials and security settings.")

role = st.session_state.role
user_id = st.session_state.user_id

col_left, col_right = st.columns([1.2, 1.8])

with col_left:
    st.markdown("### Profile Summary")
    # Fetch latest user details from DB directly (in case updated)
    users = load_json(USERS_FILE, [])
    current_db_user = next((u for u in users if u["id"] == user_id), None)
    
    if not current_db_user:
        st.error("Error loading account profile from database.")
    else:
        st.markdown(
            f"""
            <div class="gradient-card-purple" style="text-align: center;">
                <div style="width: 80px; height: 80px; border-radius: 50%; background-color: rgba(255,255,255,0.25); 
                            display: flex; align-items: center; justify-content: center; font-size: 2.2rem; font-weight: 700; color: white; margin: 0 auto 1rem auto; font-family: 'Inter', sans-serif;">
                    {current_db_user['name'][0].upper()}
                </div>
                <h4 style="margin:0; color:white; font-size:1.3rem; font-family: 'Inter', sans-serif;">{current_db_user['name']}</h4>
                <p style="margin:0.2rem 0 0.8rem 0; color:rgba(255,255,255,0.85); font-size:0.85rem; font-family: 'Inter', sans-serif;">@{current_db_user['username']}</p>
                <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top:0.8rem; font-size:0.85rem; text-align:left; font-family: 'Inter', sans-serif;">
                    <strong>Academic Role:</strong> {current_db_user['role']}<br>
                    <strong>Email:</strong> {current_db_user['email']}<br>
                    <strong>Account ID:</strong> <code style="color:white; font-size:0.75rem;">{current_db_user['id']}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

with col_right:
    st.markdown("### Update Profile Details")
    if current_db_user:
        with st.form("update_profile_form", clear_on_submit=False):
            new_name = st.text_input("Full Name", value=current_db_user["name"])
            new_email = st.text_input("Email Address", value=current_db_user["email"])
            
            st.markdown("---")
            st.write("🔑 **Change Password** (Leave blank to keep current password)")
            new_pass = st.text_input("New Password", type="password", placeholder="At least 6 characters")
            confirm_pass = st.text_input("Confirm New Password", type="password", placeholder="Re-type password")
            
            submit_update = st.form_submit_button("Save Profile Changes")
            
            if submit_update:
                if not new_name.strip() or not new_email.strip():
                    st.error("Full Name and Email fields cannot be blank.")
                elif not validate_email(new_email):
                    st.error("Please enter a valid email address.")
                else:
                    fields_to_update = {
                        "name": new_name.strip(),
                        "email": new_email.strip()
                    }
                    
                    # Validate password change if provided
                    pw_valid = True
                    if new_pass:
                        if len(new_pass) < 6:
                            st.error("New password must be at least 6 characters long.")
                            pw_valid = False
                        elif new_pass != confirm_pass:
                            st.error("Passwords do not match.")
                            pw_valid = False
                        else:
                            fields_to_update["password"] = new_pass
                            
                    if pw_valid:
                        success, message = update_user(user_id, fields_to_update)
                        if success:
                            st.success("Profile details updated successfully!")
                            
                            # Sync local session variables
                            st.session_state.name = new_name
                            st.session_state.email = new_email
                            
                            st.rerun()
                        else:
                            st.error(message)

# Footer
render_footer()

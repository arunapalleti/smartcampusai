import streamlit as st
from streamlit_option_menu import option_menu
from utils.auth import logout_session

def render_sidebar(current_page_label: str):
    """
    Renders a unified custom navigation menu in the sidebar.
    Hides standard pages and implements custom routing.
    """
    role = st.session_state.get("role", "Student")
    name = st.session_state.get("name", "User")
    
    # Base options
    # Role-based menu customization
    if role == "Student":
        options = ["Dashboard", "Students", "Assignments", "Attendance", "AI Assistant", "Profile", "Logout"]
        icons = ["house", "mortarboard", "journal-text", "calendar-check", "robot", "person", "box-arrow-right"]
    elif role == "Faculty":
        options = ["Dashboard", "Students", "Faculty", "Assignments", "Attendance", "AI Assistant", "Profile", "Logout"]
        icons = ["house", "mortarboard", "person-badge", "journal-text", "calendar-check", "robot", "person", "box-arrow-right"]
    else:  # Admin
        options = ["Dashboard", "Students", "Faculty", "Assignments", "Attendance", "AI Assistant", "Profile", "Logout"]
        icons = ["house", "mortarboard", "person-badge", "journal-text", "calendar-check", "robot", "person", "box-arrow-right"]
        
    # File mapping for st.switch_page
    mapping = {
        "Dashboard": "pages/1_Dashboard.py",
        "Students": "pages/2_Student.py",
        "Faculty": "pages/3_Faculty.py",
        "Assignments": "pages/4_Assignments.py",
        "Attendance": "pages/5_Attendance.py",
        "AI Assistant": "pages/6_AI_Assistant.py",
        "Profile": "pages/7_Profile.py"
    }

    # Ensure the default index matches current page
    try:
        default_index = options.index(current_page_label)
    except ValueError:
        default_index = 0

    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 1rem 0; text-align: center;">
                <h2 style="color: white; font-size: 1.4rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    SmartCampusAI
                </h2>
                <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.2rem; font-weight: 500;">Role: {role}</p>
            </div>
            <hr style="border-top: 1px solid rgba(255,255,255,0.15); margin: 0 0 1rem 0;">
            """,
            unsafe_allow_html=True
        )

        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            menu_icon="cast",
            default_index=default_index,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#a78bfa", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin": "2px 0px", 
                    "color": "#cbd5e1",
                    "font-family": "Inter, sans-serif",
                    "font-weight": "500",
                    "transition": "all 0.15s ease"
                },
                "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600"},
            }
        )

        # Handle page routing
        if selected == "Logout":
            logout_session()
        elif selected in mapping and selected != current_page_label:
            st.switch_page(mapping[selected])

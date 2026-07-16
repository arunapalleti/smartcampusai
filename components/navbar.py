import streamlit as st

def render_navbar(title="SmartCampusAI"):
    """
    Renders a unified top navbar with branding, user info, role badges, and visual avatar.
    """
    name = st.session_state.get("name", "Guest")
    role = st.session_state.get("role", "Visitor")
    
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    background-color: white; padding: 0.8rem 1.5rem; border-radius: 12px; 
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 1.5rem;
                    border: 1px solid #e5e7eb;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                             -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: 'Inter', sans-serif;">
                    SmartCampusAI
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="text-align: right; font-family: 'Inter', sans-serif;">
                    <div style="font-weight: 600; color: #1f2937; font-size: 0.95rem;">{name}</div>
                    <div style="font-size: 0.75rem; color: #8b5cf6; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">{role}</div>
                </div>
                <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); 
                            display: flex; align-items: center; justify-content: center; font-weight: 700; color: white; font-family: 'Inter', sans-serif;">
                    {name[0].upper() if name else 'G'}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

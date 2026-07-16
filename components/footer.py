import streamlit as st

def render_footer():
    """
    Renders a premium system footer.
    """
    st.markdown(
        """
        <hr style="border-top: 1px solid #e5e7eb; margin-top: 3rem; margin-bottom: 1.5rem;">
        <div style="text-align: center; color: #6b7280; font-size: 0.85rem; font-family: 'Inter', sans-serif; padding-bottom: 1.5rem;">
            <p style="margin: 0;">SmartCampusAI © 2026 • Powered by Streamlit, Gemini & OpenAI</p>
            <p style="margin: 0.2rem 0 0 0; font-size: 0.75rem; color: #9ca3af;">Designed for Administrative Excellence and AI Integration</p>
        </div>
        """,
        unsafe_allow_html=True
    )

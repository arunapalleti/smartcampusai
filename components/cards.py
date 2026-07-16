import streamlit as st

def render_metric_card(title: str, value: str, icon: str = "", delta: str = None, style_class: str = "dashboard-card"):
    """
    Renders a customized CSS metric card.
    style_class options:
    - 'dashboard-card' (White styled card with custom hover animations)
    - 'gradient-card-blue' (Blue gradient card)
    - 'gradient-card-purple' (Purple gradient card)
    """
    delta_html = ""
    if delta:
        if delta.startswith("-") or "down" in delta.lower():
            color = "#ef4444"
        else:
            color = "#10b981"
        delta_html = f'<div style="font-size: 0.85rem; color: {color}; margin-top: 0.5rem; font-weight: 600; font-family: \'Inter\', sans-serif;">{delta}</div>'
    
    # Text color adjust for gradient cards
    text_style = "color: white !important;" if "gradient" in style_class else "color: #4b5563;"
    val_style = "color: white !important;" if "gradient" in style_class else "color: #111827;"
    
    st.markdown(
        f"""
        <div class="{style_class}" style="font-family: 'Inter', sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; opacity: 0.85; {text_style}">
                        {title}
                    </div>
                    <div style="font-size: 2rem; font-weight: 800; margin-top: 0.4rem; line-height: 1; {val_style}">
                        {value}
                    </div>
                    {delta_html}
                </div>
                <div style="font-size: 1.8rem; opacity: 0.9;">
                    {icon}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

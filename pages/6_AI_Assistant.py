import streamlit as st
import os
from utils.config import inject_custom_css, GOOGLE_API_KEY, OPENAI_API_KEY
from utils.helpers import require_auth, custom_banner
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.footer import render_footer

# Page Setup
st.set_page_config(page_title="SmartCampusAI - Chatbot", page_icon="🤖", layout="wide")

# Check Auth
require_auth()

# Inject Styles
inject_custom_css()

# Navigation
render_sidebar("AI Assistant")
render_navbar("AI Campus Assistant")

custom_banner("AI Study & Administration Assistant", "Ask questions about campus policies, coursework navigation, attendance compliance, or general guidelines.")

# System Prompt Context
SYSTEM_INSTRUCTION = """
You are the SmartCampusAI Assistant, an AI assistant dedicated to helping students, faculty, and administrators.
Your job is to answer questions related to campus life, scheduling, attendance policies, assignment submissions, user management, and general academics.
Keep your answers brief, professional, and friendly.
If the query is completely unrelated to academic or campus matters, politely refuse to answer and redirect the user to campus resources.
"""

# Track AI Queries count in session state for dashboard metrics
if "ai_queries_count" not in st.session_state:
    st.session_state.ai_queries_count = 28

# Choose AI Client
api_mode = "demo"
client = None

if GOOGLE_API_KEY:
    try:
        from google import genai
        # Initialize Google GenAI Client
        client = genai.Client(api_key=GOOGLE_API_KEY)
        api_mode = "gemini"
    except Exception as e:
        st.error(f"Failed to load Google GenAI SDK: {e}")

if api_mode == "demo" and OPENAI_API_KEY:
    try:
        from openai import OpenAI
        # Initialize OpenAI Client
        client = OpenAI(api_key=OPENAI_API_KEY)
        api_mode = "openai"
    except Exception as e:
        st.error(f"Failed to load OpenAI SDK: {e}")

# Alert user about mode
if api_mode == "demo":
    st.info("⚠️ **Demo Mode Active**: To connect live Gemini or OpenAI models, create a `.env` file at the root directory and add `GOOGLE_API_KEY` or `OPENAI_API_KEY` credentials.")
else:
    st.success(f"⚡ **Live Connection Active**: Chatbot is connected to **{api_mode.upper()}**.")

# Chat History Init
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hello {st.session_state.name}! I am your SmartCampusAI Assistant. How can I help you today?"}
    ]

# Render chat logs
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Chat Input
user_prompt = st.chat_input("Ask a campus question...")

if user_prompt:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)
        
    # Increment AI Usage Counter
    st.session_state.ai_queries_count += 1
    
    # Generate Response
    response_text = ""
    
    with st.chat_message("assistant"):
        with st.spinner("Generating answer..."):
            if api_mode == "gemini":
                try:
                    # New google-genai Client format
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"{SYSTEM_INSTRUCTION}\n\nUser Question: {user_prompt}"
                    )
                    response_text = response.text
                except Exception as e:
                    response_text = f"API Error: Failed to generate response from Gemini. Details: {e}"
            
            elif api_mode == "openai":
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": SYSTEM_INSTRUCTION},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    response_text = response.choices[0].message.content
                except Exception as e:
                    response_text = f"API Error: Failed to generate response from OpenAI. Details: {e}"
            
            else:
                # Demo Fallback Keyword Matcher
                prompt_lower = user_prompt.lower()
                if "attendance" in prompt_lower or "absent" in prompt_lower or "present" in prompt_lower:
                    response_text = (
                        "Attendance records are managed under the **Attendance** page. Students must maintain a minimum compliance "
                        "threshold of 75%. If you are absent, contact your faculty instructor to submit a leave certificate."
                    )
                elif "assignment" in prompt_lower or "grade" in prompt_lower or "homework" in prompt_lower or "submission" in prompt_lower:
                    response_text = (
                        "You can review, submit, and grade coursework in the **Assignments** dashboard. Students can paste "
                        "their submissions directly in the provided text field. Faculty can grade them from their dashboard cockpit."
                    )
                elif "notice" in prompt_lower or "announcement" in prompt_lower or "update" in prompt_lower:
                    response_text = (
                        "Announcements are visible on the **Dashboard** screen. Admins and Faculty can post general announcements "
                        "or announcements tailored to specific roles (e.g. Students or Faculty only)."
                    )
                elif "login" in prompt_lower or "register" in prompt_lower or "password" in prompt_lower or "user" in prompt_lower:
                    response_text = (
                        "User registration and verification is handled securely using bcrypt password hashing. Admins can add, "
                        "update details, or remove user profiles via the User Management tab on the Admin Dashboard."
                    )
                elif "faculty" in prompt_lower or "teacher" in prompt_lower or "instructor" in prompt_lower:
                    response_text = (
                        "You can locate faculty instructors, their email addresses, and account listings in the **Faculty** directory page."
                    )
                elif "student" in prompt_lower or "roster" in prompt_lower:
                    response_text = (
                        "Registered student directory boards can be searched under the **Students** panel page. Faculty can select specific student files to review their credentials."
                    )
                else:
                    response_text = (
                        "That is a great campus query! In Demo Mode, I match key terms like 'attendance', 'assignments', "
                        "'notices', 'faculty', and 'users'. To get a full conversational response from a live LLM, configure "
                        "your `GOOGLE_API_KEY` or `OPENAI_API_KEY` inside the `.env` file."
                    )
                    
            st.write(response_text)
            
    # Append assistant answer
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Footer
render_footer()

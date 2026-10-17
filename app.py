import streamlit as st
from dotenv import load_dotenv

from utils.auth import init_db, authenticate_user, register_user, generate_reset_token, reset_password
from utils.data_manager import initialize_session_state
from utils.ai_agent import initialize_agent
from components.chat_widget import render_chat_widget
from views.portfolio import render_portfolio
from views.watchlist import render_watchlist
from views.charts import render_charts
from views.admin import render_admin

load_dotenv()
st.set_page_config(page_title="AI Market Dashboard", page_icon="📈", layout="wide")

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# Track recovery flow state
if "recovery_stage" not in st.session_state:
    st.session_state.recovery_stage = "request"

if not st.session_state.logged_in:
    st.title("📈 AI Market Dashboard")
    st.markdown("Please log in or register an account to access your personalized market data.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔒 Login", "📝 Register", "🔑 Recover Password"])
        
        # ---------------------------------------------------------
        # LOGIN TAB
        # ---------------------------------------------------------
        with tab1:
            with st.form("login_form"):
                log_email = st.text_input("Email Address").lower()
                log_pass = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Login", use_container_width=True)
                
                if submit_login:
                    user = authenticate_user(log_email, log_pass)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                        
        # ---------------------------------------------------------
        # REGISTER TAB
        # ---------------------------------------------------------
        with tab2:
            with st.form("register_form"):
                reg_email = st.text_input("Email Address").lower()
                reg_pass = st.text_input("Password", type="password")
                reg_pass_conf = st.text_input("Confirm Password", type="password")
                submit_register = st.form_submit_button("Register Account", use_container_width=True)
                
                if submit_register:
                    if reg_pass != reg_pass_conf:
                        st.error("Passwords do not match.")
                    elif len(reg_pass) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        success = register_user(reg_email, reg_pass, False)
                        if success:
                            st.success("Account created successfully! You can now log in.")
                        else:
                            st.error("An account with that email already exists.")

        # ---------------------------------------------------------
        # RECOVER PASSWORD TAB
        # ---------------------------------------------------------
        with tab3:
            if st.session_state.recovery_stage == "request":
                with st.form("request_reset_form"):
                    st.markdown("Enter your email address to generate a recovery token.")
                    rec_email = st.text_input("Account Email").lower()
                    submit_request = st.form_submit_button("Generate Token", use_container_width=True)
                    
                    if submit_request:
                        token = generate_reset_token(rec_email)
                        if token:
                            # In production, you would email this token here.
                            # For local use, we print it to the terminal.
                            print(f"\n{'='*40}\nPASSWORD RESET TOKEN FOR {rec_email}:\n{token}\n{'='*40}\n")
                            
                            st.session_state.recovery_email = rec_email
                            st.session_state.recovery_stage = "reset"
                            st.rerun()
                        else:
                            st.error("Email not found in our system.")
                            
            elif st.session_state.recovery_stage == "reset":
                st.info("A recovery token has been generated. Check your terminal (PowerShell) to view it.")
                with st.form("reset_password_form"):
                    reset_token = st.text_input("Enter the 8-character Token")
                    new_pass = st.text_input("New Password", type="password")
                    new_pass_conf = st.text_input("Confirm New Password", type="password")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        submit_reset = st.form_submit_button("Reset Password", use_container_width=True)
                    with colB:
                        cancel_reset = st.form_submit_button("Cancel", use_container_width=True)
                        
                    if cancel_reset:
                        st.session_state.recovery_stage = "request"
                        st.rerun()
                        
                    if submit_reset:
                        if new_pass != new_pass_conf:
                            st.error("Passwords do not match.")
                        elif len(new_pass) < 6:
                            st.error("Password must be at least 6 characters.")
                        else:
                            success = reset_password(st.session_state.recovery_email, reset_token, new_pass)
                            if success:
                                st.success("Password reset successfully! You can now log in.")
                                st.session_state.recovery_stage = "request"
                            else:
                                st.error("Invalid or expired token.")

# ---------------------------------------------------------------------------
# MAIN DASHBOARD LOGIC
# ---------------------------------------------------------------------------
else:
    initialize_session_state()
    initialize_agent()

    st.sidebar.title("Navigation")
    
    menu_options = ["💼 Portfolio Manager", "⭐ Smart Watchlist", "📈 Interactive Charts"]
    if st.session_state.current_user.get("is_admin"):
        menu_options.append("🔐 Admin Panel")
        
    menu = st.sidebar.radio("Go to:", menu_options)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown(f"**Logged in as:**\n*{st.session_state.current_user['email']}*")
    if st.sidebar.button("Log Out"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("Agent powered by Gemini 3.5 Flash")

    head_col1, head_col2 = st.columns([5, 1])
    with head_col1:
        st.title(menu)
    with head_col2:
        st.write("") 
        render_chat_widget()

    if menu == "💼 Portfolio Manager":
        render_portfolio()
    elif menu == "⭐ Smart Watchlist":
        render_watchlist()
    elif menu == "📈 Interactive Charts":
        render_charts()
    elif menu == "🔐 Admin Panel":
        render_admin()
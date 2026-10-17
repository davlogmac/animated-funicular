import streamlit as st

def render_chat_widget():
    with st.popover("💬 AI Chat Agent", use_container_width=True):
        st.markdown("**Your Market Assistant**")
        
        chat_box = st.container(height=350)
        with chat_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        with st.form(key="chat_form", clear_on_submit=True, border=False):
            user_input = st.text_input("Ask a question:", placeholder="Press Enter to send...", label_visibility="collapsed")
            submit_btn = st.form_submit_button("Send", use_container_width=True)
            
        if submit_btn and user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(user_input)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing markets..."):
                        try:
                            response = st.session_state.chat_session.send_message(user_input)
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            error_msg = f"API Error: {e}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            st.rerun()
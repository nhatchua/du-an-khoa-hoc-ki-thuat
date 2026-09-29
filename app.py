import streamlit as st

st.set_page_config(page_title="Streamlit App", page_icon="🚀")

st.title("Chào mừng đến với Streamlit App! 👋")
st.write("Đây là ứng dụng web đơn giản chạy bằng Python.")

name = st.text_input("Nhập tên của bạn:")
if name:
    st.success(f"Xin chào {name}!")
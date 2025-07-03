import streamlit as st

# Page config
st.set_page_config(
    page_title="CatGDP - Feline whiskerful conversations.",
)

# Open new window/tab redirect
st.markdown("""
<script>
window.open("https://www.catgdp.com", "_blank");
</script>
""", unsafe_allow_html=True)

# Brief message for users
st.write("Redirecting to CatGDP...")

# Fallback link
st.markdown('[Click here if you are not redirected automatically](https://www.catgdp.com)', unsafe_allow_html=True)

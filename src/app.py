import streamlit as st

# Page config
st.set_page_config(
    page_title="CatGDP - Feline whiskerful conversations.",
)

# HTML meta refresh redirect
st.markdown("""
<meta http-equiv="refresh" content="0;url=https://www.catgdp.com">
<script>
window.location.href = "https://www.catgdp.com";
</script>
""", unsafe_allow_html=True)

# Brief message for users
st.write("Redirecting to CatGDP...")

# Fallback link
st.markdown('[Click here if you are not redirected automatically](https://www.catgdp.com)', unsafe_allow_html=True)

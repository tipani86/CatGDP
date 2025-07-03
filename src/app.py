import streamlit as st

# Page config
st.set_page_config(
    page_title="CatGDP - Feline whiskerful conversations.",
)

# # HTML meta refresh redirect
# st.markdown("""
# <meta http-equiv="refresh" content="0;url=https://www.catgdp.com">
# <script>
# if (window.top !== window.self) {
#     // We're in an iframe, break out of it
#     window.top.location.href = "https://www.catgdp.com";
# } else {
#     // Normal redirect
#     window.location.href = "https://www.catgdp.com";
# }
# </script>
# """, unsafe_allow_html=True)

# Brief message for users
st.write("Redirecting to CatGDP...")

# Fallback link
st.markdown('[Click here if you are not redirected automatically](https://www.catgdp.com)')

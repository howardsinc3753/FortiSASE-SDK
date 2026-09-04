"""
Entry point for the FortiSASE BOR / SPA toolkit (Streamlit multipage app).

Thin `st.navigation` launcher so the sidebar shows real, branded page titles instead of
raw filenames ("app"). Each page keeps its own `st.set_page_config`. Nothing else changed —
still launched with:  streamlit run app.py
"""
import streamlit as st

pages = [
    st.Page("generator_page.py", title="FortiSASE BOR & SPA Config Generator",
            icon="🛰️", default=True),
    st.Page("pages/1_FortiSASE_Tenant_Status.py", title="FortiSASE Tenant Status",
            icon="📊"),
    st.Page("pages/2_MSSP_Deploy.py", title="MSSP Deploy",
            icon="🚀"),
]
st.navigation(pages).run()

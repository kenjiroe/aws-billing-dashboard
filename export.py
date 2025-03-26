import pandas as pd
from fpdf import FPDF
import tempfile
import streamlit as st

def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="AWS Billing Report", ln=True)

    for index, row in df.iterrows():
        pdf.cell(200, 10, txt=f"{row['Account ID']} | {row['Service']} | ${row['Cost (USD)']:.4f}", ln=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            st.download_button("Export PDF", f, "billing_report.pdf")
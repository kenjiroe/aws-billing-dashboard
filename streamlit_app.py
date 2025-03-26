import streamlit as st
import boto3
import datetime
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os
import urllib3
from fpdf import FPDF

load_dotenv()
LINE_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

def send_line_notify(message):
    http = urllib3.PoolManager()
    http.request(
        "POST",
        "https://notify-api.line.me/api/notify",
        headers={
            "Authorization": f"Bearer {LINE_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body=f"message={message}".encode('utf-8')
    )

def export_pdf(df, total, month_text, filename="aws_billing_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"AWS Billing Report ({month_text})", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total Cost: ${total:.2f}", ln=True)

    pdf.ln(5)
    for index, row in df.iterrows():
        pdf.cell(200, 10, txt=f"{row['Service']} ({row['Account ID']}): ${row['Cost (USD)']:.2f}", ln=True)

    pdf.output(filename)

def fetch_billing_data_for_month(offset_months=0):
    client = boto3.client('ce')
    today = datetime.date.today()
    first_day = (today.replace(day=1) - pd.DateOffset(months=offset_months)).date()
    last_day = (first_day + pd.DateOffset(months=1)).date()

    response = client.get_cost_and_usage(
        TimePeriod={'Start': str(first_day), 'End': str(last_day)},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'},
            {'Type': 'DIMENSION', 'Key': 'SERVICE'}
        ]
    )

    data = []
    total = 0

    for group in response['ResultsByTime'][0]['Groups']:
        account_id, service = group['Keys']
        amount = float(group['Metrics']['UnblendedCost']['Amount'])
        if amount > 0:
            data.append({"Account ID": account_id, "Service": service, "Cost (USD)": amount})
            total += amount

    df = pd.DataFrame(data)
    return df, total, str(first_day), str(last_day)

# === STREAMLIT UI ===
st.set_page_config(page_title="AWS Billing Dashboard", layout="wide")
st.title("📊 AWS Billing Dashboard (Safe Version)")

months = st.selectbox("เลือกย้อนหลังกี่เดือน", options=list(range(0, 6)), format_func=lambda x: f"{x} เดือนที่ผ่านมา")

df, total, start, end = fetch_billing_data_for_month(months)
month_label = pd.to_datetime(start).strftime("%B %Y")

if df.empty:
    st.warning(f"📭 ไม่มีค่าใช้จ่ายในเดือน {month_label}")
else:
    st.markdown(f"### 📅 ข้อมูลเดือน: {month_label}")
    st.metric(label="รวมค่าใช้จ่าย (USD)", value=f"{total:.2f}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Bar Chart: ยอดแยกตามบริการ")
        fig_bar = px.bar(df, x="Service", y="Cost (USD)", color="Service", title="Cost by Service")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Pie Chart: สัดส่วนการใช้จ่าย")
        fig_pie = px.pie(df, values="Cost (USD)", names="Service", title="Cost Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.dataframe(df.sort_values(by="Cost (USD)", ascending=False), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        if st.button("🔔 แจ้งเตือนผ่าน LINE"):
            message_lines = [f"📊 AWS Billing ({month_label})", f"💰 รวมทั้งหมด: {total:.2f} USD\n"]
            for _, row in df.iterrows():
                message_lines.append(f"• {row['Service']} ({row['Account ID'][-4:]}): {row['Cost (USD)']:.2f} USD")
            if total > 4.0:
                send_line_notify("\n".join(message_lines))
                st.success("✅ แจ้งเตือน LINE แล้ว")
            else:
                st.info("ยอดยังไม่เกิน $4 จึงไม่แจ้งเตือน")

    with col4:
        if st.button("📄 Export PDF"):
            export_pdf(df, total, month_label)
            st.success("✅ บันทึก PDF แล้ว (aws_billing_report.pdf)")

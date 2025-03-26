import streamlit as st
import boto3
import pandas as pd
import altair as alt
import os

from fpdf import FPDF
from notifier import send_line_notify
from export import export_pdf
from datetime import date, timedelta

# load_dotenv()
# LINE_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]

st.set_page_config(page_title="AWS Billing Dashboard (Safe Version)", layout="wide")
st.markdown("## 📊 AWS Billing Dashboard (Safe Version)")

# เลือกย้อนหลัง
months_back = st.selectbox("เลือกย้อนหลังกี่เดือน", [0, 1, 2, 3, 6], index=0)

# คำนวณช่วงเวลา
today = date.today()
# start_date = (today - timedelta(days=30 * months_back)).replace(day=1)
start_date = (today - timedelta(days=30)).replace(day=1)  # เริ่มจากวันที่ 1 ของเดือนก่อน
# end_date = today.replace(day=1)
# ให้ end_date เป็นวันแรกของเดือนถัดไป
end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1)

# ใช้ AWS Cost Explorer API
client = boto3.client('ce', 
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
)

response = client.get_cost_and_usage(
    TimePeriod={
        'Start': start_date.strftime('%Y-%m-%d'),
        'End': end_date.strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost'],
    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
)

# แปลงเป็น DataFrame
records = []
# account_id = os.getenv("ACCOUNT_ID", "your-account-id")
for group in response['ResultsByTime'][0]['Groups']:
    service = group['Keys'][0]
    amount = float(group['Metrics']['UnblendedCost']['Amount'])
    if amount > 0:
        records.append({
            "Account ID": account_id,
            "Service": service,
            "Cost (USD)": amount
        })

df = pd.DataFrame(records)
# total = df['Cost (USD)'].sum()
if not df.empty and 'Cost (USD)' in df.columns:
    total = df['Cost (USD)'].sum()
    st.metric("รวมค่าใช้จ่าย (USD)", f"{total:.2f}")
else:
    total = 0.0
    st.warning("ไม่พบข้อมูลในช่วงเวลาที่เลือก")

# แสดงผล
st.markdown(f"### 📅 ข้อมูลเดือน: {start_date.strftime('%B %Y')}")
st.metric("รวมค่าใช้จ่าย (USD)", f"{total:.2f}")

# Bar และ Pie Charts
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Bar Chart: ยอดแยกตามบริการ")
    st.altair_chart(alt.Chart(df).mark_bar().encode(
        x=alt.X("Service", sort='-y'),
        y="Cost (USD)",
        color="Service"
    ).properties(height=300), use_container_width=True)

with col2:
    st.markdown("### Pie Chart: สัดส่วนการใช้จ่าย")
    st.altair_chart(alt.Chart(df).mark_arc(innerRadius=50).encode(
        theta="Cost (USD)",
        color="Service",
        tooltip=["Service", "Cost (USD)"]
    ), use_container_width=True)

# ตาราง
st.dataframe(df, use_container_width=True)

# ปุ่มแจ้งเตือน / export
col3, col4 = st.columns([1, 3])
with col3:
    if st.button("⚠️ แจ้งเตือนผ่าน LINE"):
        send_line_notify(f"📊 แจ้งเตือนงบเดือน {start_date.strftime('%B')} รวม: ${total:.2f}")
with col4:
    export_pdf(df)
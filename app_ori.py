import streamlit as st
import boto3
import pandas as pd
from datetime import date, timedelta
import altair as alt
from notifier import send_line_notify
from export import export_pdf
import os

sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]

st.set_page_config(page_title="AWS Billing Dashboard (Safe Version)", layout="wide")
st.markdown("## 📊 AWS Billing Dashboard (Safe Version)")

months_back = st.selectbox("เลือกย้อนหลังกี่เดือน", [0, 1, 2, 3, 6], index=0)

today = date.today()
start_date = (today - timedelta(days=30 * months_back)).replace(day=1)
end_date = (start_date + timedelta(days=32)).replace(day=1)

client = boto3.client('ce',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
)

try:
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]
except:
    account_id = "unknown"

response = client.get_cost_and_usage(
    TimePeriod={
        'Start': start_date.strftime('%Y-%m-%d'),
        'End': end_date.strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost'],
    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
)

records = []
groups = response['ResultsByTime'][0].get('Groups', [])
for group in groups:
    service = group['Keys'][0]
    amount = float(group['Metrics']['UnblendedCost']['Amount'])
    if amount > 0:
        records.append({
            "Account ID": account_id,
            "Service": service,
            "Cost (USD)": amount
        })

df = pd.DataFrame(records)

st.markdown(f"### 📅 ข้อมูลเดือน: {start_date.strftime('%B %Y')}")
if not df.empty and 'Cost (USD)' in df.columns:
    total = df['Cost (USD)'].sum()
    st.metric("รวมค่าใช้จ่าย (USD)", f"{total:.2f}")
else:
    st.warning("ไม่พบข้อมูลในช่วงเวลาที่เลือก")
    total = 0.0

col1, col2 = st.columns(2)
if not df.empty and 'Service' in df.columns:
    with col1:
        st.markdown("### Bar Chart: ยอดแยกตามบริการ")
        bar = alt.Chart(df).mark_bar().encode(
            x=alt.X("Service", sort='-y'),
            y="Cost (USD)",
            color="Service"
        ).properties(height=300)
        st.altair_chart(bar, use_container_width=True)

    with col2:
        st.markdown("### Pie Chart: สัดส่วนการใช้จ่าย")
        pie = alt.Chart(df).mark_arc(innerRadius=50).encode(
            theta="Cost (USD)",
            color="Service",
            tooltip=["Service", "Cost (USD)"]
        )
        st.altair_chart(pie, use_container_width=True)

st.dataframe(df, use_container_width=True)

col3, col4 = st.columns([1, 3])
with col3:
    if st.button("⚠️ แจ้งเตือนผ่าน LINE"):
        send_line_notify(f"📊 แจ้งเตือนงบเดือน {start_date.strftime('%B')} รวม: ${total:.2f}")
with col4:
    export_pdf(df)
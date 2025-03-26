# AWS Billing Dashboard (Advanced)

📊 Streamlit Dashboard สำหรับดูค่าใช้จ่าย AWS แบบย้อนหลัง พร้อมส่งออก PDF และแจ้งเตือน LINE Notify อัตโนมัติ

---

## ✅ ฟีเจอร์

- 🔍 ดูยอดใช้จ่ายย้อนหลัง 0–5 เดือน
- 📊 แสดงกราฟ Bar Chart / Pie Chart แยกตามบริการ
- 📄 ส่งออกเป็น PDF ได้ทันที
- 🔔 ส่งเข้า LINE ได้ทันที

---

## 📦 วิธีติดตั้ง

### 1. Clone หรือแตก zip
```bash
cd aws-billing-dashboard-advanced
```

### 2. ติดตั้ง dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า LINE Notify Token

สร้างไฟล์ `.env` แล้วใส่:
```env
LINE_TOKEN=your_line_notify_token
```

หรือใช้ `.env` ที่ให้มา แล้วใส่ Token แทนในบรรทัดนั้น

---

## ▶️ วิธีรัน

```bash
streamlit run streamlit_app.py
```
## Docker-run
docker build -t billing-dashboard .
docker run -p 8501:8501 --env-file .env billing-dashboard

---

## 📝 หมายเหตุ

- ต้องตั้งค่า `aws configure` ไว้แล้วในเครื่อง (ให้สามารถเรียก AWS CLI ได้)
- ใช้สิทธิ์ IAM ที่มี `ce:GetCostAndUsage` สำหรับเรียกข้อมูลจาก Cost Explorer
- สามารถแก้ `$5` ในโค้ดเป็น threshold ที่คุณต้องการ

---

## 💡 ต่อไปอาจเพิ่ม:
- ส่งออกรายงานเป็น Excel
- สรุปยอดรวมหลายเดือนในกราฟเดียว
- 🔔 แจ้งเตือนเข้า LINE ถ้ายอดรวมเกิน $5
- รองรับ Email / Telegram แจ้งเตือน

Local URL: http://localhost:8501
Network URL: http://0.0.0.0:8501
import streamlit as st
import pandas as pd
from fpdf import FPDF
import math
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="BG Calculator", page_icon="💰")

# --- Functions ---
def calculate_bg(total_gas_sum):
    avg_gas = total_gas_sum / 12
    avg_with_vat = avg_gas * 1.07
    bg_raw = avg_with_vat * 2
    
    # Logic: >= 1M ปัดเต็ม 1000, < 1M ปัดเต็ม 100
    if bg_raw >= 1000000:
        bg_final = math.ceil(bg_raw / 1000) * 1000
    else:
        bg_final = math.ceil(bg_raw / 100) * 100
        
    return avg_gas, avg_with_vat, bg_raw, bg_final

def create_pdf(customer_name, df_data, avg_gas, avg_with_vat, bg_raw, bg_final):
    pdf = FPDF()
    pdf.add_page()
    
    # ใช้ Font ธรรมดาไปก่อนนะเพื่อน เพื่อความชัวร์บน Server (ถ้าจะเอาไทยต้องโหลด Font ใส่ Folder)
    pdf.set_font("Arial", size=12)

    # Header
    pdf.cell(200, 10, txt="Bank Guarantee Calculation Report", ln=1, align='C')
    pdf.ln(10)
    
    # Info
    pdf.cell(200, 10, txt=f"Customer: {customer_name}", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1, align='L')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, "Month", 1)
    pdf.cell(60, 10, "Gas Cost (THB)", 1)
    pdf.ln()
    
    # Table Body
    pdf.set_font("Arial", size=12)
    for index, row in df_data.iterrows():
        pdf.cell(100, 10, row['Month'], 1)
        pdf.cell(60, 10, f"{row['Amount']:,.2f}", 1)
        pdf.ln()
        
    pdf.ln(10)
    
    # Calculation Show
    pdf.cell(0, 10, txt=f"1. Average (12 Months) = {avg_gas:,.2f} THB", ln=1)
    pdf.cell(0, 10, txt=f"2. Average + VAT 7% = {avg_with_vat:,.2f} THB", ln=1)
    pdf.cell(0, 10, txt=f"3. Initial BG (x2) = {bg_raw:,.2f} THB", ln=1)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt=f"4. FINAL BG = {bg_final:,.2f} THB", ln=1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Main App ---
st.title("💰 BG Calculator Platform")
st.write("สำหรับคำนวณ BG ลูกค้า (Smart Rounding)")

col1, col2 = st.columns([2, 1])
with col1:
    customer_name = st.text_input("Customer Name (ภาษาอังกฤษ)", "ABC Company Ltd.")

# Generate Months
months_list = []
today = datetime.today()
last_month = today.replace(day=1) - timedelta(days=1)
for i in range(12):
    m_name = (last_month.replace(day=1) - pd.DateOffset(months=i)).strftime('%B %Y')
    months_list.append(m_name)
months_list.reverse()

st.subheader("Input Data (12 Months)")
default_data = pd.DataFrame({'Month': months_list, 'Amount': [0.0]*12})
edited_df = st.data_editor(default_data, num_rows="fixed", hide_index=True)

if st.button("Calculate BG", type="primary"):
    total_sum = edited_df['Amount'].sum()
    if total_sum == 0:
        st.error("ใส่ตัวเลขก่อนเพื่อน!")
    else:
        avg, avg_vat, raw, final = calculate_bg(total_sum)
        
        st.success(f"✅ Final BG Amount: {final:,.2f} THB")
        st.write(f"*(From Raw: {raw:,.2f})*")
        
        pdf_bytes = create_pdf(customer_name, edited_df, avg, avg_vat, raw, final)
        st.download_button("Download PDF Report", data=pdf_bytes, file_name="bg_report.pdf", mime="application/pdf")

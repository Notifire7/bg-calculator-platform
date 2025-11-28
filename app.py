import streamlit as st
import pandas as pd
from fpdf import FPDF
import math
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="BG Calculator", page_icon="💰")

# --- Functions ---
def calculate_bg(total_gas_sum):
    # total_gas_sum คือผลรวมของ (Cn + Sn) ทั้ง 12 เดือนแล้ว
    avg_gas = total_gas_sum / 12
    avg_with_vat = avg_gas * 1.07
    bg_raw = avg_with_vat * 2
    
    # Logic ปัดเศษ: >= 1M ปัดเต็ม 1000, < 1M ปัดเต็ม 100
    if bg_raw >= 1000000:
        bg_final = math.ceil(bg_raw / 1000) * 1000
    else:
        bg_final = math.ceil(bg_raw / 100) * 100
        
    return avg_gas, avg_with_vat, bg_raw, bg_final

def create_pdf(customer_name, df_data, avg_gas, avg_with_vat, bg_raw, bg_final):
    pdf = FPDF()
    pdf.add_page()
    
    # ใช้ Font ธรรมดา (พิมพ์อังกฤษเท่านั้นนะเพื่อน ถึงจะไม่ Error)
    pdf.set_font("Arial", size=11)

    # Header
    pdf.cell(200, 10, txt="Bank Guarantee Calculation Report", ln=1, align='C')
    pdf.ln(5)
    
    # Info
    pdf.cell(200, 8, txt=f"Customer: {customer_name}", ln=1, align='L')
    pdf.cell(200, 8, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1, align='L')
    pdf.ln(5)
    
    # Table Header (เพิ่มช่อง Cn, Sn ให้ดูโปร)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, "Month", 1)
    pdf.cell(40, 10, "Cn (THB)", 1)
    pdf.cell(40, 10, "Sn (THB)", 1)
    pdf.cell(45, 10, "Total (THB)", 1)
    pdf.ln()
    
    # Table Body
    pdf.set_font("Arial", size=10)
    for index, row in df_data.iterrows():
        total_row = row['Cn'] + row['Sn']
        pdf.cell(60, 10, row['Month'], 1)
        pdf.cell(40, 10, f"{row['Cn']:,.2f}", 1)
        pdf.cell(40, 10, f"{row['Sn']:,.2f}", 1)
        pdf.cell(45, 10, f"{total_row:,.2f}", 1)
        pdf.ln()
        
    pdf.ln(10)
    
    # Calculation Show
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt=f"1. Total Gas (12 Months) = {df_data['Cn'].sum() + df_data['Sn'].sum():,.2f} THB", ln=1)
    pdf.cell(0, 8, txt=f"2. Average/Month = {avg_gas:,.2f} THB", ln=1)
    pdf.cell(0, 8, txt=f"3. Average + VAT 7% = {avg_with_vat:,.2f} THB", ln=1)
    pdf.cell(0, 8, txt=f"4. Initial BG (x2) = {bg_raw:,.2f} THB", ln=1)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 12, txt=f"5. FINAL BG = {bg_final:,.2f} THB", ln=1)
    
    # แก้ Error ภาษาไทยตรงนี้ (ใส่ ignore)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- Main App ---
st.title("💰 BG Calculator (Cn + Sn)")
st.write("ระบุค่า Cn และ Sn แยกกัน (โปรแกรมรวมให้เอง)")

col1, col2 = st.columns([2, 1])
with col1:
    customer_name = st.text_input("Customer Name (ENG Only)", "ABC Company Ltd.")

# Generate Months
months_list = []
today = datetime.today()
last_month = today.replace(day=1) - timedelta(days=1)
for i in range(12):
    m_name = (last_month.replace(day=1) - pd.DateOffset(months=i)).strftime('%B %Y')
    months_list.append(m_name)
months_list.reverse()

# Input Data Grid (เพิ่ม Cn, Sn)
st.subheader("Input Data (Cn & Sn exclude VAT)")
default_data = pd.DataFrame({
    'Month': months_list, 
    'Cn': [0.0]*12,
    'Sn': [0.0]*12
})

edited_df = st.data_editor(
    default_data, 
    column_config={
        "Cn": st.column_config.NumberColumn("Cn Amount", format="%.2f"),
        "Sn": st.column_config.NumberColumn("Sn Amount", format="%.2f")
    },
    num_rows="fixed", 
    hide_index=True,
    use_container_width=True
)

if st.button("Calculate BG", type="primary"):
    # คำนวณยอดรวม: (Sum Cn) + (Sum Sn)
    total_cn = edited_df['Cn'].sum()
    total_sn = edited_df['Sn'].sum()
    total_all = total_cn + total_sn
    
    if total_all == 0:
        st.error("ใส่ตัวเลขก่อนเพื่อน! (Cn หรือ Sn ก็ได้)")
    else:
        avg, avg_vat, raw, final = calculate_bg(total_all)
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Cn", f"{total_cn:,.2f}")
        c2.metric("Total Sn", f"{total_sn:,.2f}")
        c3.metric("Grand Total", f"{total_all:,.2f}")
        
        st.success(f"🏁 Final BG Amount: {final:,.2f} THB")
        
        # สร้าง PDF
        pdf_bytes = create_pdf(customer_name, edited_df, avg, avg_vat, raw, final)
        st.download_button("Download PDF Report", data=pdf_bytes, file_name="bg_report.pdf", mime="application/pdf")



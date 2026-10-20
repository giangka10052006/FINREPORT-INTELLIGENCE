import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="FinReport Intelligence", layout="wide")

st.title("📈 FinReport Intelligence System")
st.subheader("Hệ thống Phân tích & Cảnh báo Sức khỏe Tài chính Doanh nghiệp")


@st.cache_data
def load_data():
    master_df = pd.read_csv("output/master_financial_data.csv")
    with open("output/alerts_with_traceability.json", "r", encoding="utf-8") as f:
        alerts = json.load(f)
    return master_df, alerts


try:
    df, alerts = load_data()

    company_list = df['company_id'].unique()
    selected_company = st.sidebar.selectbox("Chọn Doanh nghiệp", company_list)

    comp_df = df[df['company_id'] == selected_company]

    col1, col2, col3, col4 = st.columns(4)
    latest = comp_df[comp_df['fiscal_year'] == 2025].iloc[0]

    # Đã sửa lại tên cột khớp với file CSV (_vnd_mn)
    col1.metric("Doanh thu 2025", f"{latest['revenue_vnd_mn']:,.0f}")
    col2.metric("LN Ròng 2025", f"{latest['net_income_vnd_mn']:,.0f}")
    col3.metric("Biên Lợi Nhuận Ròng", f"{latest['net_margin']:.1%}")
    col4.metric("Nợ / Vốn Chủ", f"{latest['debt_to_equity']:.2f}x")

    tab1, tab2, tab3 = st.tabs([
        " XU HƯỚNG TÀI CHÍNH",
        " TÍN HIỆU CẢNH BÁO",
        " TRUY VẾT BẰNG CHỨNG"
    ])

    with tab1:
        st.write("### Xu hướng Doanh thu vs Lợi nhuận qua các năm")
        st.line_chart(comp_df.set_index('fiscal_year')[
            ['revenue_vnd_mn', 'net_income_vnd_mn',
                'net_cash_from_operating_activities_vnd_mn']
        ])

        st.write("### Biên Lợi nhuận Ròng & ROE")
        st.line_chart(comp_df.set_index('fiscal_year')[['net_margin', 'roe']])

    with tab2:
        st.write("### Các Tín hiệu Bất thường Cần Lưu ý")
        comp_alerts = [
            a for a in alerts if a['company_id'] == selected_company]
        if comp_alerts:
            for a in comp_alerts:
                color = "red" if a['severity'] == "CRITICAL" else "orange" if a['severity'] == "HIGH" else "blue"
                st.markdown(
                    f":{color}[**[{a['severity']}] {a['signal_type']} (Năm {a['fiscal_year']})**]")
                st.write(a['message'])
                st.divider()
        else:
            st.success("Không phát hiện tín hiệu rủi ro nghiêm trọng.")

    with tab3:
        st.write("### Chi tiết Bằng chứng Truy vết (Audit Trail)")
        comp_alerts = [
            a for a in alerts if a['company_id'] == selected_company]
        st.json(comp_alerts)

except Exception as e:
    st.error(
        f"Lỗi: {e}. Vui lòng đảm bảo bạn đã chạy file `pipeline_finreport.py` trước!")

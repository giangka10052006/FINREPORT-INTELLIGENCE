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

    # Tạo các tab phân chia chuyên sâu theo nhóm chỉ tiêu
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Tăng trưởng & Biên LN",
        "⚖️ Thanh khoản & Đòn bẩy",
        "🔄 Vòng quay & Vận hành",
        "💰 Dòng tiền & FCF",
        "🚨 Cảnh báo & Truy vết"
    ])

    with tab1:
        st.write("### 1. Tốc độ Tăng trưởng Doanh thu (%)")
        if 'revenue_growth' in comp_df.columns:
            st.line_chart(comp_df.set_index('fiscal_year')[['revenue_growth']])
        else:
            # Nếu pipeline chưa tính sẵn, tính trực tiếp trên DataFrame
            comp_df['revenue_growth'] = comp_df['revenue_vnd_mn'].pct_change() * \
                100
            st.line_chart(comp_df.set_index('fiscal_year')[['revenue_growth']])

        st.write("### 2. Các chỉ tiêu Biên Lợi nhuận (%)")
        # Gross Margin, Operating Margin, Net Margin
        margin_cols = [c for c in ['gross_margin',
                                'operating_margin', 'net_margin'] if c in comp_df.columns]
        if not margin_cols:
            # Tự tính nếu chưa có trong master_df
            comp_df['gross_margin'] = (
                comp_df['gross_profit_vnd_mn'] / comp_df['revenue_vnd_mn']) * 100
            comp_df['operating_margin'] = (
                comp_df['operating_profit_vnd_mn'] / comp_df['revenue_vnd_mn']) * 100
            comp_df['net_margin'] = (
                comp_df['net_income_vnd_mn'] / comp_df['revenue_vnd_mn']) * 100
            margin_cols = ['gross_margin', 'operating_margin', 'net_margin']
        st.line_chart(comp_df.set_index('fiscal_year')[margin_cols])

        st.write("### 3. Hiệu suất sinh lời ROA, ROE (%) & Interest Coverage")
        profitability_cols = [c for c in ['roa', 'roe',
                                        'interest_coverage'] if c in comp_df.columns]
        st.line_chart(comp_df.set_index('fiscal_year')[profitability_cols])

    with tab2:
        st.write("### 1. Khả năng Thanh khoản (Current Ratio & Quick Ratio)")
        liquidity_cols = [c for c in ['current_ratio',
                                    'quick_ratio'] if c in comp_df.columns]
        if not liquidity_cols:
            comp_df['current_ratio'] = comp_df['total_current_assets_vnd_mn'] / \
                comp_df['total_current_liabilities_vnd_mn']
            comp_df['quick_ratio'] = (comp_df['cash_and_cash_equivalents_vnd_mn'] +
                                    comp_df['accounts_receivable_vnd_mn']) / comp_df['total_current_liabilities_vnd_mn']
            liquidity_cols = ['current_ratio', 'quick_ratio']
        st.line_chart(comp_df.set_index('fiscal_year')[liquidity_cols])

        st.write("### 2. Đòn bẩy tài chính (Debt/Assets & Debt/Equity)")
        leverage_cols = [c for c in ['debt_to_assets',
                                    'debt_to_equity'] if c in comp_df.columns]
        st.line_chart(comp_df.set_index('fiscal_year')[leverage_cols])

        st.write("### 3. Vốn lưu động thuần (Working Capital)")
        if 'working_capital' in comp_df.columns:
            st.line_chart(comp_df.set_index(
                'fiscal_year')[['working_capital']])
        else:
            comp_df['working_capital'] = comp_df['total_current_assets_vnd_mn'] - \
                comp_df['total_current_liabilities_vnd_mn']
            st.line_chart(comp_df.set_index(
                'fiscal_year')[['working_capital']])

    with tab3:
        st.write(
            "### Vòng quay Vốn lưu động (DSO, Inventory Days, DPO - Tính bằng ngày)")
        days_cols = [c for c in ['dso', 'inventory_days', 'dpo']
                    if c in comp_df.columns]
        if days_cols:
            st.line_chart(comp_df.set_index('fiscal_year')[days_cols])
        else:
            st.info(
                "Chưa có sẵn các chỉ số ngày vòng quay trong master_df. Bạn có thể bổ sung logic tính toán vào pipeline.")

    with tab4:
        st.write("### 1. Chất lượng dòng tiền (CFO / Net Income)")
        if 'cfo_to_net_income' in comp_df.columns:
            st.line_chart(comp_df.set_index('fiscal_year')
                        [['cfo_to_net_income']])
        else:
            comp_df['cfo_to_net_income'] = comp_df['net_cash_from_operating_activities_vnd_mn'] / \
                comp_df['net_income_vnd_mn']
            st.line_chart(comp_df.set_index('fiscal_year')
                        [['cfo_to_net_income']])

        st.write("### 2. Dòng tiền tự do (Free Cash Flow - FCF)")
        if 'free_cash_flow' in comp_df.columns:
            st.line_chart(comp_df.set_index('fiscal_year')[['free_cash_flow']])
        else:
            # Do capital_expenditure_vnd_mn đã mang dấu âm
            comp_df['free_cash_flow'] = comp_df['net_cash_from_operating_activities_vnd_mn'] + \
                comp_df['capital_expenditure_vnd_mn']
            st.line_chart(comp_df.set_index('fiscal_year')[['free_cash_flow']])

    with tab5:
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

        st.write("### Chi tiết Bằng chứng Truy vết (Audit Trail)")
        st.json(comp_alerts)

except Exception as e:
    st.error(
        f"Lỗi: {e}. Vui lòng đảm bảo bạn đã chạy file `pipeline_finreport.py` trước!")

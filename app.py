import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

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

    col1.metric("Doanh thu 2025", f"{latest['revenue_vnd_mn']:,.0f}")
    col2.metric("LN Ròng 2025", f"{latest['net_income_vnd_mn']:,.0f}")
    col3.metric("Biên Lợi Nhuận Ròng", f"{latest['net_margin']:.1%}")
    col4.metric("Nợ / Vốn Chủ", f"{latest['debt_to_equity']:.2f}x")

    # Tạo các tab phân chia chuyên sâu theo nhóm chỉ tiêu
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Tăng trưởng & Biên LN",
        "⚖️ Thanh khoản & Đòn bẩy",
        "🔄 Vòng quay & Vận hành",
        "💰 Dòng tiền & FCF",
        "📊 Phân tích & Biểu đồ Chuyên sâu",
        "🚨 Cảnh báo & Truy vết"
    ])

    with tab1:
        st.write("### 1. Tốc độ Tăng trưởng Doanh thu (%)")
        if 'revenue_growth' in comp_df.columns:
            st.line_chart(comp_df.set_index('fiscal_year')[['revenue_growth']])
        else:
            comp_df['revenue_growth'] = comp_df['revenue_vnd_mn'].pct_change() * \
                100
            st.line_chart(comp_df.set_index('fiscal_year')[['revenue_growth']])

        st.write("### 2. Các chỉ tiêu Biên Lợi nhuận (%)")
        margin_cols = [c for c in ['gross_margin',
                                'operating_margin', 'net_margin'] if c in comp_df.columns]
        if not margin_cols:
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
            st.info("Chưa có sẵn các chỉ số ngày vòng quay trong master_df.")

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
            comp_df['free_cash_flow'] = comp_df['net_cash_from_operating_activities_vnd_mn'] + \
                comp_df['capital_expenditure_vnd_mn']
            st.line_chart(comp_df.set_index('fiscal_year')[['free_cash_flow']])

    with tab5:
        st.write(f"### 📊 Phân tích Chi tiết Doanh nghiệp: {selected_company}")

        # 1. Histogram - Phân Bố Số Tiền Giao Dịch (Lấy từ doanh thu qua các năm của doanh nghiệp)
        st.subheader("Histogram - Phan Bo So Tien Giao Dich")
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        sns.histplot(comp_df['revenue_vnd_mn'], bins=18, color='#5DADE2',
                    edgecolor='black', alpha=0.8, ax=ax1, shrink=0.85)
        ax1.set_title("Histogram - Phan Bo So Tien Giao Dich",
                    fontsize=12, fontweight='bold')
        ax1.set_xlabel("Số tiền (VND/USD)", fontsize=10)
        ax1.set_ylabel("Tần suất", fontsize=10)
        ax1.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig1)

        # 2. Zigzag - Đường xu hướng giao dịch theo thời gian (Lấy doanh thu theo từng năm của doanh nghiệp)
        st.subheader("Zigzag - Duong xu huong giao dich theo thoi gian")
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        years = comp_df['fiscal_year']
        revenues = comp_df['revenue_vnd_mn']
        ax2.plot(years, revenues, marker='o', color='#E74C3C',
                linewidth=2, label='Tong so tien hang ngay')
        ax2.fill_between(years, revenues, color='#FADBD8', alpha=0.5)
        ax2.set_title("Zigzag - Duong xu huong giao dich theo thoi gian",
                    fontsize=12, fontweight='bold')
        ax2.set_xlabel("Ngay giao dịch", fontsize=10)
        ax2.set_ylabel("So tien (VND/USD)", fontsize=10)
        ax2.legend(loc='upper left')
        ax2.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig2)

        # 3. Zigzag - Số tiền tích lũy theo thời gian (Tính tổng tích lũy doanh thu của doanh nghiệp qua các năm)
        st.subheader("Zigzag - So tien tich luy theo thoi gian")
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        cumulative_rev = revenues.cumsum()
        ax3.plot(years, cumulative_rev, marker='o', color='#27AE60',
                linewidth=2, label='So tien tich luy')
        ax3.fill_between(years, cumulative_rev, color='#D4EFDF', alpha=0.5)
        ax3.set_title("Zigzag - So tien tich luy theo thoi gian",
                    fontsize=12, fontweight='bold')
        ax3.set_xlabel("Ngay giao dịch", fontsize=10)
        ax3.set_ylabel("So tien tich luy (VND/USD)", fontsize=10)
        ax3.legend(loc='upper left')
        ax3.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig3)

        # 2 biểu đồ tròn cấu trúc giống hệt mẫu nhưng số liệu chia theo cơ cấu tài chính thực tế của doanh nghiệp đó
        col_pie1, col_pie2 = st.columns(2)

        with col_pie1:
            st.subheader("Bieu do Tron - Phan bo loai giao dich")
            fig4, ax4 = plt.subplots(figsize=(5, 5))

            # Lấy số liệu năm mới nhất của doanh nghiệp để phân rã cơ cấu chi phí/doanh thu làm loại giao dịch
            latest_r = comp_df.iloc[-1]
            cogs = latest_r['cost_of_goods_sold_vnd_mn']
            sell_exp = latest_r['selling_expense_vnd_mn']
            admin_exp = latest_r['administrative_expense_vnd_mn']
            tax = latest_r['income_tax_expense_vnd_mn']
            net_inc = latest_r['net_income_vnd_mn']

            sizes_type = [cogs, sell_exp, admin_exp, tax, net_inc]
            labels_type = ['Giá vốn hàng bán', 'Chi phí bán hàng',
                        'Chi phí quản lý', 'Thuế TNDN', 'Lợi nhuận ròng']
            colors_type = ['#FA8072', '#48C9B0',
                        '#5DADE2', '#F8C471', '#A3E4D7']

            ax4.pie(sizes_type, labels=labels_type, autopct='%1.1f%%',
                    startangle=90, colors=colors_type, textprops={'fontsize': 8})
            ax4.set_title("Bieu do Tron - Phan bo loai giao dich",
                        fontsize=11, fontweight='bold')
            st.pyplot(fig4)

        with col_pie2:
            st.subheader("Bieu do Tron - Phan bo tien te")
            fig5, ax5 = plt.subplots(figsize=(5, 5))

            # Phân bổ nguồn vốn chủ sở hữu và tổng nợ phải trả làm tỷ trọng tiền tệ/nguồn vốn
            liab = latest_r['total_liabilities_vnd_mn']
            eq = latest_r['total_equity_vnd_mn']

            sizes_curr = [liab, eq]
            labels_curr = ['Nợ phải trả (VND)', 'Vốn chủ sở hữu (VND)']
            colors_curr = ['#5DADE2', '#F8C471']

            ax5.pie(sizes_curr, labels=labels_curr, autopct='%1.1f%%',
                    startangle=90, colors=colors_curr, textprops={'fontsize': 9})
            ax5.set_title("Bieu do Tron - Phan bo tien te",
                        fontsize=11, fontweight='bold')
            st.pyplot(fig5)

    with tab6:
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

import pandas as pd
import numpy as np
import json
import os


class FinReportPipeline:
    def __init__(self, data_dir="data", metadata_dir="metadata"):
        self.data_dir = data_dir
        self.metadata_dir = metadata_dir
        self.master_df = None
        self.alerts = []

    def load_and_validate_data(self):
        print("Bắt đầu Kiểm định & Hợp nhất dữ liệu...")

        bs = pd.read_csv(os.path.join(self.data_dir, "balance_sheet.csv"))
        cf = pd.read_csv(os.path.join(self.data_dir, "cashflow.csv"))
        is_df = pd.read_csv(os.path.join(
            self.data_dir, "income_statement.csv"))
        info = pd.read_csv(os.path.join(self.data_dir, "company_info.csv"))
        notes = pd.read_csv(os.path.join(self.data_dir, "financial_notes.csv"))

        assert len(
            info) == 12, f"File company_info có {len(info)} dòng (cần 12)!"
        for name, df in [("balance_sheet", bs), ("cashflow", cf), ("income_statement", is_df), ("financial_notes", notes)]:
            assert len(df) == 60, f"File {name} có {len(df)} dòng (cần 60)!"

        master = bs.merge(cf, on=['company_id', 'fiscal_year'], how='inner', suffixes=('', '_cf')) \
                .merge(is_df, on=['company_id', 'fiscal_year'], how='inner', suffixes=('', '_is')) \
                .merge(notes, on=['company_id', 'fiscal_year'], how='inner', suffixes=('', '_notes')) \
                .merge(info, on='company_id', how='inner', suffixes=('', '_info'))

        assert len(
            master) == 60, f"Bảng Master bị lệch số dòng: {len(master)} dòng (cần 60)!"
        assert master[['company_id', 'fiscal_year']].duplicated().sum(
        ) == 0, "Bị trùng lặp khóa (company_id + fiscal_year)!"

        print("  Đang chạy 3 Phép kiểm tra Kế toán Bắt buộc...")

        bs_check = np.isclose(
            master['total_assets_vnd_mn'], master['total_liabilities_vnd_mn'] + master['total_equity_vnd_mn'], atol=1e-3)
        assert bs_check.all(), "Phép kiểm 1 Thất bại: Tài sản != Nợ + Vốn chủ!"

        cf_check = np.isclose(master['beginning_cash_vnd_mn'] +
                            master['net_change_in_cash_vnd_mn'], master['ending_cash_vnd_mn'], atol=1e-3)
        assert cf_check.all(), "Phép kiểm 2 Thất bại: Tiền đầu kỳ + Biến động != Tiền cuối kỳ!"

        
        cross_check = np.isclose(
            master['ending_cash_vnd_mn'], master['cash_and_cash_equivalents_vnd_mn'], atol=1e-3)
        assert cross_check.all(), "Phép kiểm 3 Thất bại: Tiền cuối kỳ trên LCT khác CĐKT!"

        print("  Dữ liệu Master SẠCH & ĐẠT CHUẨN KẾ TOÁN (60 dòng, khóa duy nhất, 3/3 phép kiểm pass).")
        self.master_df = master.sort_values(
            by=['company_id', 'fiscal_year']).reset_index(drop=True)
        return self.master_df

    def calculate_metrics(self):
        print(" Đang tính toán các chỉ tiêu tài chính & Tỷ số...")
        df = self.master_df

        df['gross_margin'] = df['gross_profit_vnd_mn'] / df['revenue_vnd_mn']
        df['net_margin'] = df['net_income_vnd_mn'] / df['revenue_vnd_mn']
        df['roa'] = df['net_income_vnd_mn'] / df['total_assets_vnd_mn']
        df['roe'] = df['net_income_vnd_mn'] / df['total_equity_vnd_mn']

        df['debt_to_equity'] = df['total_liabilities_vnd_mn'] / \
            df['total_equity_vnd_mn']
        df['current_ratio'] = df['total_current_assets_vnd_mn'] / \
            df['total_current_liabilities_vnd_mn']

        df['cfo_to_net_income'] = df['net_cash_from_operating_activities_vnd_mn'] / \
            df['net_income_vnd_mn']

        df['rev_growth_yoy'] = df.groupby(
            'company_id')['revenue_vnd_mn'].pct_change()
        df['rec_growth_yoy'] = df.groupby(
            'company_id')['accounts_receivable_vnd_mn'].pct_change()
        df['inv_growth_yoy'] = df.groupby(
            'company_id')['inventory_vnd_mn'].pct_change()

        self.master_df = df
        print("  Đã tính xong nhóm tỷ số: Margin, Liquidity, Leverage, YoY Growth.")

    def detect_signals_and_alerts(self):
        print(" Đang quét các tín hiệu bất thường & Cảnh báo...")
        self.alerts = []

        for idx, row in self.master_df.iterrows():
            cid = row['company_id']
            year = int(row['fiscal_year'])

            if pd.notnull(row['rec_growth_yoy']) and pd.notnull(row['rev_growth_yoy']):
                if row['rec_growth_yoy'] > row['rev_growth_yoy'] + 0.15:
                    self.alerts.append({
                        "company_id": cid,
                        "fiscal_year": year,
                        "signal_type": "RECEIVABLES_SPIKE",
                        "severity": "HIGH",
                        "message": f"Tốc độ tăng khoản phải thu ({row['rec_growth_yoy']:.1%}) vượt xa tốc độ tăng doanh thu ({row['rev_growth_yoy']:.1%}).",
                        "evidence_trace": {
                            "file": "balance_sheet.csv & income_statement.csv",
                            "fields": ["accounts_receivable_vnd_mn", "revenue_vnd_mn"],
                            "period": f"{year-1}-{year}"
                        }
                    })

            if row['net_income_vnd_mn'] > 0 and row['net_cash_from_operating_activities_vnd_mn'] < 0:
                self.alerts.append({
                    "company_id": cid,
                    "fiscal_year": year,
                    "signal_type": "LOW_EARNINGS_QUALITY",
                    "severity": "CRITICAL",
                    "message": f"Lợi nhuận ròng dương ({row['net_income_vnd_mn']:,.0f}) nhưng Dòng tiền kinh doanh (CFO) âm ({row['net_cash_from_operating_activities_vnd_mn']:,.0f}).",
                    "evidence_trace": {
                        "file": "income_statement.csv & cashflow.csv",
                        "fields": ["net_income_vnd_mn", "net_cash_from_operating_activities_vnd_mn"],
                        "period": str(year)
                    }
                })

            if row['debt_to_equity'] > 2.5:
                self.alerts.append({
                    "company_id": cid,
                    "fiscal_year": year,
                    "signal_type": "HIGH_LEVERAGE",
                    "severity": "MEDIUM",
                    "message": f"Tỷ lệ Nợ/Vốn chủ sở hữu đạt mức rủi ro cao: {row['debt_to_equity']:.2f}x.",
                    "evidence_trace": {
                        "file": "balance_sheet.csv",
                        "fields": ["total_liabilities_vnd_mn", "total_equity_vnd_mn"],
                        "period": str(year)
                    }
                })

        print(
            f"  Đã phát hiện {len(self.alerts)} cảnh báo có đầy đủ bằng chứng truy vết.")


    def export_results(self, output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)

        # Bổ sung tính toán các chỉ số tài chính nâng cao trước khi xuất file
        self.master_df['dso'] = (
            self.master_df['accounts_receivable_vnd_mn'] / self.master_df['revenue_vnd_mn']) * 365
        self.master_df['inventory_days'] = (
            self.master_df['inventory_vnd_mn'] / self.master_df['cost_of_goods_sold_vnd_mn']) * 365
        self.master_df['dpo'] = (self.master_df['accounts_payable_vnd_mn'] /
                                 self.master_df['cost_of_goods_sold_vnd_mn']) * 365
        self.master_df['working_capital'] = self.master_df['total_current_assets_vnd_mn'] - \
            self.master_df['total_current_liabilities_vnd_mn']
        self.master_df['free_cash_flow'] = self.master_df['net_cash_from_operating_activities_vnd_mn'] + \
            self.master_df['capital_expenditure_vnd_mn']
        self.master_df['cfo_to_net_income'] = self.master_df['net_cash_from_operating_activities_vnd_mn'] / \
            self.master_df['net_income_vnd_mn']

        master_path = os.path.join(output_dir, "master_financial_data.csv")
        self.master_df.to_csv(master_path, index=False)

        alerts_path = os.path.join(output_dir, "alerts_with_traceability.json")
        with open(alerts_path, "w", encoding="utf-8") as f:
            json.dump(self.alerts, f, ensure_ascii=False, indent=2)

        print(f"Đã xuất kết quả thành công vào thư mục `{output_dir}/`:")
        print(f"   - Bảng Master: {master_path}")
        print(f"   - Tệp Cảnh báo: {alerts_path}")


# KHỞI CHẠY PIPELINE
if __name__ == "__main__":
    pipeline = FinReportPipeline()
    pipeline.load_and_validate_data()
    pipeline.calculate_metrics()
    pipeline.detect_signals_and_alerts()
    pipeline.export_results()

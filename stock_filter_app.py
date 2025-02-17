import numpy as np
import pandas as pd
import re
from datetime import datetime
import streamlit as st

# ========================= Các hàm lọc =========================
## Tiêu chí 1
def parse_date(date_str):
    """
    Chuyển đổi chuỗi ngày tháng thành đối tượng datetime.
    Hỗ trợ nhiều định dạng ngày khác nhau.
    """
    formats = ['%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%Y-%m-%d']
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            if parsed_date.year > datetime.today().year:  # Loại bỏ năm quá lớn
                return None
            return parsed_date
        except ValueError:
            continue
    
    # Xử lý trường hợp chỉ có năm (yyyy)
    if re.fullmatch(r'\d{4}', date_str):
        year = int(date_str)
        if 1900 <= year <= datetime.today().year:
            return datetime(year, 1, 1)  # Lấy giả định ngày 01/01 của năm đó
    return None

def extract_relevant_dates(text):
    """
    Trích xuất các ngày niêm yết và giao dịch từ văn bản lịch sử.
    """
    date_patterns = [
        r'\b(\d{2}/\d{2}/\d{4})\b',  # dd/mm/yyyy hoặc mm/dd/yyyy
        r'\b(\d{2}/\d{4})\b',        # mm/yyyy
        r'\b(?:năm\s*)?(\d{4})\b'    # yyyy hoặc "Năm yyyy"
    ]
    
    text_lower = text.lower()
    relevant_dates = {'niêm yết': [], 'giao dịch': []}
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            date_str = match.group(1)
            date = parse_date(date_str)
            if not date:
                continue

            # Kiểm tra nội dung trước và sau ngày tìm thấy
            before_context = text_lower[max(0, match.start() - 50): match.start()]
            after_context = text_lower[match.end(): match.end() + 200]
            full_context = before_context + " " + after_context

            if any(x in full_context for x in ['hose', 'sở giao dịch chứng khoán thành phố hồ chí minh',
                                               'sở giao dịch chứng khoán tp. Hồ Chí Minh',
                                               'sở giao dịch chứng khoán tp hcm', 'ttgd ck tp.hcm',
                                               'trung tâm giao dịch chứng khoán thành phố hồ chí minh',
                                               'sàn giao dịch chứng khoán thành phố hồ chí minh']):
                if 'niêm yết' in full_context:
                    relevant_dates['niêm yết'].append(date)
                if 'giao dịch' in full_context:
                    relevant_dates['giao dịch'].append(date)
    
    return relevant_dates

def filter_stocks_full_list(df):
    """
    Kiểm tra danh sách cổ phiếu dựa trên tiêu chí số năm hoạt động >= 5 năm trên HOSE.
    """
    result = []
    current_date = datetime.today()
    
    for _, row in df.iterrows():
        ma_co_phieu = row["ticker"]  # Mã chứng khoán
        history_text = row["history_dev"]  # Lịch sử niêm yết/giao dịch
        
        if pd.isna(history_text) or not isinstance(history_text, str):
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Kết quả kiểm tra": "Không đạt",
                "Lý do": "Không có dữ liệu",
                "Lịch sử niêm yết": history_text
            })
            continue
        
        dates = extract_relevant_dates(history_text)
        
        # Chọn ngày giao dịch cuối cùng nếu có, nếu không lấy ngày niêm yết
        last_date = max(dates['giao dịch']) if dates['giao dịch'] else (
            max(dates['niêm yết']) if dates['niêm yết'] else None)
        
        if not last_date:
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Kết quả kiểm tra": "Không đạt",
                "Lý do": "Không tìm thấy ngày niêm yết hoặc giao dịch",
                "Lịch sử niêm yết": history_text
            })
            continue
        
        # Tính số năm hoạt động dựa trên ngày giao dịch cuối cùng
        years_active = round((current_date - last_date).days / 365, 2)
        
        text_lower = history_text.lower()
        if years_active >= 5 and any(x in text_lower for x in ['hose', 'sở giao dịch chứng khoán thành phố hồ chí minh',
                                                               'sở giao dịch chứng khoán tp. Hồ Chí Minh',
                                                               'sở giao dịch chứng khoán tp hcm', 'ttgd ck tp.hcm',
                                                               'trung tâm giao dịch chứng khoán thành phố hồ chí minh',
                                                               'sàn giao dịch chứng khoán thành phố hồ chí minh']):
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Ngày giao dịch cuối cùng": last_date.strftime("%d/%m/%Y"),
                "Số năm hoạt động": years_active,
                "Kết quả kiểm tra": "Đạt",
                "Lý do": "Đủ điều kiện (>=5 năm + HOSE)",
                "Lịch sử niêm yết": history_text
            })
        else:
            reason = "Không có HOSE" if years_active >= 5 else "Thời gian hoạt động < 5 năm"
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Ngày giao dịch cuối cùng": last_date.strftime("%d/%m/%Y"),
                "Số năm hoạt động": years_active,
                "Kết quả kiểm tra": "Không đạt",
                "Lý do": reason,
                "Lịch sử niêm yết": history_text
            })
    
    return result

def listed_for_over_5_years(df):
    """
    Kiểm tra danh sách cổ phiếu dựa trên tiêu chí số năm hoạt động >= 5 năm trên HOSE.
    """
    result = []
    current_date = datetime.today()
    
    for _, row in df.iterrows():
        ma_co_phieu = row["ticker"]  # Mã chứng khoán
        history_text = row["history_dev"]  # Lịch sử niêm yết/giao dịch
        
        if pd.isna(history_text) or not isinstance(history_text, str):
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Kết quả kiểm tra": "Không đạt",
                "Lý do": "Không có dữ liệu",
                "Lịch sử niêm yết": history_text
            })
            continue
        
        dates = extract_relevant_dates(history_text)
        
        # Chọn ngày giao dịch cuối cùng nếu có, nếu không lấy ngày niêm yết
        last_date = max(dates['giao dịch']) if dates['giao dịch'] else (
            max(dates['niêm yết']) if dates['niêm yết'] else None)
        
        if not last_date:
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Kết quả kiểm tra": "Không đạt",
                "Lý do": "Không tìm thấy ngày niêm yết hoặc giao dịch",
                "Lịch sử niêm yết": history_text
            })
            continue
        
        # Tính số năm hoạt động dựa trên ngày giao dịch cuối cùng
        years_active = round((current_date - last_date).days / 365, 2)
        
        text_lower = history_text.lower()
        if years_active >= 5 and any(x in text_lower for x in ['hose', 'sở giao dịch chứng khoán thành phố hồ chí minh',
                                                               'sở giao dịch chứng khoán tp. Hồ Chí Minh',
                                                               'sở giao dịch chứng khoán tp hcm', 'ttgd ck tp.hcm',
                                                               'trung tâm giao dịch chứng khoán thành phố hồ chí minh',
                                                               'sàn giao dịch chứng khoán thành phố hồ chí minh']):
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Ngày giao dịch cuối cùng": last_date.strftime("%d/%m/%Y"),
                "Số năm hoạt động": years_active,
                "Kết quả kiểm tra": "Đạt",
                "Lý do": "Đủ điều kiện (>=5 năm + HOSE)",
                "Lịch sử niêm yết": history_text
            })
        else:
            reason = "Không có HOSE" if years_active >= 5 else "Thời gian hoạt động < 5 năm"
            result.append({
                "Mã cổ phiếu": ma_co_phieu,
                "Ngày giao dịch cuối cùng": last_date.strftime("%d/%m/%Y"),
                "Số năm hoạt động": years_active,
                "Kết quả kiểm tra": "Không đạt",
                "Lý do": reason,
                "Lịch sử niêm yết": history_text
            })
    
    return result

def filter_last_5_years(df):
    latest_year = df['Năm'].max()
    return df[df['Năm'] >= latest_year - 4]

## Tiêu chí 2
def positive_net_profit(df):
    invalid_cp = df[df['Lợi nhuận thuần'] < 0]['CP'].unique()
    return df[~df['CP'].isin(invalid_cp)]

## Tiêu chí 3 và 4
def is_positive_continuous(series):
    series = series.dropna()
    return (series > 0).all()

def positive_revenue_growth(group):
    group['revenue_growth']=group.groupby('CP')['Doanh thu (Tỷ đồng)'].pct_change()
    return is_positive_continuous(group['revenue_growth'])

def positive_profit_growth(group):
    group['profit_growth']=group.groupby('CP')['Lợi nhuận thuần'].pct_change()
    return is_positive_continuous(group['profit_growth'])

# ========================= Streamlit App =========================

st.set_page_config(page_title="Lọc cổ phiếu giá trị", page_icon="📊")
st.title("📊 Ứng dụng Lọc Cổ Phiếu Giá Trị")

file_financial_statement = st.file_uploader("Tải dữ liệu báo cáo tài chính (Excel)", type="xlsx")
file_profile = st.file_uploader("Tải dữ liệu thông tin công ty (.CSV)", type="csv")

if (file_financial_statement is not None) & (file_profile is not None):

    options = st.multiselect("Chọn tiêu chí lọc:", [
        "Niêm yết trên 5 năm",
        "Lợi nhuận sau thuế dương 5 năm liên tục",
        "Tăng trưởng doanh thu dương 5 năm",
        "Tăng trưởng lợi nhuận dương 5 năm"
    ])

    if st.button("Lọc cổ phiếu"):
        income_statement = pd.read_excel(file_financial_statement,sheet_name="income_statement")
        event=pd.read_csv(file_profile)

        income_statement=income_statement[income_statement['Năm']>=2019]
        income_statement = income_statement.sort_values(['CP', 'Năm'])

        selected_stocks = income_statement.CP.unique()
        
        if "Niêm yết trên 5 năm" in options:
            results_option_1 = listed_for_over_5_years(event)
            results_option_1 = pd.DataFrame(results_option_1)
            results_option_1=results_option_1[results_option_1['Kết quả kiểm tra']=="Đạt"]
            stock_option_1=results_option_1['Mã cổ phiếu'].unique()
            selected_stocks=np.intersect1d(selected_stocks,stock_option_1)
        if "Lợi nhuận sau thuế dương 5 năm liên tục" in options:
            result_option_2 = positive_net_profit(income_statement)
            stock_option_2=result_option_2.CP.unique()
            selected_stocks=np.intersect1d(selected_stocks,stock_option_2)
        if "Tăng trưởng doanh thu dương 5 năm" in options:
            result_option_3 = income_statement.groupby('CP').filter(positive_revenue_growth)
            stock_option_3=result_option_3.CP.unique()
            selected_stocks=np.intersect1d(selected_stocks,stock_option_3)
        if "Tăng trưởng lợi nhuận dương 5 năm" in options:
            result_option_4 = income_statement.groupby('CP').filter(positive_profit_growth)
            stock_option_4=result_option_4.CP.unique()
            selected_stocks=np.intersect1d(selected_stocks,stock_option_4)

        st.write("### Danh sách mã cổ phiếu đã lọc:")
        st.write(list(selected_stocks) if selected_stocks.size !=0 else "Không có mã cổ phiếu nào thỏa mãn tất cả tiêu chí đã chọn.")

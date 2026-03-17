# 📊 Value Stock Screener (Prototype)

## 📌 Overview
This is a lightweight, rapid-prototype Streamlit application designed for quick stock screening based on fundamental value investing criteria. It processes uploaded financial statements and company profile data to filter out stocks that do not meet strict growth, profitability, and listing longevity thresholds on the Vietnamese stock market (specifically HOSE).

## ✨ Features
Users can dynamically select multiple filtering criteria via the UI:
* **Longevity (Listed > 5 Years):** Uses Regex to parse unstructured historical text data and ensure the stock has been trading on HOSE for at least 5 years.
* **Positive Net Profit:** Filters out companies that recorded any negative net profit over the evaluated period.
* **Consistent Revenue Growth:** Ensures Year-over-Year (YoY) revenue growth is strictly positive.
* **Consistent Profit Growth:** Ensures YoY net profit growth is strictly positive.

## 📁 Required Data Format
As a basic prototype, the script relies on hardcoded column names. The application will crash if the uploaded files do not strictly match the following structures:

**1. Financial Statement (`.xlsx`)**
* Must contain a sheet explicitly named `income_statement`.
* Required columns:
  * `CP`: Stock Ticker.
  * `Năm`: Year.
  * `Lợi nhuận thuần`: Net Profit.
  * `Doanh thu (Tỷ đồng)`: Revenue.

**2. Company Profile (`.csv`)**
* Required columns:
  * `ticker`: Stock Ticker.
  * `history_dev`: A text block containing the company's listing history (used to extract dates via regex).

## ⚙️ How to Run Locally
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```
2. Execute the Streamlit app:
```bash
streamlit run app.py
```

## ⚠️ Known Limitations
* **Fragile Text Parsing:** The listing date extraction (`extract_relevant_dates`) relies heavily on specific keywords ('hose', 'sở giao dịch') and date formats in the `history_dev` column. Unconventional text formatting will result in missing data.
* **Zero Error Handling:** The app lacks UI warnings for incorrect file formats, missing columns, or division-by-zero errors during percentage change calculations.
* **Hardcoded Logic:** Data is forcefully filtered to include only records from 2019 onwards.

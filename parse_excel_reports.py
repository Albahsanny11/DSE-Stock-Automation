import os
import pandas as pd
from datetime import datetime

REPORTS_DIR = "reports/Solomon"  # Or wherever you saved them
OUTPUT_CSV = "solomon_market_data.csv"

def parse_excel_file(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
        df.columns = df.columns.str.strip()

        # Attempt to standardize based on common headers
        required_cols = ['Security', 'Closing Price', 'Volume', 'Change %']
        found_cols = [col for col in df.columns if any(key in col for key in required_cols)]

        if len(found_cols) < 3:
            print(f"Skipping file: {file_path} — Columns not matched")
            return pd.DataFrame()

        df = df[found_cols].copy()
        df.columns = ['Security', 'Closing Price', 'Volume', 'Change %'][:len(found_cols)]
        df['Date'] = extract_date_from_filename(file_path)
        df['Source'] = 'Solomon'

        return df
    except Exception as e:
        print(f"❌ Failed to parse {file_path}: {e}")
        return pd.DataFrame()

def extract_date_from_filename(filename):
    base = os.path.basename(filename)
    try:
        parts = base.split("_")
        date_str = parts[0]
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return datetime.today().date()

def parse_all_reports():
    all_data = []
    for root, dirs, files in os.walk(REPORTS_DIR):
        for file in files:
            if file.endswith(".xls") or file.endswith(".xlsx"):
                path = os.path.join(root, file)
                df = parse_excel_file(path)
                if not df.empty:
                    all_data.append(df)
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(OUTPUT_CSV, index=False)
        print(f"✅ Parsed data saved to: {OUTPUT_CSV}")
    else:
        print("⚠️ No valid Excel files parsed.")

if __name__ == "__main__":
    parse_all_reports()

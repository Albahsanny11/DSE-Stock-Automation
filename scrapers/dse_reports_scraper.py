import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import urllib3
import pdfplumber
import re
import csv
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
BASE_URL = "https://www.dse.co.tz"
REPORTS_URL = "https://www.dse.co.tz/market-reports"
DOWNLOAD_DIR = os.path.join("reports", "DSE")
CSV_OUTPUT = os.path.join(DOWNLOAD_DIR, "financial_metrics.csv")

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_report_links():
    response = requests.get(REPORTS_URL, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')

    report_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if any(ext in href for ext in ['.pdf', '.xls', '.xlsx']):
            full_url = urljoin(BASE_URL, href)
            report_links.append(full_url)
    return report_links

def download_reports(report_links):
    downloaded_files = []
    for url in report_links:
        filename = url.split("/")[-1]
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        save_path = os.path.join(DOWNLOAD_DIR, f"{date_prefix}_{filename}")

        if not os.path.exists(save_path):
            print(f"Downloading: {filename}")
            r = requests.get(url)
            with open(save_path, "wb") as f:
                f.write(r.content)
            downloaded_files.append(save_path)
        else:
            print(f"Already downloaded: {filename}")
            downloaded_files.append(save_path)
    return downloaded_files

def extract_financial_metrics_pdf(pdf_path):
    metrics = {
        "filename": os.path.basename(pdf_path),
        "Revenue": None,
        "Net Profit": None,
        "EPS": None
    }

    keywords = {
        "Revenue": re.compile(r"Revenue", re.I),
        "Net Profit": re.compile(r"Net\s*Profit", re.I),
        "EPS": re.compile(r"Earnings\s*Per\s*Share|EPS", re.I)
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                for line in lines:
                    for key, pattern in keywords.items():
                        if metrics[key] is None and pattern.search(line):
                            numbers = re.findall(r"[\d,]+(?:\.\d+)?", line.replace(',', ''))
                            if numbers:
                                metrics[key] = numbers[0]
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

    return metrics

def extract_financial_metrics_excel(excel_path):
    metrics = {
        "filename": os.path.basename(excel_path),
        "Revenue": None,
        "Net Profit": None,
        "EPS": None
    }

    keywords = {
        "Revenue": re.compile(r"Revenue", re.I),
        "Net Profit": re.compile(r"Net\s*Profit", re.I),
        "EPS": re.compile(r"Earnings\s*Per\s*Share|EPS", re.I)
    }

    try:
        xls = pd.ExcelFile(excel_path)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
            # Flatten dataframe to 1D list of strings for search
            values = df.fillna('').astype(str).values.flatten()
            for val in values:
                for key, pattern in keywords.items():
                    if metrics[key] is None and pattern.search(val):
                        # Try to find number near the keyword (in the dataframe)
                        # Look in the same row for numbers
                        row_idx = df.apply(lambda row: row.astype(str).str.contains(val, case=False, regex=False)).any(axis=1)
                        if row_idx.any():
                            row = df.loc[row_idx].astype(str)
                            nums = row.apply(lambda x: x.str.extract(r'([\d,.]+)').dropna(), axis=1)
                            nums = pd.concat(nums.values)
                            if not nums.empty:
                                number = nums.iloc[0, 0].replace(',', '')
                                metrics[key] = number
    except Exception as e:
        print(f"Error processing {excel_path}: {e}")

    return metrics

def save_metrics_to_csv(metrics_list, csv_path=CSV_OUTPUT):
    keys = ["filename", "Revenue", "Net Profit", "EPS"]
    with open(csv_path, "w", newline="", encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for data in metrics_list:
            writer.writerow(data)

import time
import schedule

def job():
    print("Running scheduled scraper job...")
    links = fetch_report_links()
    downloaded_files = download_reports(links)

    all_metrics = []

    for fpath in downloaded_files:
        if fpath.lower().endswith(".pdf"):
            metrics = extract_financial_metrics_pdf(fpath)
            all_metrics.append(metrics)
        elif fpath.lower().endswith((".xls", ".xlsx")):
            metrics = extract_financial_metrics_excel(fpath)
            all_metrics.append(metrics)

    save_metrics_to_csv(all_metrics)
    print(f"✅ Done! Financial metrics saved to {CSV_OUTPUT}")

# Schedule job every day at 7:00 am
schedule.every().day.at("07:00").do(job)

print("Scheduler started. Waiting for jobs...")
while True:
    schedule.run_pending()
    time.sleep(60)

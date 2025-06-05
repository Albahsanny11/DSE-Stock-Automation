import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Target URLs
BASE_URL = "https://www.dse.co.tz"
REPORTS_URL_DSE = "https://www.dse.co.tz/market-reports"
REPORTS_URL_SOLOMON = "https://solomon.co.tz/market_reports"
DOWNLOAD_DIR = os.path.join("reports", "DSE_and_Solomon")

# Make sure the folder exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_report_links(url, base_url):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Look for all download links (PDFs, Excel, etc.)
    report_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if any(ext in href for ext in ['.pdf', '.xls', '.xlsx']):
            full_url = urljoin(base_url, href)
            report_links.append(full_url)
    return report_links

def download_reports(report_links):
    for url in report_links:
        filename = url.split("/")[-1]
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        save_path = os.path.join(DOWNLOAD_DIR, f"{date_prefix}_{filename}")

        if not os.path.exists(save_path):  # avoid re-downloading
            print(f"Downloading: {filename}")
            r = requests.get(url)
            with open(save_path, "wb") as f:
                f.write(r.content)
        else:
            print(f"Already downloaded: {filename}")

if __name__ == "__main__":
    # Fetch and download DSE reports
    print("Fetching DSE reports...")
    dse_links = fetch_report_links(REPORTS_URL_DSE, BASE_URL)
    download_reports(dse_links)
    print("✅ Finished downloading DSE market reports.")

    # Fetch and download Solomon Stockbrokers reports
    print("Fetching Solomon Stockbrokers reports...")
    solomon_links = fetch_report_links(REPORTS_URL_SOLOMON, BASE_URL)
    download_reports(solomon_links)
    print("✅ Finished downloading Solomon Stockbrokers reports.")

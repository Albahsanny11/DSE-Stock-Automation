import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# CONFIGURATION
SHEET_NAME = "DSE Trends"
GMAIL_TO = "albahsanny@gmail.com" 
DATE = datetime.today().strftime("%Y-%m-%d")

# GOOGLE SHEETS AUTH
creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
gc = gspread.authorize(creds)

try:
    sheet = gc.open(SHEET_NAME).sheet1
except gspread.SpreadsheetNotFound:
    sh = gc.create(SHEET_NAME)
    sh.share(GMAIL_TO, perm_type='user', role='writer')
    sheet = sh.sheet1

# SCRAPE DSE DATA
url = "https://www.dse.co.tz/"
res = requests.get(url, verify=False)
tables = pd.read_html(res.text)
data = tables[3]  # Adjust as needed

data = data[["Symbol", "Close", "Change"]]
data.rename(columns={"Symbol": "Security", "Close": "Closing Price"}, inplace=True)
data = data.dropna(subset=["Security", "Closing Price"])

def clean_percent(val):
    try:
        val = re.sub(r"[^\d.\-]+", "", str(val))
        return float(val) if val else 0.0
    except:
        return 0.0

data["Change (%)"] = data["Change"].apply(clean_percent)
data["Trend"] = data["Change (%)"].apply(lambda x: "UP \U0001F4C8" if x > 0 else "DOWN \U0001F4C9" if x < 0 else "FLAT")

# APPEND TO SHEET
for _, row in data.iterrows():
    sheet.append_row([DATE, row["Security"], row["Closing Price"], row["Change (%)"], row["Trend"]])

# SEND EMAIL SUMMARY
summary = "\n".join([f"{row['Security']}: {row['Closing Price']} TZS ({row['Trend']})" for _, row in data.iterrows()])
body = f"DSE Trends for {DATE}:\n\n{summary}"
msg = MIMEText(body)
msg["Subject"] = f"DSE Market Summary - {DATE}"
msg["From"] = GMAIL_TO
msg["To"] = GMAIL_TO

app_password = os.environ.get("GMAIL_APP_PASSWORD")
if not app_password:
    raise Exception("Missing GMAIL_APP_PASSWORD environment variable")

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    print(f"📧 Logging in as {GMAIL_TO} with app password loaded: {'Yes' if app_password else 'No'}")
    smtp.login(GMAIL_TO, app_password)
    smtp.send_message(msg)

print(f"✅ Email sent to {GMAIL_TO}")

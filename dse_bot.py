import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from predict_stock import predict_trend
import joblib
from predict_stock import predict_trend
AI_ENABLED = False  # Default to false if imports fail
try:
    import joblib
    from predict_stock import predict_trend
    AI_ENABLED = True
except ImportError as import_err:  # Fixed syntax here
    print(f"⚠️ AI dependencies not available: {import_err}")

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

data = data[["Symbol", "Close", "Change"]].copy()
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

def recommend_action(change):
    if change > 3:
        return "BUY 🟢"
    elif change < -2:
        return "SELL 🔴"
    else:
        return "HOLD ⚪"

data["Action"] = data["Change (%)"].apply(recommend_action)

def assess_risk(change):
    if abs(change) > 5:
        return "HIGH ⚠️"
    elif abs(change) > 2:
        return "MEDIUM ⚠"
    else:
        return "LOW ✅"

def system_checks():
    import sys
    print(f"Python version: {sys.version}")
    print(f"Pandas version: {pd.__version__}")
    try:
        import sklearn
        print(f"Scikit-learn version: {sklearn.__version__}")
    except ImportError:
        print("Scikit-learn not installed")

def backtest_model():
    from predict_stock import train_model
    train_model(['CRDB', 'NMB', 'TBL'], backtest=True)

def generate_charts():
    import matplotlib.pyplot as plt
    data[['Closing Price', 'Change (%)']].plot()
    plt.savefig('trends.png')
    # Add to email as attachment



# AI PREDICTIONS - Add this after your data scraping section
if AI_ENABLED:
    try:
        model = joblib.load('dse_model.joblib')
        
        def get_prediction(symbol):
            try:
                result = predict_trend(symbol, model)
                return {
                    'prediction': result['prediction'] if result else 'N/A',
                    'confidence': result['confidence'] if result else 0
                }
            except Exception as e:
                print(f"Prediction failed for {symbol}: {str(e)}")
                return {'prediction': 'N/A', 'confidence': 0}
        
        predictions = data['Security'].apply(get_prediction)
        data['AI Prediction'] = predictions.apply(lambda x: x['prediction'])
        data['Confidence'] = predictions.apply(lambda x: x['confidence'])
        
    except Exception as e:
        print(f"⚠️ AI Prediction system failed: {str(e)}")
        data['AI Prediction'] = 'N/A'
        data['Confidence'] = 0
else:
    data['AI Prediction'] = 'N/A'
    data['Confidence'] = 0
    
# APPEND TO SHEET
if not sheet.get_all_values():
    sheet.append_row(["Date", "Security", "Closing Price", "Change (%)", "Trend", "Action"])

for _, row in data.iterrows():
    sheet.append_row([DATE, row["Security"], row["Closing Price"], row["Change (%)"], row["Trend"], row["Action"]])

if "Risk" not in data.columns:
    data["Risk"] = "N/A"
# SEND EMAIL SUMMARY
summary = "\n".join([
    f"{row['Security']}: {row['Closing Price']} TZS ({row['Trend']}) → {row['Action']} | Risk: {row['Risk']}"
    for _, row in data.iterrows()
])
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

print("📊 Columns in data:", data.columns.tolist())
print("🧪 Preview row:", data.head(1).to_dict())
print(f"✅ Email sent to {GMAIL_TO}")
# -------------------------
# TELEGRAM MESSAGE
if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"DSE Alert - {DATE}\n\n{summary}",
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        # Add timeout and better error handling
        response = requests.post(telegram_url, json=payload, timeout=10)
        response.raise_for_status()  # Raises exception for 4XX/5XX
        
        print(f"✅ Telegram alert sent. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Response content: {e.response.text}")
else:
    print("⚠️ Telegram credentials missing. Required env vars:")
    print("- TELEGRAM_BOT_TOKEN")
    print("- TELEGRAM_CHAT_ID")

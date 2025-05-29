try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    import yfinance as yf
    import pandas as pd
    import joblib
    from datetime import datetime, timedelta
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install required packages:")
    print("pip install scikit-learn yfinance pandas joblib")
    exit(1)

# Configuration
MODEL_FILE = 'dse_model.joblib'
LOOKBACK_DAYS = 90
SYMBOLS = ['CRDB', 'NMB', 'TBL']  # Add more DSE symbols

def ensure_dependencies():
    """Verify all packages are available"""
    try:
        import sklearn
        import yfinance
        return True
    except ImportError:
        return False

def fetch_historical_data(symbol):
    """Get stock data with error handling"""
    try:
        stock = yf.Ticker(f"{symbol}.DS")
        hist = stock.history(
            period=f"{LOOKBACK_DAYS}d",
            interval="1d"
        )
        return hist.dropna()
    except Exception as e:
        print(f"Failed to fetch {symbol}: {e}")
        return None

def main():
    if not ensure_dependencies():
        print("❌ Missing required packages")
        exit(1)
    
    print("✅ All dependencies available")
    
    # Train or load model
    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
        print("Loaded existing model")
    else:
        print("Training new model...")
        model = RandomForestClassifier(n_estimators=100)
        # Add your training logic here
        joblib.dump(model, MODEL_FILE)
    
    # Example prediction
    for symbol in SYMBOLS:
        data = fetch_historical_data(symbol)
        if data is not None:
            print(f"{symbol}: Last close {data['Close'][-1]:.2f}")

if __name__ == "__main__":
    main()

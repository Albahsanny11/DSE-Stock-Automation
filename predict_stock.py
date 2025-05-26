import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import yfinance as yf
from datetime import datetime, timedelta

# Configuration
MODEL_FILE = 'dse_model.joblib'
LOOKBACK_DAYS = 90

def fetch_historical_data(symbol, days=LOOKBACK_DAYS):
    """Fetch historical stock data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        stock = yf.Ticker(f"{symbol}.DS")
        hist = stock.history(start=start_date, end=end_date)
        return hist
    except:
        print(f"Failed to fetch data for {symbol}")
        return None

def prepare_features(data):
    """Create technical indicators as features"""
    if data is None or len(data) < 5:
        return None
        
    # Simple moving averages
    data['SMA_5'] = data['Close'].rolling(window=5).mean()
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Target variable (1 if next day's close is higher)
    data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
    
    return data.dropna()

def train_model(symbols):
    """Train model on multiple stocks"""
    all_data = []
    
    for symbol in symbols:
        data = fetch_historical_data(symbol)
        if data is not None:
            prepared = prepare_features(data)
            if prepared is not None:
                prepared['Symbol'] = symbol
                all_data.append(prepared)
    
    if not all_data:
        return None
    
    combined = pd.concat(all_data)
    X = combined[['SMA_5', 'SMA_20', 'RSI']]
    y = combined['Target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    print(f"Model accuracy: {accuracy_score(y_test, preds):.2f}")
    
    joblib.dump(model, MODEL_FILE)
    return model

def predict_trend(symbol, model):
    """Predict next day trend for a stock"""
    data = fetch_historical_data(symbol)
    if data is None:
        return None
        
    features = prepare_features(data)
    if features is None or len(features) == 0:
        return None
    
    latest = features.iloc[-1][['SMA_5', 'SMA_20', 'RSI']].values.reshape(1, -1)
    prediction = model.predict(latest)[0]
    probability = model.predict_proba(latest)[0][1]
    
    return {
        'symbol': symbol,
        'prediction': 'UP' if prediction else 'DOWN',
        'confidence': float(probability),
        'last_close': float(data.iloc[-1]['Close'])
    }

if __name__ == "__main__":
    # Example usage
    symbols = ['CRDB', 'NMB', 'TBL']  # Add more DSE symbols
    model = train_model(symbols)
    
    if model:
        for symbol in symbols:
            prediction = predict_trend(symbol, model)
            if prediction:
                print(f"{symbol}: {prediction['prediction']} (Confidence: {prediction['confidence']:.2%})")

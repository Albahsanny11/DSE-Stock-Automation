import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import joblib

# Load latest data
df = pd.read_csv('data/dse_data.csv')
scaler = joblib.load('models/scaler.save')
model = load_model('models/lstm_model.h5')

# Prepare input
df = df.tail(10)
input_data = scaler.transform(df[['Close']])
X_input = np.array([input_data])
X_input = X_input.reshape((1, 10, 1))

# Predict
pred = model.predict(X_input)
predicted_price = scaler.inverse_transform(pred)[0][0]

print(f"🔮 Predicted next Close: {predicted_price:.2f}")

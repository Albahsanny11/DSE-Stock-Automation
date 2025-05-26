import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import joblib

# Load data
df = pd.read_csv('data/dse_data.csv')  # use your actual file path
df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
df.dropna(inplace=True)

# Normalize data
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df[['Close']].values)

# Prepare sequences
X, y = [], []
look_back = 10
for i in range(look_back, len(scaled_data)):
    X.append(scaled_data[i-look_back:i])
    y.append(scaled_data[i])

X, y = np.array(X), np.array(y)

# Build LSTM
model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)),
    LSTM(50),
    Dense(1)
])
model.compile(optimizer='adam', loss='mean_squared_error')

# Train
model.fit(X, y, epochs=10, batch_size=16)

# Save model and scaler
model.save('models/lstm_model.h5')
joblib.dump(scaler, 'models/scaler.save')

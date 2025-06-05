import pandas as pd

def merge_datasets(solomon_csv, dse_csv, output_csv="merged_market_data.csv"):
    df_solomon = pd.read_csv(solomon_csv)
    df_dse = pd.read_csv(dse_csv)

    # Ensure common column names
    df_solomon.rename(columns={
        "Change %": "Change",
        "Volume": "Volume"
    }, inplace=True)

    # Add missing columns to match
    for col in ["Trend", "Risk", "Action"]:
        if col not in df_solomon.columns:
            df_solomon[col] = None

    for col in ["Volume"]:
        if col not in df_dse.columns:
            df_dse[col] = None

    combined_df = pd.concat([df_solomon, df_dse], ignore_index=True)
    combined_df.sort_values(by=["Security", "Date"], inplace=True)
    combined_df.to_csv(output_csv, index=False)
    print(f"✅ Combined dataset saved to: {output_csv}")

if __name__ == "__main__":
    merge_datasets("solomon_market_data.csv", "dse_live_data.csv")

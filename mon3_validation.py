
import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog
import random
from datetime import datetime

root = tk.Tk()
root.withdraw()
csv_file_path = filedialog.askopenfilename(title="Select the timestamps CSV file", filetypes=[("CSV files", "*.csv")])

if csv_file_path:
    df = pd.read_csv(csv_file_path, dtype={'Date (YYYY-MM-DD)': str, 'Time (HH:MM)': str})
    print("Loaded timestamps:")
    print(df)

    df['Time (HH:MM)'] = pd.to_datetime(df['Time (HH:MM)'], format='%H:%M').dt.time

    # separate into nighttime (18:00 - 07:00 next day) and daytime (07:00 - 18:00) (specific to MON3)
    nighttime_df = df[(df['Time (HH:MM)'] >= pd.to_datetime('18:00', format='%H:%M').time()) | 
                      (df['Time (HH:MM)'] < pd.to_datetime('07:00', format='%H:%M').time())]
    daytime_df = df[(df['Time (HH:MM)'] >= pd.to_datetime('07:00', format='%H:%M').time()) & 
                    (df['Time (HH:MM)'] < pd.to_datetime('18:00', format='%H:%M').time())]

    total_sample_size = int(len(df) * 0.1)
    nighttime_sample_size = int(total_sample_size * 0.9)
    daytime_sample_size = total_sample_size - nighttime_sample_size

    # strat sampling by date for nighttime and daytime
    def stratified_sample(df, sample_size):
        grouped = df.groupby('Date (YYYY-MM-DD)')
        per_group_sample = max(1, sample_size // len(grouped))
        sampled_df = grouped.apply(lambda x: x.sample(min(len(x), per_group_sample), random_state=42)).reset_index(drop=True)
        # sampled dataframe is smaller than the desired sample size, perform additional random sampling with replacement (specific to MON3)
        if len(sampled_df) < sample_size:
            additional_sample = df.sample(n=sample_size - len(sampled_df), random_state=42, replace=True)
            sampled_df = pd.concat([sampled_df, additional_sample]).reset_index(drop=True)
        return sampled_df

    nighttime_sample = stratified_sample(nighttime_df, nighttime_sample_size)
    daytime_sample = stratified_sample(daytime_df, daytime_sample_size)

    combined_sample = pd.concat([nighttime_sample, daytime_sample]).sort_values(by=['Date (YYYY-MM-DD)', 'Time (HH:MM)']).reset_index(drop=True)

    current_date_str = datetime.now().strftime('%Y%m%d_%H%M')
    output_sample_path = os.path.join(os.path.dirname(csv_file_path), f"timestamp_subset_{current_date_str}.csv")
    combined_sample.to_csv(output_sample_path, index=False, date_format='%Y-%m-%d', columns=['Date (YYYY-MM-DD)', 'Time (HH:MM)'])
    print(f"Subset of all timestamps saved to {output_sample_path}")
else:
    print("No CSV file selected.")
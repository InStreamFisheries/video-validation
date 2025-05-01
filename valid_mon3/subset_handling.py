import pandas as pd
import csv
import os
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
from io import StringIO
from datetime import datetime

def sample_csv_subset():
    root = tk.Tk()
    root.withdraw()

    input_path = filedialog.askopenfilename(
        title="Select your CSV file (tab- or comma-separated)",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not input_path or not os.path.isfile(input_path):
        print("Invalid file path.")
        return
    
    try:
        sample_percent = float(input("Enter the percentage of footage to sample (e.g., 5 for 5%): ").strip())
        if not (0.1 <= sample_percent <= 100):
            print("Please enter a percentage between 0.1 and 100.")
            return
    except ValueError:
        print("Invalid percentage input.")
        return

    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log(f"[{timestamp}] Starting CSV sampling...")
    log(f"Input file: {input_path}")
    log(f"Sampling percentage: {sample_percent}%")

    try:
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        data_lines = [line for line in lines if not line.startswith("#")]
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(data_lines[0])
        delimiter = dialect.delimiter
        log(f"Detected delimiter: '{delimiter}'")

        content = ''.join(data_lines)
        df = pd.read_csv(StringIO(content), delimiter=delimiter, dtype=str)
    except Exception as e:
        log(f"Error reading CSV: {e}")
        write_log_file(input_path, log_lines, timestamp)
        return

    required_columns = ["Date (YYYY-MM-DD)", "Time (HH:MM:SS)", "Filename"]
    if not all(col in df.columns for col in required_columns):
        log(f"CSV must contain columns: {', '.join(required_columns)}")
        log(f"Detected columns: {df.columns.tolist()}")
        write_log_file(input_path, log_lines, timestamp)
        return

    if df.empty:
        log("The input CSV is empty.")
        write_log_file(input_path, log_lines, timestamp)
        return

    sample_size = max(1, int((sample_percent / 100.0) * len(df)))
    log(f"Total rows: {len(df)} | Sampling {sample_size} rows")
    sampled_df = df.sample(n=sample_size, random_state=42)

    input_basename = os.path.splitext(os.path.basename(input_path))[0]
    input_dir = os.path.dirname(input_path)
    output_filename = f"{input_basename}_sample_{int(sample_percent)}pct_{timestamp}.csv"
    output_path = os.path.join(input_dir, output_filename)

    log(f"Saving sampled CSV to: {output_path}")
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=sampled_df.columns, delimiter=delimiter)
            writer.writeheader()
            for i in tqdm(range(len(sampled_df)), desc="Writing rows", unit="row"):
                writer.writerow(sampled_df.iloc[i].to_dict())
    except Exception as e:
        log(f"Error writing CSV: {e}")
        write_log_file(output_path, log_lines, timestamp)
        return

    log(f"Sampled CSV saved: {output_path}")
    write_log_file(output_path, log_lines, timestamp)
    log(f"Log saved: {os.path.splitext(output_path)[0]}.log")

def write_log_file(base_path, log_lines, timestamp):
    log_path = os.path.splitext(base_path)[0] + ".log"
    with open(log_path, 'w', encoding='utf-8') as f_log:
        for line in log_lines:
            f_log.write(line + "\n")

if __name__ == "__main__":
    sample_csv_subset()

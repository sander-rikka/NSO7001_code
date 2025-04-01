"""File to unzip the radar raw data.
Author: Yee Chun Tsoi
Modified by: Sander Rikka"""
import os
import zipfile
from datetime import datetime, timedelta
from joblib import Parallel, delayed
import pandas as pd


# ----------------------------
# Configuration
# ----------------------------
ZIP_DIR = "data/radar_raw"
OUTPUT_DIR = "data/radar_unzipped"
MISSING_CSV_PATH = "data/missing_data_final.csv"

START_TIME = datetime(2023, 11, 9, 2, 0)
END_TIME = datetime(2023, 11, 9, 7, 59)
TIME_INTERVAL = timedelta(minutes=5)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------
# Helpers
# ----------------------------
def extract_zip_file(zip_filename):
    extracted_files = set()
    zip_path = os.path.join(ZIP_DIR, zip_filename)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                target_path = os.path.join(OUTPUT_DIR, file)
                if not os.path.exists(target_path):
                    zip_ref.extract(file, OUTPUT_DIR)
                extracted_files.add(file)
    except zipfile.BadZipFile:
        print(f"Invalid ZIP file: {zip_filename}")
    return extracted_files


def extract_all_zips():
    zip_files = sorted(f for f in os.listdir(ZIP_DIR) if f.endswith(".zip"))
    results = Parallel(n_jobs=-1)(delayed(extract_zip_file)(f) for f in zip_files)
    all_extracted = set().union(*results)
    return all_extracted


def generate_expected_timestamps():
    timestamps = []
    current = START_TIME
    while current <= END_TIME:
        timestamps.append(current.strftime("%Y-%m-%dT%H:%M"))
        current += TIME_INTERVAL
    return timestamps


def extract_timestamps_from_files(file_list):
    timestamps = set()
    for file in file_list:
        try:
            ts_str = file[4:16]  # Assuming timestamp is in this position
            ts = datetime.strptime(ts_str, "%Y%m%d%H%M")
            timestamps.add(ts.strftime("%Y-%m-%dT%H:%M"))
        except Exception:
            print(f"Failed to extract timestamp from filename: {file}")
    return timestamps


# ----------------------------
# Main Execution
# ----------------------------
if __name__ == "__main__":
    print("Extracting ZIP files...")
    extracted_files = os.listdir(OUTPUT_DIR) or extract_all_zips()

    print("Extracting timestamps from files...")
    actual_timestamps = extract_timestamps_from_files(extracted_files)

    print("Generating expected timestamps...")
    expected_timestamps = generate_expected_timestamps()

    print("Comparing and writing results...")
    status = [
        {"Timestamp": ts, "Available": ts in actual_timestamps}
        for ts in expected_timestamps
    ]
    df = pd.DataFrame(status)
    df.to_csv(MISSING_CSV_PATH, index=False)

    print(f"Done. Missing data written to: {MISSING_CSV_PATH}")

"""
Author: Yee Chun Tsoi, Department of Marine Systems
Modified by: Sander Rikka, Department of Marine Systems
"""
import os
import datetime
import numpy as np
import xradar as xd
import wradlib as wrl
from joblib import Parallel, delayed
from scipy.ndimage import median_filter, label


def reflectivity_to_rainfall(reflectivity, a=300, b=1.5):
    # Convert reflectivity (dBZ) to rainfall intensity (mm/h)
    Z = 10 ** (reflectivity / 10)
    return (Z / a) ** (1 / b)


def clean_radar_reflectivity_by_azimuth_aggressive(dbzh, window, threshold, background_cutoff, fill_value, min_area):
    # Detect and replace outlier rows based on azimuthal profiles
    row_medians = np.percentile(dbzh, 95, axis=1)
    row_medians[row_medians < 0] = 0
    neighbor_medians = median_filter(row_medians, size=window, mode='reflect')
    outlier_rows = np.abs(row_medians - neighbor_medians) > threshold

    local_median_image = median_filter(dbzh, size=(window, window), mode='reflect')
    new_dbzh = dbzh.copy()
    for i in range(dbzh.shape[0]):
        if outlier_rows[i]:
            new_dbzh[i, :] = local_median_image[i, :]

    # Apply background cutoff
    new_dbzh[new_dbzh < background_cutoff] = fill_value

    # Remove small speckles and isolated regions
    valid_mask = ~np.isnan(new_dbzh)
    labeled, num_features = label(valid_mask)
    for region in range(1, num_features + 1):
        region_mask = (labeled == region)
        area = np.sum(region_mask)
        if area <= min_area:
            new_dbzh[region_mask] = np.nan

    new_dbzh = wrl.util.despeckle(new_dbzh, n=5)
    return new_dbzh


def save_radar_metadata(directory, sweep_0, radar_data):
    # Save range, azimuth, and radar metadata to disk
    np.save(os.path.join(directory, "ranges.npy"), sweep_0["range"].values)
    np.save(os.path.join(directory, "azimuths.npy"), sweep_0["azimuth"].values)
    np.save(os.path.join(directory, "radar_metadata.npy"), np.array([
        radar_data["/radar_parameters"]["latitude"].values,
        radar_data["/radar_parameters"]["longitude"].values,
        radar_data["/radar_parameters"]["altitude"].values
    ]))


def process_radar_file(file, rainfall_intensities_dir):
    # Process a single radar file and compute rainfall intensity
    try:
        radar_data = xd.io.open_odim_datatree(file)
    except Exception as e:
        print(f"Failed to open: {file} with error: {e}")
        return

    filename = os.path.basename(file)
    timestamp = filename.split(".")[1]
    output_file = os.path.join(rainfall_intensities_dir, f"rainfall_{timestamp}.npy")

    if os.path.exists(output_file):
        print(f"Skipping existing file: {output_file}")
        return

    sweep_0 = radar_data["/sweep_0"]
    reflectivity = sweep_0["DBZH"].values

    if reflectivity.shape != (360, 833):
        return

    # Clean reflectivity and convert to rainfall
    reflectivity_filtered = clean_radar_reflectivity_by_azimuth_aggressive(
        reflectivity, window=5, threshold=8.0, background_cutoff=0.0, fill_value=np.nan, min_area=10)
    rainfall_intensity = reflectivity_to_rainfall(reflectivity_filtered)

    # Save processed rainfall intensity
    np.save(output_file, np.where(np.isnan(rainfall_intensity), np.nan, rainfall_intensity))
    print(f"Saved: {output_file}")

    if not os.path.exists(os.path.join(rainfall_intensities_dir, "ranges.npy")):
        save_radar_metadata(rainfall_intensities_dir, sweep_0, radar_data)


def main():
    # --- CONFIGURATION ---
    a, b = 300, 1.5
    path = "./data"
    input_dir = "data/radar_unzipped"
    output_base_dir = "data/radar_rainfall"

    rainfall_intensities_dir = os.path.join(output_base_dir, "rainfall_intensities")
    os.makedirs(rainfall_intensities_dir, exist_ok=True)
    accumulated_rainfall_dir = os.path.join(output_base_dir, "accumulated_rainfall")
    os.makedirs(accumulated_rainfall_dir, exist_ok=True)

    # --- LIST RADAR FILES ---
    radar_files = []
    for f in os.listdir(input_dir):
        if f.endswith(".h5"):
            radar_files.append(os.path.join(input_dir, f))
    radar_files = sorted(radar_files)

    # Process files in parallel
    num_cores = os.cpu_count() - 1
    Parallel(n_jobs=num_cores)(delayed(process_radar_file)(file, rainfall_intensities_dir) for file in radar_files)

    # --- LIST RAINFALL FILES ---
    rainfall_files = []
    for f in os.listdir(rainfall_intensities_dir):
        if f.startswith("rainfall_"):
            rainfall_files.append(os.path.join(rainfall_intensities_dir, f))
    rainfall_files = sorted(rainfall_files)

    # Parse timestamps from filenames
    timestamps = []
    for idx, file in enumerate(rainfall_files):
        ts_str = os.path.basename(file).split("_")[1].split(".")[0]
        ts = datetime.datetime.strptime(ts_str, "%Y%m%d%H%M")
        timestamps.append((idx, ts))

    # --- HOURLY ACCUMULATION ---
    intervals = [1]  # in hours
    for interval_hr in intervals:
        frames_needed = interval_hr * 6  # 12 files per hour
        interval_dir = os.path.join(accumulated_rainfall_dir, f"{interval_hr}h")
        os.makedirs(interval_dir, exist_ok=True)

        # Collect indices that align on the hour
        hourly_indices = []
        for i, ts in timestamps:
            if ts.minute == 0 and ts.second == 0:
                hourly_indices.append(i)

        # For each full-hour timestamp, accumulate previous frames
        for i in hourly_indices:
            if i < frames_needed:
                continue  # Not enough history

            # Select files to sum
            files_to_sum = []
            for j in range(i - frames_needed, i):
                files_to_sum.append(rainfall_files[j])

            try:
                sample = np.load(files_to_sum[0])
            except:
                continue
            accum_rainfall = np.zeros_like(sample)

            # Sum rainfall across selected frames
            for file in files_to_sum:
                try:
                    rainfall = np.load(file)
                    accum_rainfall += np.nan_to_num(rainfall)
                except Exception as e:
                    print(f"Skipping {file} due to error: {e}")
                    break

            # Save accumulated rainfall to file
            timestamp_str = os.path.basename(rainfall_files[i]).split("_")[1].split(".")[0]
            out_name = os.path.join(interval_dir, f"rainfall_{timestamp_str}.npy")
            np.save(out_name, accum_rainfall)
            print(f"Saved accumulated rainfall: {out_name}")


if __name__ == "__main__":
    main()

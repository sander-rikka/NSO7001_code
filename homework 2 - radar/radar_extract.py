import numpy as np
import pandas as pd
import datetime
import os


def get_coords_arr(ranges, azimuths, radar_lat, radar_lon):

    r, theta = np.meshgrid(ranges, np.radians(azimuths))
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    lat = radar_lat + (y / 6371000) * (180 / np.pi)
    lon = radar_lon + (x / (6371000 * np.cos(np.radians(radar_lat)))) * (180 / np.pi)
    return lat, lon


def get_station_index(latarr, lonarr, stationcoords):
    lat, lon = stationcoords
    # Compute squared distance to avoid square root for speed
    dist_sq = (latarr - lat) ** 2 + (lonarr - lon) ** 2
    # Get index of minimum distance in 2D
    idx = np.unravel_index(np.argmin(dist_sq), dist_sq.shape)
    return idx


if __name__ == '__main__':
    # load in radar azimuths, ranges and meta file that holds information to generate coordinate fields.
    azims = np.load('data/radar_rainfall/rainfall_intensities/azimuths.npy')
    ranges = np.load('data/radar_rainfall/rainfall_intensities/ranges.npy')
    meta = np.load('data/radar_rainfall/rainfall_intensities/radar_metadata.npy')

    # generate coordinate fields
    latarr, lonarr = get_coords_arr(ranges, azims, meta[0], meta[1])

    # Türi station that I have used so far
    stationcoords = [58.808708, 25.409156]

    # get array index for the station that user analyses
    lat_ind, lon_ind = get_station_index(latarr, lonarr, stationcoords)

    # loop to extract accumulated rainfall from radar arrays for the station
    image_path = 'data/radar_rainfall/accumulated_rainfall/1h'
    rain_amount = []
    for file in os.listdir(image_path):
        print(file)
        ts_str = os.path.basename(file).split("_")[1].split(".")[0]
        ts = datetime.datetime.strptime(ts_str, "%Y%m%d%H%M")
        rainfall = np.load(os.path.join(image_path, file))
        rain_amount.append((ts, rainfall[lat_ind, lon_ind]))

    # save radar rainfall for further plotting
    rain_df = pd.DataFrame(rain_amount, columns=['datetime', 'radar_rain_amount'])
    rain_df.set_index('datetime', inplace=True)
    rain_df.sort_index(inplace=True)
    rain_df.to_csv('radar_rain_amount.csv')

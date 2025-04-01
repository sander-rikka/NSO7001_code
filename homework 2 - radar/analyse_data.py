"""Script and functions to download radar and measurements and do the analysis."""
# TODO: rewrite in jupyter notebook for next year students :)
from radar_download import download_radar_data_with_limit
from measurement_download import fetch_data_for_parameters
import pandas as pd
import datetime
import matplotlib.pyplot as plt


def download_measurement_data():
    """Download measurement data from KAUR website."""
    params_to_download = ['1h max air temp (C)',
                          '1h precipitation sum (mm)']
    stations_to_download = ['Türi']

    start_date_str = '2024-10-01 00:00:00'
    end_date_str = '2024-10-31 23:59:59'

    final_df = fetch_data_for_parameters(
        params_to_download,
        stations_to_download,
        start_date_str,
        end_date_str
    )
    final_df.to_csv('data/tyri_meas_data_202410.csv')
    return final_df


def download_radar_data():
    start_date = datetime.datetime(2024, 10, 9, 0, 0)
    end_date = datetime.datetime(2024, 10, 16, 23, 59)

    interval_hour = 1
    days_per_hour = 24

    download_radar_data_with_limit(start_date, end_date, interval_hour, days_per_hour)


if __name__ == '__main__':
    pass # comment this line if you want to run the whole script from start to the end

    # description
    # 1. download corresponding measurement data
    #measurements_df = download_measurement_data()

    # 2. based on measurements, find a week from your month that has some variability in precipitation amounts
    # 2.1. download radar data
    #download_radar_data()

    # 4. plot measured precipitation against radar values
    # 4.1 calculate distance between station and radar
    # 4.2 save data to csv -> upload to moodle

    # 5. describe results

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

    # download measurements according to your station
    # find suitable time period to download radar data
    # unzip radar data
    # convert radar reflectivity to rainfall
    # extract rainfall amounts from radar based on the measurement location

    # from measurements take the same time period (5 - 6 values) as radar data in radar_rain_amount.csv
        # use matplotlib scatterplot
        # measured rainfall on x-axis, radar rainfall on y-axis
        # do not forget units
    # calculate following statistics between measured rainfall and radar derived rainfall
        # pearson correlation
        # root mean squared difference (RMSD which is same as RMSE if somebody is confused)
    # calculate distance between radar tower and your station
    # plot all 6 hours of radar data > use radar_plot.py for that
    pass

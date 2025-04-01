""" https://keskkonnaportaal.ee/et/avaandmed/kliimaandmestik/kliimaandmestiku-kirjeldus """

import requests
import pandas as pd
from datetime import datetime, timedelta

# ---------------- Dictionaries ----------------
possible_minute_params = {'10 minute mean wind speed (m/s)': 'WS10MA',
                          '10 minute max wind speed (m/s)': 'WS10MX',
                          '10 minute prevailing wind direction (deg)': 'WS10W',
                          '10 minute precipitation sum (mm)': 'PR10M'}

possible_hour_params = {'1h max wind speed (m/s)': 'WSX1H',
                        'last 10 min mean wind speed (m/s)': 'WS10M',
                        'last 10 min prevailing wind dir (deg)': 'WD10M',
                        '1h max air temp (C)': 'TAX1H',
                        '1h min air temp (C)': 'TAN1H',
                        'air temp at full hour (C)': 'TA',
                        '1h sunshine duration sum (min)': 'SDUR1H',
                        'relative humidity at full hour (%)': 'RH',
                        '1h precipitation sum (mm)': 'PR1H',
                        'air pressure at sea level at full hout (hPa)': 'PA0'}

possible_24h_params = {'24h max wind speed (m/s)': 'DWSX',
                       '24h mean wind speed (m/s)': 'DWS08',
                       '24h max air temp (C)': 'DTAX',
                       '24h min air temp (C)': 'DTAN',
                       '24h mean air temp (C)': 'DTA08',
                       '24h total radiation (MJ/m2)': 'DRQS',
                       '24h mean relative humidity (%)': 'DRH08',
                       '24h precipitation sum (mm)': 'DPREC',
                       '24h mean air pressure at sea level (hPa)': 'DPA008',
                       'snow depth (measured 06:00 UTC) (cm)': 'DSND',
                       '24h sum of sunshine duration (h)': 'DSDUR'}

possible_stations = {'Heltermaa': 'AJHELT01',
                     'Jõgeva': 'AJJOGE01',
                     'Jõhvi': 'AJJOHV01',
                     'Kihnu': 'AJKIHN01',
                     'Kunda': 'AJKUND01',
                     'Kuressaare': 'AJKURE_L',
                     'Kuusiku': 'AJKUUS01',
                     'Lääne-Nigula': 'AJNIGU01',
                     'Narva': 'AJNARV01',
                     'Pakri': 'AJPAKR01',
                     'Pärnu': 'AJPARN01',
                     'Ristna': 'AJRIST01',
                     'Roomassaare': 'AJROOM01',
                     'Ruhnu': 'AJRUHN01',
                     'Sõrve': 'AJSORV01',
                     'Tallinn-Harku': 'AJHARK01',
                     'Tartu-Tõravere': 'AJTART01',
                     'Tiirikoja': 'AJTIIR01',
                     'Tooma': 'AJTOOM01',
                     'Türi': 'AJTURI01',
                     'Valga': 'AJVALG01',
                     'Viljandi': 'AJVILJ01',
                     'Vilsandi': 'AJVILS01',
                     'Virtsu': 'AJVIRT01',
                     'Võru': 'AJVORU01',
                     'Väike-Maarja': 'AJV-MA01'}

# ---------------- Base URLs ----------------
base_url_minute = 'https://keskkonnaandmed.envir.ee/f_kliima_minut?'
base_url_hour = 'https://keskkonnaandmed.envir.ee/f_kliima_tund?'
base_url_24h = 'https://keskkonnaandmed.envir.ee/f_kliima_paev?'


def download_data(data_type, year, station_code, element_code, month=None, day=None):
    """
    Single function to download data for minute, hour, or 24h.
    For minute/hour, pass year, month, day.
    For 24h, pass year, month (day is ignored).
    """
    if data_type == 'minute':
        if month is None or day is None:
            raise ValueError("For minute data, both 'month' and 'day' must be specified.")
        url = (
            f"{base_url_minute}"
            f"aasta=eq.{year}&kuu=eq.{month}&paev=eq.{day}&jaam_kood=eq.{station_code}"
            f"&element_kood=eq.{element_code}"
        )
    elif data_type == 'hour':
        if month is None or day is None:
            raise ValueError("For hour data, both 'month' and 'day' must be specified.")
        url = (
            f"{base_url_hour}"
            f"aasta=eq.{year}&kuu=eq.{month}&paev=eq.{day}&jaam_kood=eq.{station_code}"
            f"&element_kood=eq.{element_code}"
        )
    elif data_type == '24h':
        if month is None:
            raise ValueError("For 24h data, 'month' must be specified (day is ignored).")
        url = (
            f"{base_url_24h}"
            f"aasta=eq.{year}&kuu=eq.{month}&jaam_kood=eq.{station_code}"
            f"&element_kood=eq.{element_code}"
        )
    else:
        raise ValueError("data_type must be one of: 'minute', 'hour', or '24h'.")

    response = requests.get(url)
    return response.json()


def to_dataframe(raw_data, param_label):
    """
    Convert the JSON list of dicts into a DataFrame with columns:
      - 'datetime'
      - param_label
    For minute/hour: [aasta, kuu, paev, tund, vaartus]
    For 24h:         [aasta, kuu, paev, vaartus]
    """
    if not raw_data:
        return pd.DataFrame(columns=['datetime', param_label])

    df = pd.DataFrame(raw_data)

    if 'minut' in df.columns:
        df['datetime'] = df.apply(
            lambda row: datetime(row['aasta'], row['kuu'], row['paev'], row['tund'], row['minut']),
            axis=1
        )
    elif 'minut' not in df.columns:
        df['datetime'] = df.apply(
            lambda row: datetime(row['aasta'], row['kuu'], row['paev'], row['tund']),
            axis=1
        )
    else:
        # No 'tund' => daily data
        df['datetime'] = df.apply(
            lambda row: datetime(row['aasta'], row['kuu'], row['paev']),
            axis=1
        )

    df.rename(columns={'vaartus': param_label}, inplace=True)
    return df[['datetime', param_label]]


def fetch_data_for_parameters(params_to_download, stations_to_download, start_date_str, end_date_str):
    """
    Fetch data (minute, hour, 24h) for the given parameters and stations
    between start_date_str and end_date_str.

    Returns a single combined DataFrame.
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        exit('End date not valid. Probably day number too high for selected month.')

    print(f'Fetching {len(params_to_download)} measured parameters for {len(stations_to_download)} station(s).')
    final_df = pd.DataFrame()

    for station_name in stations_to_download:
        print(f'Fetching data for {station_name}...')
        station_code = possible_stations[station_name]

        for param_fullname in params_to_download:
            # Determine data type and element_code
            if param_fullname in possible_minute_params:
                data_type = 'minute'
                element_code = possible_minute_params[param_fullname]
            elif param_fullname in possible_hour_params:
                data_type = 'hour'
                element_code = possible_hour_params[param_fullname]
            elif param_fullname in possible_24h_params:
                data_type = '24h'
                element_code = possible_24h_params[param_fullname]
            else:
                # Unrecognized param
                continue

            # Create a column label, e.g. "Kihnu_WS10MA"
            col_label = f"{station_name}_{element_code}"

            # -- Create an *accumulator* DF just for this station–param --
            temp_accumulator_df = pd.DataFrame()

            if data_type in ['minute', 'hour']:
                # Loop day by day
                curr_date = start_date
                while curr_date <= end_date:
                    y, m, d = curr_date.year, curr_date.month, curr_date.day
                    raw_data = download_data(data_type, y, station_code, element_code,
                                             month=m, day=d)
                    df_temp = to_dataframe(raw_data, col_label)

                    # Concatenate row-wise (same columns, more rows)
                    # No risk of new "col_label_x / col_label_y"
                    temp_accumulator_df = pd.concat([temp_accumulator_df, df_temp], ignore_index=True)

                    curr_date += timedelta(days=1)

            # 24h => fetch month by month
            else:
                # data_type == "24h", loop by month
                month_start = datetime(start_date.year, start_date.month, 1)
                while month_start <= end_date:
                    y, m = month_start.year, month_start.month
                    raw_data = download_data(
                        data_type, y, station_code, element_code, month=m
                    )
                    df_temp = to_dataframe(raw_data, col_label)

                    temp_accumulator_df = pd.concat(
                        [temp_accumulator_df, df_temp],
                        ignore_index=True
                    )

                    # Move to next month
                    next_month = (month_start.month % 12) + 1
                    next_year = month_start.year + (month_start.month // 12)
                    month_start = datetime(next_year, next_month, 1)

                    if month_start > end_date:
                        break

            # 2b) Remove exact duplicate rows, if any
            temp_accumulator_df.drop_duplicates(subset=["datetime"], inplace=True)

            # 3) Merge once with final_df
            #    We'll set datetime as the index to do index-based joins
            temp_accumulator_df.set_index("datetime", inplace=True)

            # If final_df is empty, just copy
            if final_df.empty:
                final_df = temp_accumulator_df
            else:
                # Otherwise, do a join on index (datetime)
                # This ensures only 1 column named col_label is created
                final_df = final_df.join(temp_accumulator_df[[col_label]], how="outer")

            # Now we move on to the next param or next station

    # 4) Optionally reset index so 'datetime' is a column again
    final_df.reset_index(inplace=True)

    # Sort by datetime
    final_df.sort_values("datetime", inplace=True)
    final_df.set_index('datetime', inplace=True)

    return final_df


if __name__ == '__main__':
    """
    Usage example as shown below:
    - define parameters to download in a list
    - define station(s) to download
    - define start and end dates
    - don't forget to save the data
    """

    # ========== Only definitions of parameters, stations, dates ==========
    # NB! only use parameters from single parameter (minute, hour, day) list at once.
    # NB! mixed parameters from different time intervals not checked --> probably fails?
    #params_to_download = [
    #    '10 minute precipitation sum (mm)',
    #    '10 minute mean wind speed (m/s)'
    #]
    params_to_download = ['1h max air temp (C)',
                          '1h precipitation sum (mm)']
    stations_to_download = ['Türi']

    start_date_str = '2023-11-01 00:00:00'
    end_date_str = '2023-11-30 23:59:59'

    # ========== Call the function to fetch data ==========
    final_df = fetch_data_for_parameters(
        params_to_download,
        stations_to_download,
        start_date_str,
        end_date_str
    )

    # Example: save to CSV or process further
    final_df.to_csv('data/tyri_meas_data_202311.csv')
    print(final_df.head(20))
    print("Data download complete.")

import os
import json
import time
import datetime
import requests

path = "./data/radar_raw"
os.makedirs(path, exist_ok=True)

zipped_files_url = "https://avaandmed.keskkonnaportaal.ee/_vti_bin/RmApi.svc/active/items/zipped-files"

base_filter_raw_json = {
    "filter": {
        "and": {
            "children": [
                {
                    "isEqual": {
                        "field": "$contentType",
                        "value": "0102FB01"
                    }
                },
                {
                    "and": {
                        "children": [
                            {
                                "and": {
                                    "children": [
                                        {
                                            "and": {
                                                "children": [
                                                    {
                                                        "greaterThanOrEqual": {
                                                            "field": "Timestamp",
                                                            "value": ""
                                                        }
                                                    },
                                                    {
                                                        "lessThanOrEqual": {
                                                            "field": "Timestamp",
                                                            "value": ""
                                                        }
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "isEqual": {
                                                "field": "Phenomenon",
                                                "value": "VOL"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "isEqual":{
                                    "field": "Radar",
                                    "value": "S\u00FCrgavere radar (SUR)"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
}

base_filter_json = {
    "filter": {
        "and": {
            "children": [
                {
                    "and": {
                        "children": [
                            {
                                "isEqual": {
                                    "field": "$contentType",
                                    "value": "0102FB01"
                                }
                            },
                            {
                                "isEqual": {
                                    "field": "Radar",
                                    "value": "comp"
                                }
                            }
                        ]
                    }
                },
                {
                    "and": {
                        "children": [
                            {
                                "greaterThanOrEqual": {
                                    "field": "Timestamp",
                                    "value": ""
                                }
                            },
                            {
                                "lessThanOrEqual": {
                                    "field": "Timestamp",
                                    "value": ""
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
}


def generate_ranges(start_date, end_date, interval_hour):
    ranges = []
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + datetime.timedelta(hours=interval_hour) - datetime.timedelta(seconds=1)
        if next_date > end_date:
            next_date = end_date
        ranges.append((current_date, next_date))
        current_date = next_date + datetime.timedelta(seconds=1)
    return ranges


def format_timestep(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.0000000\u002B00:00")


def download_radar_data_for_range(start_datetime, end_datetime, raw=False):
    start_timestamp = format_timestep(start_datetime)
    end_timestamp = format_timestep(end_datetime)

    if not raw:
        filter_json = base_filter_json.copy()
        filter_json["filter"]["and"]["children"][1]["and"]["children"][0]["greaterThanOrEqual"]["value"] = start_timestamp
        filter_json["filter"]["and"]["children"][1]["and"]["children"][1]["lessThanOrEqual"]["value"] = end_timestamp
    else:
        filter_json = base_filter_raw_json.copy()
        filter_json["filter"]["and"]["children"][1]["and"]["children"][0]["and"]["children"][0]["and"]["children"][0][
            "greaterThanOrEqual"]["value"] = start_timestamp
        filter_json["filter"]["and"]["children"][1]["and"]["children"][0]["and"]["children"][0]["and"]["children"][1][
            "lessThanOrEqual"]["value"] = end_timestamp

    try:
        print(f"Requesting data from {start_timestamp} to {end_timestamp}...")
        with requests.post(
                zipped_files_url,
                json=filter_json,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=360
        ) as response:

            if response.status_code == 200:
                print(response.headers)

                filename = f"{path}/SUR_{start_datetime.strftime('%Y%m%d%H%M')}_{end_datetime.strftime('%Y%m%d%H%M')}.zip"
                with open(filename, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):

                        file.write(chunk)
                print(f"Data downloaded successfully as '{filename}'.")
                return True
            else:
                print(f"Failed to download data: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def download_radar_data_with_limit(start_datetime: datetime.datetime,
                                   end_datetime: datetime.datetime,
                                   interval_hour: int,
                                   days_per_hour: int,
                                   raw=True):

    ranges = generate_ranges(start_datetime, end_datetime, interval_hour)
    total_days_downloaded = 0
    start_time = time.time()

    for start, end in ranges:
        if total_days_downloaded >= days_per_hour:
            elapsed_time = time.time() - start_time
            if elapsed_time < 3600:
                wait_time = 3800 - elapsed_time
                print(f"Waiting {wait_time:.2f} seconds to comply with the hourly limit...")
                time.sleep(wait_time)
            total_days_downloaded = 0
            start_time = time.time()

        success = download_radar_data_for_range(start, end, raw=raw)
        if success:
            total_days_downloaded += interval_hour / 24
        else:
            print(f"Skipping to the next range after failure for {start} to {end}.")


if __name__ == '__main__':
    # 1. get suitable 6h range to download radar data from measurements
    start_date = datetime.datetime(2023, 11, 13, 2, 0)
    end_date = datetime.datetime(2023, 11, 13, 7, 59)
    assert start_date < end_date

    # todo: check raw data download
    interval_hour = 1
    days_per_hour = 12

    download_radar_data_with_limit(start_date, end_date, interval_hour, days_per_hour)

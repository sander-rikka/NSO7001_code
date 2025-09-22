"""
KAUR downloader — parallel by month + progress prints + per‑station CSVs
- Parallel month fetching with pagination (20k rows/page)
- Progress prints for each station/parameter
- Datetime index is NAIVE (no timezone) and named "datetime (utc)"
- Final index reindexed to strict 10‑minute frequency → gaps become NaN
- Per‑station CSVs with columns as element codes (no station name)

Adjust MAX_WORKERS as needed to be polite to the API.
"""

import time
import threading
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

# ---------------- Dictionaries ----------------
possible_minute_params = {
    '10 minute mean wind speed (m/s)': 'WS10MA',
    '10 minute max wind speed (m/s)': 'WS10MX',
    '10 minute prevailing wind direction (deg)': 'WD10MA',
    '10 minute precipitation sum (mm)': 'PR10M',
}

# possible_hour_params = {
#     '1h max wind speed (m/s)': 'WSX1H',
#     'last 10 min mean wind speed (m/s)': 'WS10M',
#     'last 10 min prevailing wind dir (deg)': 'WD10M',
#     '1h max air temp (C)': 'TAX1H',
#     '1h min air temp (C)': 'TAN1H',
#     '1h mean air temp (C)': 'TA1H',
#     '1h mean relative humidity (%)': 'RH1H',
#     '1h precipitation sum (mm)': 'PR1H',
#     '1h mean air pressure (hPa)': 'PA1H',
#     '1h mean wind speed (m/s)': 'WS1H',
#     '1h mean wind direction (deg)': 'WD1H',
#     '1h mean radiation (W/m2)': 'RQS1H',
#     '1h sunshine duration (min)': 'SDUR1H',
# }

possible_hour_params = {
    '1h max wind speed (m/s)': 'WSX1H',
    'last 10 min mean wind speed (m/s)': 'WS10M',
    'last 10 min prevailing wind dir (deg)': 'WD10M',
    '1h max air temp (C)': 'TAX1H',
    '1h min air temp (C)': 'TAN1H',
    'air temp at full hour (C)': 'TA',
    '1h sunshine duration sum (min)': 'SDUR1H',
    'relative humidity at full hour (%)': 'RH',
    '1h precipitation sum (mm)': 'PR1H',
    'air pressure at sea level at full hour (hPa)': 'PA0'
}

possible_24h_params = {
    '24h mean wind direction (deg)': 'DWD08',
    '24h mean wind speed (m/s)': 'DWS08',
    '24h max air temp (C)': 'DTAX',
    '24h min air temp (C)': 'DTAN',
    '24h mean air temp (C)': 'DTA08',
    '24h total radiation (MJ/m2)': 'DRQS',
    '24h mean relative humidity (%)': 'DRH08',
    '24h precipitation sum (mm)': 'DPREC',
    '24h mean air pressure at sea level (hPa)': 'DPA008',
    'snow depth (measured 06:00 UTC) (cm)': 'DSND',
    '24h sum of sunshine duration (h)': 'DSDUR',
}

possible_stations = {
    'Heltermaa': 'AJHELT01',
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
    'Väike-Maarja': 'AJV-MA01'
}

# --- API base URLs ---
BASE_URLS = {
    'minute': 'https://keskkonnaandmed.envir.ee/f_kliima_minut?',
    'hour':   'https://keskkonnaandmed.envir.ee/f_kliima_tund?',
    '24h':    'https://keskkonnaandmed.envir.ee/f_kliima_paev?',
}

# --- Pagination / request tuning ---
MAX_PAGE_SIZE = 20000
REQUEST_TIMEOUT = 30
MAX_RETRIES = 4
BACKOFF_BASE = 1.8

# Concurrency
MAX_WORKERS = 6

# --- Minimal column selection to reduce payload ---
SELECT_COLS = {
    'minute': 'aasta,kuu,paev,tund,minut,vaartus',
    'hour':   'aasta,kuu,paev,tund,vaartus',
    '24h':    'aasta,kuu,paev,vaartus',
}

# --- Thread-local session ---
_thread_local = threading.local()
def get_session() -> requests.Session:
    s = getattr(_thread_local, "session", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"Accept": "application/json"})
        _thread_local.session = s
    return s

print_lock = threading.Lock()
def log(msg: str) -> None:
    with print_lock:
        print(msg, flush=True)


def iter_months(start: datetime, end: datetime):
    """Yield (year, month) pairs from start..end inclusive."""
    y, m = start.year, start.month
    while (y < end.year) or (y == end.year and m <= end.month):
        yield y, m
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def month_bounds(year: int, month: int) -> (datetime, datetime):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(seconds=1)
    return start, end


def build_query(data_type: str, year: int, station_code: str, element_code: str,
                month: Optional[int] = None, day: Optional[int] = None) -> str:
    base = BASE_URLS[data_type]
    parts = [
        f"aasta=eq.{year}",
        f"jaam_kood=eq.{station_code}",
        f"element_kood=eq.{element_code}",
        f"select={SELECT_COLS[data_type]}",
    ]
    if month is None:
        raise ValueError("Provide month for monthly batching.")
    parts.append(f"kuu=eq.{month}")
    if day is not None:
        parts.append(f"paev=eq.{day}")
    return base + "&".join(parts)


def request_paged_json(base_qs: str) -> List[dict]:
    """Fetch all rows for a given query using limit/offset pagination with retries."""
    all_rows: List[dict] = []
    offset = 0

    while True:
        url = f"{base_qs}&limit={MAX_PAGE_SIZE}&offset={offset}"
        attempt = 0
        while True:
            try:
                resp = get_session().get(url, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                page = resp.json()
                break
            except Exception as e:
                attempt += 1
                if attempt > MAX_RETRIES:
                    raise
                sleep_s = (BACKOFF_BASE ** attempt) + (0.05 * attempt)
                log(f"  retrying after error ({attempt}/{MAX_RETRIES}): {e}")
                time.sleep(sleep_s)

        if not page:
            break

        all_rows.extend(page)
        if len(page) < MAX_PAGE_SIZE:
            break
        offset += MAX_PAGE_SIZE

    return all_rows


def rows_to_df(raw_data: List[dict], col_label: str, data_type: str) -> pd.DataFrame:
    """Normalize KAUR rows → DataFrame with a single value column under col_label."""
    if not raw_data:
        return pd.DataFrame(columns=["datetime", col_label])

    df = pd.DataFrame(raw_data)

    # coerce date parts to int safely
    for c in ("aasta", "kuu", "paev", "tund", "minut"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64").fillna(0).astype(int)

    # Make naive datetimes (no timezone) — still UTC by definition of the source
    if data_type == "minute":
        tmp = df.rename(columns={"aasta": "year", "kuu": "month", "paev": "day", "tund": "hour", "minut": "minute"})
        df["datetime"] = pd.to_datetime(tmp[["year", "month", "day", "hour", "minute"]], errors="coerce")
    elif data_type == "hour":
        tmp = df.rename(columns={"aasta": "year", "kuu": "month", "paev": "day", "tund": "hour"})
        df["datetime"] = pd.to_datetime(tmp[["year", "month", "day", "hour"]], errors="coerce")
    else:  # 24h
        tmp = df.rename(columns={"aasta": "year", "kuu": "month", "paev": "day"})
        df["datetime"] = pd.to_datetime(tmp[["year", "month", "day"]], errors="coerce")

    df = df.dropna(subset=["datetime"]).copy()
    df.rename(columns={"vaartus": col_label}, inplace=True)
    return df[["datetime", col_label]]


def fetch_month_chunk(station_code: str, element_code: str, data_type: str,
                      y: int, m: int, col_label: str, tag: str) -> pd.DataFrame:
    qs = build_query(data_type, y, station_code, element_code, month=m)
    rows = request_paged_json(qs)
    log(f"    [{tag}] {y}-{m:02d} fetched ({len(rows)} rows)")
    return rows_to_df(rows, col_label, data_type)


def fetch_data_for_parameters_parallel(params_to_download: List[str],
                                       stations_to_download: List[str],
                                       start_date_str: str,
                                       end_date_str: str,
                                       max_workers: int = MAX_WORKERS) -> Dict[str, pd.DataFrame]:
    """
    Parallel month fetching with final 10‑minute reindex for gaps.
    RETURNS: dict { station_name: DataFrame } —
             each DF is indexed by naive UTC datetime (name: 'datetime (utc)')
             and columns are element codes only (no station names).
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
    log(f"Fetching {len(params_to_download)} parameter(s) for {len(stations_to_download)} station(s) "
        f"from {start_date_str} to {end_date_str} with {max_workers} workers.")

    station_frames: Dict[str, pd.DataFrame] = {}

    for station_name in stations_to_download:
        station_code = possible_stations[station_name]
        log(f"\nStation: {station_name} ({station_code})")

        # We'll build a wide DF per station with element_code columns
        station_df = pd.DataFrame()

        for param_fullname in params_to_download:
            if param_fullname in possible_minute_params:
                data_type = "minute"
                element_code = possible_minute_params[param_fullname]
            elif param_fullname in possible_hour_params:
                data_type = "hour"
                element_code = possible_hour_params[param_fullname]
            elif param_fullname in possible_24h_params:
                data_type = "24h"
                element_code = possible_24h_params[param_fullname]
            else:
                log(f"  Skipping unknown parameter: {param_fullname}")
                continue

            col_label = element_code  # IMPORTANT: no station name in the header

            # Build month job list
            month_jobs: List[Tuple[int,int]] = []
            for (y, m) in iter_months(start_date, end_date):
                m_start, m_end = month_bounds(y, m)
                if m_end < start_date or m_start > end_date:
                    continue
                month_jobs.append((y, m))

            total = len(month_jobs)
            if total == 0:
                log(f"  {param_fullname} → {element_code}: no months in range")
                continue

            log(f"  Param: {param_fullname} → {element_code} [{data_type}], months: {total}")

            frames: List[pd.DataFrame] = []
            tag = f"{station_name} {element_code}"
            done = 0

            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = [
                    ex.submit(fetch_month_chunk, station_code, element_code, data_type, y, m, col_label, tag)
                    for (y, m) in month_jobs
                ]
                for fut in as_completed(futs):
                    try:
                        df_m = fut.result()
                        if not df_m.empty:
                            frames.append(df_m)
                    except Exception as e:
                        log(f"    [{tag}] ERROR: {e}")
                    finally:
                        done += 1
                        log(f"    [{tag}] progress: {done}/{total} months")

            if not frames:
                log(f"  {element_code}: no data returned")
                continue

            acc_df = pd.concat(frames, ignore_index=True)
            acc_df.drop_duplicates(subset=["datetime"], inplace=True)

            # trim to requested [start, end], sort, set index
            mask = (acc_df["datetime"] >= start_date) & (acc_df["datetime"] <= end_date)
            acc_df = acc_df.loc[mask].sort_values("datetime").set_index("datetime")

            # Merge into station-wide DF
            if station_df.empty:
                station_df = acc_df
            else:
                station_df = station_df.join(acc_df[[col_label]], how="outer")

        # Final tidy per station: sort and reindex to 10‑minute grid (naive)
        if not station_df.empty:
            station_df = station_df.sort_index()
            full_index = pd.date_range(start=start_date, end=end_date, freq="1h")
            station_df = station_df.reindex(full_index)
            station_df.index.name = "datetime (utc)"
            station_frames[station_name] = station_df
            log(f"  Station {station_name}: data shape {station_df.shape}")
        else:
            log(f"  Station {station_name}: no data")

    return station_frames


def save_station_csvs(station_frames: Dict[str, pd.DataFrame], out_dir: Path) -> None:
    """Save one CSV per station with formatted datetime index 'YYYY-mm-dd HH:MM' (no seconds)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for station, df in station_frames.items():
        # Format index to drop seconds
        idx_str = df.index.strftime('%Y-%m-%d %H:%M')
        df_to_write = df.copy()
        df_to_write.index = idx_str
        out = out_dir / f"{station.replace(' ', '_')}_1h_wind_2011-2025jul.csv"
        df_to_write.to_csv(out, index=True)
        log(f"Saved → {out}")


if __name__ == "__main__":
    # Example usage
    # params_to_download = [
    #     '10 minute mean wind speed (m/s)',
    #     '10 minute max wind speed (m/s)',
    #     '10 minute prevailing wind direction (deg)'
    # ]
    params_to_download = [
        '1h max wind speed (m/s)',
        'last 10 min mean wind speed (m/s)',
        'last 10 min prevailing wind dir (deg)',
        '1h max air temp (C)',
        '1h min air temp (C)',
        'air temp at full hour (C)',
        '1h sunshine duration sum (min)',
        'relative humidity at full hour (%)',
        '1h precipitation sum (mm)',
        'air pressure at sea level at full hour (hPa)'
    ]
    stations_to_download = ['Tallinn-Harku']
    #stations_to_download = ['Kunda', 'Kihnu', 'Ruhnu', 'Sõrve', 'Vilsandi', 'Ristna', 'Heltermaa', 'Virtsu', 'Pakri',
    #                        'Tiirikoja']

    start_date_str = "2011-01-01 00:00:00"
    end_date_str = "2025-07-30 00:00:00"

    frames = fetch_data_for_parameters_parallel(
        params_to_download,
        stations_to_download,
        start_date_str,
        end_date_str,
        max_workers=6,
    )

    # One CSV per station, headers are element codes, index labeled "datetime (utc)"
    save_station_csvs(frames, Path("data"))

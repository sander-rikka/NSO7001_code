import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io import shapereader
from pathlib import Path


def _resolve_default_land_shp():
    here = Path(__file__).resolve().parent
    shp = here.parent / "assets" / "ne_50m_land" / "ne_50m_land.shp"
    if shp.exists():
        return str(shp)
    return None


def plot_radar_polar(
    array_to_plot,
    title,
    filename,
    ranges,
    azimuths,
    radar_lat,
    radar_lon,
    land_shapefile=None,
    use_online_features=False,
    station_coords=None,
    station_label="Station",
    transparency_threshold=0.05,
    radar_alpha=0.7,
):

    levels = np.linspace(0, 15, 15)
    base_cmap = plt.cm.RdBu_r

    r, theta = np.meshgrid(ranges, np.radians(azimuths))
    # ODIM azimuth is clockwise from north:
    # x (east) = r * sin(theta), y (north) = r * cos(theta)
    x = r * np.sin(theta)
    y = r * np.cos(theta)

    lat = radar_lat + (y / 6371000) * (180 / np.pi)
    lon = radar_lon + (x / (6371000 * np.cos(np.radians(radar_lat)))) * (180 / np.pi)

    projection = ccrs.Stereographic(central_latitude=radar_lat, central_longitude=radar_lon)
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(8, 8))

    land_shapefile = land_shapefile or _resolve_default_land_shp()
    if land_shapefile and Path(land_shapefile).exists():
        land_geoms = shapereader.Reader(land_shapefile).geometries()
        land_feature = cfeature.ShapelyFeature(
            land_geoms, ccrs.PlateCarree(), edgecolor='black', linewidth=0.6, facecolor='#fefefe'
        )
        ax.add_feature(land_feature, zorder=0)
    elif use_online_features:
        # Fallback for environments where online Natural Earth download is allowed.
        ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '50m',
                                                    edgecolor='face', facecolor='#fefefe'), zorder=0)
        ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', '50m',
                                                    edgecolor='face', facecolor='#e2e3e8'), zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color='black', zorder=1)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle='--', color='gray', zorder=1)
    else:
        print("Local land shapefile not found and online features disabled; plotting rainfall only.")

    norm = BoundaryNorm(levels, ncolors=256)
    masked = np.ma.masked_invalid(array_to_plot)
    masked = np.ma.masked_where(masked < transparency_threshold, masked)

    im = ax.pcolormesh(lon, lat, masked, shading='auto',
                       cmap=base_cmap, norm=norm, alpha=radar_alpha,
                       transform=ccrs.PlateCarree(), zorder=2)

    cbar = plt.colorbar(
        mappable=plt.cm.ScalarMappable(norm=norm, cmap=base_cmap),
        ax=ax,
        orientation="vertical",
        pad=0.02
    )
    cbar.set_label("Radar rainfall (mm)")
    cbar.solids.set_alpha(1)

    gl = ax.gridlines(draw_labels=True, linestyle='--', linewidth=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.x_inline = False
    gl.y_inline = False
    gl.xlabel_style = {'rotation': 0}
    gl.ylabel_style = {'rotation': 0}

    # Radar marker (cross)
    radar_handle, = ax.plot(
        radar_lon, radar_lat, marker='x', color='black', markersize=10,
        transform=ccrs.PlateCarree(), zorder=4, label='Radar'
    )

    # Station marker (green square)
    station_handle = None
    if station_coords is not None:
        station_lat, station_lon = station_coords
        station_handle, = ax.plot(
            station_lon, station_lat, marker='s', color='green', markersize=7,
            markeredgecolor='black', markeredgewidth=0.6,
            transform=ccrs.PlateCarree(), zorder=5, label=station_label
        )
        # Slight text offset so overlap is still readable.
        ax.text(
            station_lon + 0.08, station_lat + 0.05, station_label,
            color='green', fontsize=8, transform=ccrs.PlateCarree(), zorder=6
        )

    handles = [radar_handle]
    if station_handle is not None:
        handles.append(station_handle)
    ax.legend(handles=handles, loc='lower left')
    ax.set_title(title)
    plt.savefig(filename)
    plt.close()


if __name__ == '__main__':
    file_to_plot = 'data/radar_rainfall/accumulated_rainfall/1h/rainfall_202311130300.npy'
    azims = np.load('data/radar_rainfall/rainfall_intensities/azimuths.npy')
    ranges = np.load('data/radar_rainfall/rainfall_intensities/ranges.npy')
    meta = np.load('data/radar_rainfall/rainfall_intensities/radar_metadata.npy')
    array_to_plot = np.load(file_to_plot)

    local_land = "assets/ne_50m_land/ne_50m_land.shp"
    plot_radar_polar(
        array_to_plot,
        'Rainfall 202311130300',
        'radar_rainfall_202311130300.png',
        ranges,
        azims,
        meta[0],
        meta[1],
        land_shapefile=local_land,
        use_online_features=False,
        station_coords=(58.808708, 25.409156),
        station_label="Turi station",
        transparency_threshold=0.05,
        radar_alpha=0.7,
    )

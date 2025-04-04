import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature


def plot_radar_polar(array_to_plot, title, filename, ranges, azimuths, radar_lat, radar_lon):

    levels = np.linspace(0, 15, 15)

    base_cmap = plt.cm.RdBu_r

    base_colors = base_cmap(np.linspace(0, 1, 256))
    base_colors[:, -1] = 0.5
    alpha_cmap = ListedColormap(base_colors)

    r, theta = np.meshgrid(ranges, np.radians(azimuths))
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    lat = radar_lat + (y / 6371000) * (180 / np.pi)
    lon = radar_lon + (x / (6371000 * np.cos(np.radians(radar_lat)))) * (180 / np.pi)

    projection = ccrs.Stereographic(central_latitude=radar_lat, central_longitude=radar_lon)
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(8, 8))

    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '50m',
                                                edgecolor='face', facecolor='#fefefe'), zorder=0)
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', '50m',
                                                edgecolor='face', facecolor='#e2e3e8'), zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color='black', zorder=1)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle='--', color='gray', zorder=1)

    norm = BoundaryNorm(levels, ncolors=256)

    im = ax.pcolormesh(lon, lat, array_to_plot, shading='auto',
                       cmap=alpha_cmap, norm=norm,
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

    ax.set_title(title)
    plt.savefig(filename)
    plt.close()


if __name__ == '__main__':
    file_to_plot = 'data/radar_rainfall/accumulated_rainfall/1h/rainfall_202311130300.npy'
    azims = np.load('data/radar_rainfall/rainfall_intensities/azimuths.npy')
    ranges = np.load('data/radar_rainfall/rainfall_intensities/ranges.npy')
    meta = np.load('data/radar_rainfall/rainfall_intensities/radar_metadata.npy')
    array_to_plot = np.load(file_to_plot)

    plot_radar_polar(array_to_plot, 'Rainfall 202311130300', 'radar_rainfall_202311130300.png', ranges,
                     azims, meta[0], meta[1])

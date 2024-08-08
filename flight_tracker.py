# IMPORT LIBRARIES
import requests
import json
import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import HoverTool, LabelSet, ColumnDataSource
from bokeh.tile_providers import Vendors
import numpy as np
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

# FUNCTION TO CONVERT GCS WGS84 TO WEB MERCATOR
# DATAFRAME
def wgs84_to_web_mercator(df, lon="long", lat="lat"):
    k = 6378137
    df["x"] = df[lon] * (k * np.pi / 180.0)
    df["y"] = np.log(np.tan((90 + df[lat]) * np.pi / 360.0)) * k
    return df

# POINT
def wgs84_web_mercator_point(lon, lat):
    k = 6378137
    x = lon * (k * np.pi / 180.0)
    y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k
    return x, y

# AREA EXTENT COORDINATE WGS84
lon_min, lat_min = -125.974, 30.038
lon_max, lat_max = -68.748, 52.214

# COORDINATE CONVERSION
xy_min = wgs84_web_mercator_point(lon_min, lat_min)
xy_max = wgs84_web_mercator_point(lon_max, lat_max)

# COORDINATE RANGE IN WEB MERCATOR
x_range, y_range = ([xy_min[0], xy_max[0]], [xy_min[1], xy_max[1]])

# REST API QUERY
user_name = ''
password = ''
url_data = f'https://{user_name}:{password}@opensky-network.org/api/states/all?lamin={lat_min}&lomin={lon_min}&lamax={lat_max}&lomax={lon_max}'

# FLIGHT TRACKING FUNCTION
def flight_tracking(doc):
    # Initialize Bokeh column data source
    flight_source = ColumnDataSource({
        'icao24': [], 'callsign': [], 'origin_country': [],
        'time_position': [], 'last_contact': [], 'long': [], 'lat': [],
        'baro_altitude': [], 'on_ground': [], 'velocity': [], 'true_track': [],
        'vertical_rate': [], 'sensors': [], 'geo_altitude': [], 'squawk': [], 'spi': [], 'position_source': [], 'x': [], 'y': [],
        'rot_angle': [], 'url': []
    })

    # Updating flight data
    def update():
        response = requests.get(url_data).json()

        # Convert to Pandas DataFrame
        col_name = ['icao24', 'callsign', 'origin_country', 'time_position', 'last_contact', 'long', 'lat', 'baro_altitude', 'on_ground', 'velocity',
                    'true_track', 'vertical_rate', 'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source']

        flight_df = pd.DataFrame(response['states'], columns=col_name)
        wgs84_to_web_mercator(flight_df)
        flight_df = flight_df.fillna('No Data')
        flight_df['rot_angle'] = flight_df['true_track'] * -1
        icon_url = 'https://cdn-icons-png.flaticon.com/512/0/619.png'  # Replace with the actual icon URL
        #icon_url = 'file:///./plane.png'  # Replace with the actual icon URL
        flight_df['url'] = icon_url

        # Convert to Bokeh datasource and streaming
        n_roll = len(flight_df.index)
        flight_source.stream(flight_df.to_dict(orient='list'), n_roll)

    # Callback update in an interval
    doc.add_periodic_callback(update, 5000)  # 5000 ms for registered user

    # Plot aircraft position
    p = figure(x_range=x_range, y_range=y_range, x_axis_type='mercator', y_axis_type='mercator', sizing_mode='scale_width', height=300)
    p.add_tile(Vendors.STAMEN_TERRAIN)
    p.image_url(url='url', x='x', y='y', source=flight_source, anchor='center', angle_units='deg', angle='rot_angle', h_units='screen', w_units='screen', w=40, h=40)
    p.scatter('x', 'y', source=flight_source, fill_color='red', hover_color='yellow', size=10, fill_alpha=0.8, line_width=0)

    # Add hover tool and label
    my_hover = HoverTool()
    my_hover.tooltips = [('Call sign', '@callsign'), ('Origin Country', '@origin_country'), ('Velocity (m/s)', '@velocity'), ('Altitude (m)', '@baro_altitude')]
    labels = LabelSet(x='x', y='y', text='callsign', level='glyph', x_offset=5, y_offset=5, source=flight_source, background_fill_color='white', text_font_size="8pt")
    p.add_tools(my_hover)
    p.add_layout(labels)

    doc.title = 'REAL TIME FLIGHT TRACKING'
    doc.add_root(p)

# SERVER CODE
apps = {'/': Application(FunctionHandler(flight_tracking))}
server = Server(apps, port=8084)
server.start()

# Running the server
server.io_loop.add_callback(server.show, "/")
server.io_loop.start()

# Import necessary libraries
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

# Function to convert latitude and longitude from WGS84 (World Geodetic System) to Web Mercator coordinates
def wgs84_to_web_mercator(df, lon="long", lat="lat"):
    k = 6378137  # Constant for Web Mercator conversion
    df["x"] = df[lon] * (k * np.pi / 180.0)  # Convert longitude to Web Mercator
    df["y"] = np.log(np.tan((90 + df[lat]) * np.pi / 360.0)) * k  # Convert latitude to Web Mercator
    return df

# Function to convert a single point from WGS84 to Web Mercator coordinates
def wgs84_web_mercator_point(lon, lat):
    k = 6378137  # Constant for Web Mercator conversion
    x = lon * (k * np.pi / 180.0)  # Convert longitude
    y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k  # Convert latitude
    return x, y

# Define the geographical bounding box for flight tracking in WGS84 coordinates
lon_min, lat_min = -125.974, 30.038  # Bottom-left corner of the area (Longitude, Latitude)
lon_max, lat_max = -68.748, 52.214  # Top-right corner of the area (Longitude, Latitude)

# Convert WGS84 coordinates to Web Mercator for plotting
xy_min = wgs84_web_mercator_point(lon_min, lat_min)  # Bottom-left corner in Web Mercator
xy_max = wgs84_web_mercator_point(lon_max, lat_max)  # Top-right corner in Web Mercator

# Define the coordinate range for the plot in Web Mercator
x_range, y_range = ([xy_min[0], xy_max[0]], [xy_min[1], xy_max[1]])

# REST API Query for flight tracking data
user_name = ''  # Insert your OpenSky Network username
password = ''  # Insert your OpenSky Network password
# Construct the URL to access the OpenSky API, querying flight data within the defined geographic area
url_data = f'https://{user_name}:{password}@opensky-network.org/api/states/all?lamin={lat_min}&lomin={lon_min}&lamax={lat_max}&lomax={lon_max}'

# Function to track and visualize real-time flights on a Bokeh plot
def flight_tracking(doc):
    # Initialize an empty Bokeh ColumnDataSource to hold flight data
    flight_source = ColumnDataSource({
        'icao24': [], 'callsign': [], 'origin_country': [], 'time_position': [], 'last_contact': [],
        'long': [], 'lat': [], 'baro_altitude': [], 'on_ground': [], 'velocity': [], 'true_track': [],
        'vertical_rate': [], 'sensors': [], 'geo_altitude': [], 'squawk': [], 'spi': [], 'position_source': [],
        'x': [], 'y': [], 'rot_angle': [], 'url': []
    })

    # Function to update flight data periodically
    def update():
        response = requests.get(url_data).json()  # Make a GET request to the API and parse the JSON response

        # Define the columns for the flight data DataFrame
        col_name = ['icao24', 'callsign', 'origin_country', 'time_position', 'last_contact', 'long', 'lat',
                    'baro_altitude', 'on_ground', 'velocity', 'true_track', 'vertical_rate', 'sensors',
                    'geo_altitude', 'squawk', 'spi', 'position_source']

        # Convert the API response to a Pandas DataFrame for easier manipulation
        flight_df = pd.DataFrame(response['states'], columns=col_name)

        # Convert latitude and longitude to Web Mercator coordinates for plotting
        wgs84_to_web_mercator(flight_df)

        # Fill missing data with 'No Data' for clean display
        flight_df = flight_df.fillna('No Data')

        # Calculate rotation angle for plotting plane icons based on true track (direction)
        flight_df['rot_angle'] = flight_df['true_track'] * -1

        # Add an icon URL for each flight (replace with actual plane icon if needed)
        icon_url = 'https://cdn-icons-png.flaticon.com/512/0/619.png'
        flight_df['url'] = icon_url

        # Stream the new flight data to the Bokeh ColumnDataSource, replacing old data
        n_roll = len(flight_df.index)
        flight_source.stream(flight_df.to_dict(orient='list'), n_roll)

    # Schedule the update function to run every 5000 milliseconds (5 seconds)
    doc.add_periodic_callback(update, 5000)

    # Create a Bokeh plot for flight tracking with Web Mercator coordinates
    p = figure(x_range=x_range, y_range=y_range, x_axis_type='mercator', y_axis_type='mercator', sizing_mode='scale_width', height=300)
    p.add_tile(Vendors.STAMEN_TERRAIN)  # Add a tile layer for terrain visualization

    # Plot flight icons (aircraft positions) as images on the map
    p.image_url(url='url', x='x', y='y', source=flight_source, anchor='center', angle_units='deg', angle='rot_angle',
                h_units='screen', w_units='screen', w=40, h=40)

    # Add scatter points for additional visual emphasis on aircraft positions
    p.scatter('x', 'y', source=flight_source, fill_color='red', hover_color='yellow', size=10, fill_alpha=0.8, line_width=0)

    # Add a hover tool to display flight details when hovering over aircraft
    my_hover = HoverTool()
    my_hover.tooltips = [('Call sign', '@callsign'), ('Origin Country', '@origin_country'), 
                         ('Velocity (m/s)', '@velocity'), ('Altitude (m)', '@baro_altitude')]
    p.add_tools(my_hover)

    # Add labels for aircraft call signs
    labels = LabelSet(x='x', y='y', text='callsign', level='glyph', x_offset=5, y_offset=5, source=flight_source,
                      background_fill_color='white', text_font_size="8pt")
    p.add_layout(labels)

    # Set the title of the document and add the plot to the Bokeh document
    doc.title = 'REAL-TIME FLIGHT TRACKING'
    doc.add_root(p)

# Set up Bokeh server to run the flight tracking app
apps = {'/': Application(FunctionHandler(flight_tracking))}
server = Server(apps, port=8084)  # Start the server on port 8084
server.start()

# Show the flight tracking app and start the server I/O loop
server.io_loop.add_callback(server.show, "/")
server.io_loop.start()

import streamlit as st
import pandas as pd
from datetime import datetime
from folium.plugins import HeatMap
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import flickrapi
import random
from dotenv import load_dotenv
import os
import urllib


load_dotenv()

# set page layout
st.set_page_config(
    page_title="Travel Exploration",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache
def load_data():
    """ Load the cleaned data with latitudes, longitudes & timestamps """
    travel_log = pd.read_csv("clean_data.csv")
    travel_log.rename(
        columns={"latitudeE71": "lat", "longitudeE71": "lon"}, inplace=True
    )
    travel_log["date"] = pd.to_datetime(travel_log["ts"])
    return travel_log


def get_pics_from_location(locations_df, size=10):
    """ Get images from flickr using the gps coordinates"""
    api_key = os.getenv("FLICKR_API_KEY")
    api_secret = os.getenv("FLICKR_API_SECRET")
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format="parsed-json")
    urls = []

    for index, row in locations_df.iterrows():
        try:
            photos = flickr.photos.search(
                lat=row["lat"], lon=row["lon"], per_page=10, pages=1
            )
            # Get a random image from the set of images
            choice_max = min(size - 1, int(photos["photos"]["total"]))
            selection = random.randint(0, choice_max)
            selected_photo = photos["photos"]["photo"][selection]

            # Compute the url for the image
            url = f"https://live.staticflickr.com/{selected_photo['server']}/{selected_photo['id']}_{selected_photo['secret']}_w.jpg"
            urls.append(url)
        except Exception as e:
            print(e)
            continue
    return urls


@st.cache(show_spinner=False)
def get_file_content_as_string(path):
    """ Download a single file and make its content available as a string"""
    url = (
        "https://raw.githubusercontent.com/nithishr/streamlit-data-viz-demo/main/"
        + path
    )
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")


st.title("🌍 Travels Exploration")

travel_data = load_data()

# Calculate the timerange for the slider
min_ts = datetime.strptime(min(travel_data["ts"]), "%Y-%m-%d %H:%M:%S.%f")
max_ts = datetime.strptime(max(travel_data["ts"]), "%Y-%m-%d %H:%M:%S.%f")

st.sidebar.subheader("Inputs")
min_selection, max_selection = st.sidebar.slider(
    "Timeline", min_value=min_ts, max_value=max_ts, value=[min_ts, max_ts]
)

# Toggles for the feature selection in sidebar
show_heatmap = st.sidebar.checkbox("Show Heatmap")
show_histograms = st.sidebar.checkbox("Show Histograms")
show_images = st.sidebar.checkbox("Show Images")
images_count = st.sidebar.number_input("Images to Show", value=10)
show_detailed_months = st.sidebar.checkbox("Show Detailed Split per Year")
show_code = st.sidebar.checkbox("Show Code")

# Filter Data based on selection
st.write(f"Filtering between {min_selection.date()} & {max_selection.date()}")
travel_data = travel_data[
    (travel_data["date"] >= min_selection) & (travel_data["date"] <= max_selection)
]
st.write(f"Data Points: {len(travel_data)}")

# Plot the GPS coordinates on the map
st.map(travel_data)

if show_histograms:
    # Plot the histograms based on the dates of data points
    years = travel_data.groupby(travel_data["date"].dt.year).count().plot(kind="bar")
    years.set_xlabel("Year of Data Points")
    hist_years = years.get_figure()
    st.pyplot(hist_years)

    months = travel_data.groupby(travel_data["date"].dt.month).count().plot(kind="bar")
    months.set_xlabel("Month of Data Points")
    hist_months = months.get_figure()
    st.pyplot(hist_months)

    hours = travel_data.groupby(travel_data["date"].dt.hour).count().plot(kind="bar")
    hours.set_xlabel("Hour of Data Points")
    hist_hours = hours.get_figure()
    st.pyplot(hist_hours)

if show_detailed_months:
    month_year = (
        travel_data.groupby([travel_data["date"].dt.year, travel_data["date"].dt.month])
        .count()
        .plot(kind="bar")
    )
    month_year.set_xlabel("Month, Year of Data Points")
    hist_month_year = month_year.get_figure()
    st.pyplot(hist_month_year)


if show_heatmap:
    # Plot the heatmap using folium. It is resource intensive!
    map_heatmap = folium.Map(location=[48.1351, 11.5820], zoom_start=11)

    # Filter the DF for columns, then remove NaNs
    heat_df = travel_data[["lat", "lon"]]
    heat_df = heat_df.dropna(axis=0, subset=["lat", "lon"])

    # List comprehension to make list of lists
    heat_data = [[row["lat"], row["lon"]] for index, row in heat_df.iterrows()]

    # Plot it on the map
    HeatMap(heat_data).add_to(map_heatmap)

    # Display the map using the community component
    folium_static(map_heatmap)


if show_images:
    # Show the images from Flickr's public images
    sample_data = travel_data.sample(n=images_count)
    urls = get_pics_from_location(sample_data, images_count)
    st.image(urls, width=200)


if show_code:
    st.code(get_file_content_as_string("travel_viz.py"))

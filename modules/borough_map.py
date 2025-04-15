import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from topojson import Topology
import pydeck as pdk
import streamlit as st

class BoroughMap:
    """
    Manages geographic borough data for London, including assignment and visualization.

    This class handles:
    - Loading and merging borough geometries from TopoJSON files.
    - Assigning boroughs to properties based on latitude/longitude.
    - Creating choropleth maps for visualizing borough-level metrics.
    """

    def __init__(self, df: pd.DataFrame, borough_folder: str = "data/london_boroughs"):
        """
        Initializes the BoroughMap with a dataset and TopoJSON folder path.

        Args:
            df (pd.DataFrame): A DataFrame with property data.
            borough_folder (str): Directory containing TopoJSON files for London boroughs.
        """
        self.df = df
        self.borough_folder = borough_folder
        self.boroughs_gdf = self._load_boroughs()

    def _load_boroughs(self) -> gpd.GeoDataFrame:
        """
        Loads and merges TopoJSON borough files into a single GeoDataFrame.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing London borough shapes with names.
        """
        gdfs = []

        for file in os.listdir(self.borough_folder):
            if file.endswith(".json"):
                path = os.path.join(self.borough_folder, file)

                with open(path) as f:
                    topo = json.load(f)

                object_names = list(topo["objects"].keys())
                if not object_names:
                    continue

                object_name = object_names[0]
                topology = Topology(topo, object_name=object_name)
                geojson = json.loads(topology.to_geojson())
                features = geojson["features"]
                gdf = gpd.GeoDataFrame.from_features(features)

                borough_name = os.path.splitext(file)[0].replace("topo_", "")
                gdf["borough"] = borough_name.title()  # Title-case it for nice display

                gdfs.append(gdf)

        if not gdfs:
            raise ValueError("No valid borough TopoJSON files found.")

        london_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

        if london_gdf.crs is None or london_gdf.crs.to_epsg() != 4326:
            london_gdf = london_gdf.set_crs("EPSG:4326", allow_override=True)

        return london_gdf

    def assign_boroughs(self) -> pd.DataFrame:
        """
        Assigns a borough to each property in the dataset based on lat/lon.

        Returns:
            pd.DataFrame: Original DataFrame with an added 'borough' column.
        """
        if not {'latitude', 'longitude'}.issubset(self.df.columns):
            raise ValueError("Input DataFrame must contain 'latitude' and 'longitude' columns.")

        geometry = [Point(xy) for xy in zip(self.df['longitude'], self.df['latitude'])]
        points_gdf = gpd.GeoDataFrame(self.df.copy(), geometry=geometry, crs="EPSG:4326")

        joined = gpd.sjoin(points_gdf, self.boroughs_gdf[['borough', 'geometry']],
                           how="left", predicate="within")

        # Return as a plain DataFrame
        result_df = pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))
        return result_df
    
    @st.fragment
    def plot_choropleth_pydeck(self, df_with_boroughs: pd.DataFrame, metric: str) -> pdk.Deck:
        """
        Generates a choropleth map of boroughs colored by a selected metric.

        Args:
            df_with_boroughs (pd.DataFrame): A DataFrame containing a 'borough' column.
            metric (str): One of several supported metrics (e.g., "Count", "Avg. Size").

        Returns:
            pydeck.Deck: A rendered choropleth map layer for Streamlit.
        """
        # Compute the selected metric per borough
        if metric == "Count":
            borough_stats = (df_with_boroughs.groupby("borough")["fullAddress"].nunique().reset_index(name="value"))
        elif metric == "Avg. Estimated Price":
            borough_stats = df_with_boroughs.groupby("borough")["saleEstimate_currentPrice"].mean().reset_index(name="value")
        elif metric == "Avg. History Price":
            borough_stats = df_with_boroughs.groupby("borough")["history_price"].mean().reset_index(name="value")
        elif metric == "Avg. Size":
            borough_stats = df_with_boroughs.groupby("borough")["floorAreaSqM"].mean().reset_index(name="value")
        elif metric == "Avg. Price per m²":
            df_temp = df_with_boroughs.dropna(subset=["saleEstimate_currentPrice", "floorAreaSqM"]).copy()
            df_temp["price_per_sqm"] = df_temp["saleEstimate_currentPrice"] / df_temp["floorAreaSqM"]
            borough_stats = df_temp.groupby("borough")["price_per_sqm"].mean().reset_index(name="value")
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        # Merge metric values with the GeoDataFrame
        choropleth_gdf = self.boroughs_gdf.merge(borough_stats, on="borough", how="left")
        choropleth_gdf["value"] = choropleth_gdf["value"].fillna(0).round(0)

        # Normalize values to RGB (red-yellow gradient)
        max_val = choropleth_gdf["value"].max() or 1
        choropleth_gdf["fill_color"] = choropleth_gdf["value"].apply(
            lambda x: BoroughMap.interpolate_color(x, max_val)
        )


        # Create the GeoJsonLayer
        choropleth_layer = pdk.Layer(
            "GeoJsonLayer",
            data=choropleth_gdf.__geo_interface__,
            get_fill_color="properties.fill_color",
            get_line_color=[80, 80, 80],
            pickable=True,
            stroked=True,
            filled=True,
            extruded=False,
        )

        # Define view state
        view_state = pdk.ViewState(
            latitude=51.5074,
            longitude=-0.1278,
            zoom=9,
            pitch=0
        )

        return pdk.Deck(
            layers=[choropleth_layer],
            initial_view_state=view_state,
            tooltip={"text": "{borough}: {value}"},
            map_style="mapbox://styles/mapbox/light-v10"
        )

    @staticmethod
    def interpolate_color(x: float, max_val: float) -> list[int]:
        """
        Interpolates a color value between a beige and rust-brown scale.

        Args:
            x (float): The value to normalize.
            max_val (float): The maximum value for normalization.

        Returns:
            list[int]: RGBA color as a list of 4 integers.
        """
        start_color = [240, 224, 200]  
        end_color = [150, 90, 60] 

        ratio = min(x / max_val, 1) if max_val else 0
        color = [
            int(start_color[i] + ratio * (end_color[i] - start_color[i]))
            for i in range(3)
        ]
        return color + [180]

    def render(self) -> None:
        """
        Renders the interactive choropleth map section in Streamlit.

        This method displays:
        - A section title
        - A selectbox to choose the metric used to color boroughs
        - A PyDeck choropleth map based on the selected metric
        
        Returns:
            None.
        """
        st.markdown("### 🔥 London Property Heatmap")

        metric = st.selectbox(
            "Color boroughs by:",
            options=[
                "Count", "Avg. Estimated Price", "Avg. History Price",
                "Avg. Size", "Avg. Price per m²"
            ],
            index=0,
            key="choropleth_metric_selector"
        )

        deck = self.plot_choropleth_pydeck(self.df, metric)
        st.pydeck_chart(deck, use_container_width=True)

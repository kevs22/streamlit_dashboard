import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from topojson import Topology
import plotly.express as px
import pydeck as pdk
import streamlit as st

class BoroughMapper:
    """
    Handles merging London borough geometries, assigning data points to boroughs,
    and generating choropleth maps.
    """

    def __init__(self, borough_folder: str):
        """
        Initialize the BoroughMapper with the path to TopoJSON files.
        """
        self.borough_folder = borough_folder
        self.boroughs_gdf = self._load_boroughs()

    def _load_boroughs(self) -> gpd.GeoDataFrame:
        """
        Loads and merges all TopoJSON borough files into a single GeoDataFrame.
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

    def assign_boroughs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assigns each row in the DataFrame to a London borough based on lat/lon.

        Args:
            df (pd.DataFrame): DataFrame with 'latitude' and 'longitude' columns.

        Returns:
            pd.DataFrame: Original DataFrame with added 'borough' column.
        """
        if not {'latitude', 'longitude'}.issubset(df.columns):
            raise ValueError("Input DataFrame must contain 'latitude' and 'longitude' columns.")

        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        points_gdf = gpd.GeoDataFrame(df.copy(), geometry=geometry, crs="EPSG:4326")

        # Use 'intersects' to include border cases
        joined = gpd.sjoin(points_gdf, self.boroughs_gdf[['borough', 'geometry']],
                           how="left", predicate="within")

        # Return as a plain DataFrame
        result_df = pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))
        return result_df
    
    def plot_choropleth_pydeck(self, df_with_boroughs: pd.DataFrame, metric: str) -> pdk.Deck:
        """
        Create a choropleth map using PyDeck (GeoJsonLayer), colored by the selected metric.

        Args:
            df_with_boroughs (pd.DataFrame): DataFrame with a 'borough' column.
            metric (str): Metric name to color the boroughs by.

        Returns:
            pydeck.Deck: Interactive choropleth map.
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
            lambda x: BoroughMapper.interpolate_color(x, max_val)
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
    def interpolate_color(x, max_val):
        # Define a soft brown-orange gradient
        start_color = [240, 224, 200]  # light beige
        end_color = [150, 90, 60]      # muted rust brown

        ratio = min(x / max_val, 1) if max_val else 0
        color = [
            int(start_color[i] + ratio * (end_color[i] - start_color[i]))
            for i in range(3)
        ]
        return color + [180]  # Add alpha

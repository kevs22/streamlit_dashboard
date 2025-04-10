import streamlit as st
import pandas as pd

@st.dialog("Property Details", width="large")
def render_property_details(row: pd.Series, GOOGLE_API_KEY: str) -> None:
    """
    Displays a detailed property modal with features, price, and location.

    This function is triggered by a Streamlit dialog and presents property
    details such as estimated price, room counts, type, and a Street View
    image along with an embedded map based on the property's coordinates.

    Args:
        row (pd.Series): A single row from the housing dataset representing the property.
        GOOGLE_API_KEY (str): A Google Maps API key used to render the Street View image.
        
    Returns:
        None.
    """
    st.header(row['fullAddress'])
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Estimated Price:** £{row['saleEstimate_currentPrice']:,.0f}")
        st.markdown(f"**Size (sqm):** {row.get('floorAreaSqM', 'nan')}")

        bedrooms = row.get("bedrooms")
        st.markdown(f"**Bedrooms:** {int(bedrooms)}" if pd.notnull(bedrooms) else "**Bedrooms:** nan")

        bathrooms = row.get("bathrooms")
        st.markdown(f"**Bathrooms:** {int(bathrooms)}" if pd.notnull(bathrooms) else "**Bathrooms:** nan")

        livingrooms = row.get("livingRooms")
        st.markdown(f"**Livingrooms:** {int(livingrooms)}" if pd.notnull(livingrooms) else "**Livingrooms:** nan")

        st.markdown(f"**Borough:** {row['borough']}")
        st.markdown(f"**Type:** {row.get('propertyType', 'nan')}")

    with col2:
        if row['latitude'] and row['longitude']:
            img_url = f"https://maps.googleapis.com/maps/api/streetview?size=400x300&location={row['latitude']},{row['longitude']}&key={GOOGLE_API_KEY}"
            st.image(img_url)

    if pd.notnull(row.get("latitude")) and pd.notnull(row.get("longitude")):
        map_df = pd.DataFrame({'lat': [row['latitude']], 'lon': [row['longitude']]})
        st.map(map_df, zoom=12)
import streamlit as st
import pandas as pd

@st.dialog("Property Details", width="large")
def render_property_details(row, GOOGLE_API_KEY):
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

    if row['latitude'] and row['longitude']:
        map_df = pd.DataFrame({'lat': [row['latitude']], 'lon': [row['longitude']]})
        st.map(map_df, zoom=12)
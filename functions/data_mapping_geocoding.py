import streamlit as st
import leafmap.foliumap as leafmap
import folium
import requests
import time
from shapely.geometry import Point
import geopandas as gpd

# Cache the geocoding results to avoid redundant API calls
@st.cache_data
def geocode_commune(commune_name, department_code):
    """
    Geocode a French commune using the Nominatim API.
    
    Parameters:
    -----------
    commune_name : str
        Name of the commune
    department_code : str
        Department code to narrow down search
        
    Returns:
    --------
    tuple
        (latitude, longitude) coordinates or None if not found
    """
    try:
        # Build the query - include the department to improve accuracy
        query = f"{commune_name}, {department_code}, France"
        
        # Make the request to Nominatim API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        
        headers = {
            "User-Agent": "RadiationDataExplorer/1.0"  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
        else:
            st.error(f"Could not geocode: {query}")
            return None
        
    except Exception as e:
        st.error(f"Error geocoding {commune_name}: {e}")
        return None

def create_commune_geodataframe(df):
    """
    Create a GeoDataFrame with geometry points for each commune.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing commune data
        
    Returns:
    --------
    geopandas.GeoDataFrame
        GeoDataFrame with Point geometry for each commune
    """
    # Create empty lists for coordinates
    geometries = []
    valid_indices = []
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(df)
    for i, (_, row) in enumerate(df.iterrows()):
        commune = row['Commune']
        dept = row['Département']
        
        # Update progress
        progress = int((i + 1) / total * 100)
        progress_bar.progress(progress)
        status_text.text(f"Geocoding: {commune} ({i+1}/{total})")
        
        # Get coordinates
        coords = geocode_commune(commune, dept)
        
        if coords:
            geometries.append(Point(coords[1], coords[0]))  # lon, lat
            valid_indices.append(i)
        else:
            # If geocoding fails, skip this commune
            continue
        
        # Sleep briefly to avoid overwhelming the API
        time.sleep(0.1)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Create GeoDataFrame from valid entries
    gdf = gpd.GeoDataFrame(
        df.iloc[valid_indices].copy(), 
        geometry=geometries,
        crs="EPSG:4326"  # WGS84
    )
    
    return gdf
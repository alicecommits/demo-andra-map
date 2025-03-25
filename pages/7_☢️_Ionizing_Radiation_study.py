import streamlit as st
import leafmap.foliumap as leafmap
import streamlit as st
import pandas as pd
import os
import folium
from functions import data_processing, data_mapping_geocoding

st.set_page_config(
    page_icon="☢️",
    page_title="Alice's Radiation Explorer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Here the data filter

st.title("Alice's demo: Exposure of the French population to Ionization Radiation, 2021 results")
st.text("""[ENG] "In 2021, the ASNR published a report presenting an assessment of the exposure of the French population to ionizing radiation over the 2014-2019 period. Medical imaging and radon constitute the main sources of this exposure. These are followed by telluric radiation, the incorporation of natural radionuclides, cosmic radiation, and finally the industrial and military use of radioactivity, primarily through the residual fallout from atmospheric nuclear tests and the Chernobyl accident. Note: the scope of the study focuses on mainland France."
""")
with st.expander("Read in French", expanded=False):
    st.markdown("""[FR] "L’ASNR a publié en 2021 un rapport qui présente le bilan de l’exposition de la population française aux rayonnements ionisants, sur la période 2014-2019. L’imagerie médicale et le radon constituent les sources principales de cette exposition. Viennent ensuite le rayonnement tellurique, l’incorporation de radionucléides naturels, le rayonnement cosmique, et enfin l’usage industriel et militaire de la radioactivité, essentiellement via les anciennes retombées des essais nucléaires atmosphériques et de l’accident de Tchernobyl."
    Note: le périmètre de l'étude se concentre sur la France Métropolitaine.""")
    
st.info("""**Source**: [French Data Gouv API - Exposition de la population française aux rayonnements ionisants](https://www.data.gouv.fr/fr/datasets/exposition-de-la-population-francaise-aux-rayonnements-ionisants/)""")

# --- Main App constants ---
# Specify the path to the CSV file
CSV_PATH = "data/communes.csv"
CSV_PATH_DEMO = "data/communes_samples.csv"

# --- Demo mode ON/OFF feature ---
# Initialize to True (demo mode ON by default) to avoid loading >35,000 datapoints
if "is_demo" not in st.session_state:
    st.session_state.is_demo = True
def toggle_demo_mode():
    # Toggle the value
    st.session_state.is_demo = not st.session_state.is_demo
    
    # Clear any cached geodata when switching modes
    for key in list(st.session_state.keys()):
        if key.startswith('gdf_'):
            del st.session_state[key]


# --- Main Application ---
def main():
    # ----------------------- App State Management (similar to React Hooks)
    # Initialize session state for table selection if it doesn't exist
    if "radiation_table_selected_rows" not in st.session_state:
        st.session_state.radiation_table_selected_rows = []   
    # Track selected departments to detect changes
    if "selected_departments" not in st.session_state:
        st.session_state.selected_departments = []

    # ----------------------- Load and process data
    if os.path.exists(CSV_PATH) and not st.session_state.is_demo:
        df = data_processing.load_and_process_data(CSV_PATH)
    elif os.path.exists(CSV_PATH_DEMO) and st.session_state.is_demo:
        st.warning(f"Demo mode activated, will use communes_sample demo data")
        df = data_processing.load_and_process_data(CSV_PATH_DEMO)
    else:
        st.error(f"CSV file not found at {CSV_PATH}. Please check the file path. Will use fallback hardcoded data instead.")
        fallback_data = """code_insee;nom_commune;code_departement;dose_rayonnements_telluriques;dose_rayonnements_cosmiques;dose_radon_maison_individuelle;dose_radon_habitat_collectif;dose_depots_essais_atmospheriques_et_tchernobyl;;
                92071;Sceaux;92;411;306;1532;1454;9;;
                92019;Châtenay-Malabry;92;414;306;1737;1524;9;;"""
        df = data_processing.load_and_process_data(fallback_data)
        return
    
    # To avoid loading time of real geo data, turn to demo
    if st.session_state.is_demo:
        st.button("Switch to Full Dataset (⚠️ ALL >35k datapoints!)", on_click=toggle_demo_mode)
    else:
        st.button("Switch to Demo Dataset", on_click=toggle_demo_mode)
    
    # Create columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Radiation Data by Commune")

        # Add this after the columns
        with st.expander("☢️ About Radiation Data (Expand to learn more...) 🤔", expanded=False):
                st.markdown("""
                ### Understanding Radiation Measurements
                
                The data displayed in this table is sourced from the French Nuclear Safety and Radioprotection Authority (ASNR) and shows the average annual radiation exposure in **microsieverts per year** (µSv/year).
                
                **Radiation Types:**
                - 🌍 **Telluric Radiation**: Natural radiation from the Earth's crust
                - 🌌 **Cosmic Radiation**: Radiation from space reaching Earth's surface
                - 💨 **Radon Exposure**: A radioactive gas that comes from the ground
                - ☣️ **Nuclear Tests & Chernobyl**: Residual radiation from historic events
                
                For reference, a single chest X-ray exposes you to approximately 100 µSv.
                """)
        filtered_df, selected_row, show_all, selected_departments = data_processing.create_interactive_table(df)
    
    with col2:
        # Geocode communes and create map (only if we have data)
        st.subheader("Radiation Map")
        
        # Detect changes in department selection
        departments_changed = set(selected_departments) != set(st.session_state.selected_departments)
        st.session_state.selected_departments = selected_departments
        
        # Determine which data to geocode and display
        if show_all:
            # User clicked "Show All" - use the full dataset
            data_to_geocode = df
            geocode_key = 'gdf_all'
            map_title = "All Communes"
        else:
            # Use filtered data based on department selection
            data_to_geocode = filtered_df
            geocode_key = f'gdf_dept_{"-".join(str(d) for d in sorted(selected_departments))}'
            map_title = f"Communes in Department(s): {', '.join(str(d) for d in sorted(selected_departments))}"
        
        # Check if we need to geocode the data
        if geocode_key not in st.session_state or departments_changed:
            with st.spinner(f"Geocoding communes for {map_title}..."):
                gdf = data_mapping_geocoding.create_commune_geodataframe(data_to_geocode)
                st.session_state[geocode_key] = gdf
        
        # Get the appropriate GeoDataFrame from session state
        gdf = st.session_state.get(geocode_key, None)
        
        # Create and display map
        if gdf is not None and not gdf.empty:
            m = create_map_visualization(gdf, selected_row)
            m.to_streamlit(height=600)
            
            # Display information about what's being shown
            st.info(f"Showing {len(gdf)} communes on the map for {map_title}")
        else:
            st.info("Map will appear after data is processed.")

# --- Map Visualization Function ---
def create_map_visualization(gdf, selected_row=None):
    """Create a map focused on France with radiation data visualization."""
    import leafmap.foliumap as leafmap
    
    # Create a map centered on France with appropriate zoom level
    m = leafmap.Map(center=[46.603354, 1.888334], zoom=6)
    
    # Add a basemap
    m.add_basemap("OpenStreetMap")
    
    # If we have geocoded data, add it to the map
    if gdf is not None and not gdf.empty:
        # Get min/max for color scaling
        max_rad = gdf['Total Radiation (µSv/year)'].max()
        min_rad = gdf['Total Radiation (µSv/year)'].min()
        
        # Add each commune as a circle marker
        for idx, row in gdf.iterrows():
            # Calculate normalized radiation value (0-1)
            if max_rad > min_rad:
                norm_rad = (row['Total Radiation (µSv/year)'] - min_rad) / (max_rad - min_rad)
            else:
                norm_rad = 0.5
                
            # Create color based on radiation value (green to red)
            color = f'#{int(255 * norm_rad):02x}00{int(255 * (1-norm_rad)):02x}'
            
            # Create popup content
            popup_content = f"""
            <strong>{row['Commune']}</strong><br>
            Department: {row['Département']}<br>
            Total Radiation: {row['Total Radiation (µSv/year)']:.0f} µSv/year<br>
            - Telluric: {row['Telluric Radiation (µSv/year)']:.0f} µSv/year<br>
            - Cosmic: {row['Cosmic Radiation (µSv/year)']:.0f} µSv/year<br>
            - Radon (Individual): {row['Radon - Individual House (µSv/year)']:.0f} µSv/year<br>
            - Radon (Collective): {row['Radon - Collective Housing (µSv/year)']:.0f} µSv/year<br>
            - Nuclear Tests & Chernobyl: {row['Nuclear Tests & Chernobyl (µSv/year)']:.0f} µSv/year<br>
            """
            
            # Add a circle marker
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{row['Commune']}: {row['Total Radiation (µSv/year)']:.0f} µSv/year"
            ).add_to(m)
    
    # If a commune is selected, focus on it
    if selected_row is not None:
        # Get coordinates for the selected commune
        coords = data_mapping_geocoding.geocode_commune(selected_row['Commune'], str(selected_row['Département']))
        
        if coords:
            # Add a marker for the selected commune
            icon = folium.Icon(color='red', icon='star', prefix='fa')
            marker = folium.Marker(
                location=coords,
                popup=selected_row['Commune'],
                icon=icon
            )
            marker.add_to(m)
            
            # Set the map view to focus on this commune
            m.set_center(coords[0], coords[1], zoom=12)
    
    return m

# Run the app
if __name__ == "__main__":
    main()
import pandas as pd
import streamlit as st

pd.set_option('display.max_columns', None)

def load_and_process_data(csv_path):
    """
    Load and process the radiation data CSV file.
    
    Parameters:
    -----------
    csv_file : str
        Path to the CSV file
        
    Returns:
    --------
    pandas.DataFrame
        Processed DataFrame containing radiation data
    """
    # Load data with proper encoding and separator
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    
    # Drop the empty columns (the CSV has extra semicolons)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Rename columns for better readability
    column_names = {
        'code_insee': 'Code INSEE',
        'nom_commune': 'Commune',
        'code_departement': 'Département',
        'dose_rayonnements_telluriques': 'Telluric Radiation (µSv/year)',
        'dose_rayonnements_cosmiques': 'Cosmic Radiation (µSv/year)',
        'dose_radon_maison_individuelle': 'Radon - Individual House (µSv/year)',
        'dose_radon_habitat_collectif': 'Radon - Collective Housing (µSv/year)',
        'dose_depots_essais_atmospheriques_et_tchernobyl': 'Nuclear Tests & Chernobyl (µSv/year)'
    }
    df = df.rename(columns=column_names)
    
    # Convert numeric columns to proper numeric types
    numeric_cols = [col for col in df.columns if any(s in col for s in ['Radiation', 'Radon', 'Nuclear'])]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Add total radiation column
    df['Total Radiation (µSv/year)'] = df[numeric_cols].sum(axis=1)

    return df

def create_interactive_table(df):
    """
    Create an interactive table with filtering options.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Processed DataFrame containing radiation data
        
    Returns:
    --------
    pandas.DataFrame
        Filtered DataFrame based on user selections
    int
        Selected row index if a row is clicked, otherwise None
    """
    # Add filtering options in the sidebar
    st.sidebar.header("Filter per Counties (Départements)")
    
    # Department filter
    departments = sorted(df['Département'].unique())
    selected_departments = st.sidebar.multiselect(
        "Select Department(s):", 
        departments,
        default=departments[:1]  # Default to first department
    )

    # Add a "Show All" button
    show_all = st.sidebar.button("Show All Towns on Map")
    
    # Apply filters
    if selected_departments:
        filtered_df = df[df['Département'].isin(selected_departments)]
    else:
        filtered_df = df.copy()
    
    # Display the table with ability to select rows
    # Use the built-in data_editor for interactivity
    selection = st.data_editor(
    filtered_df,
    hide_index=True,
    column_config={
        "Code INSEE": st.column_config.NumberColumn(
            "Code\nINSEE", 
            width="small",
            format="%d"
        ),
        "Commune": st.column_config.TextColumn(
            "Commune", 
            width="medium"
        ),
        "Département": st.column_config.NumberColumn(
            "Dept.", 
            width="small",
            format="%d"
        ),
        "Total Radiation (µSv/year)": st.column_config.NumberColumn(
            "Total\nRadiation\n(µSv/year)",
            format="%.0f",
            width="small"
        ),
        "Telluric Radiation (µSv/year)": st.column_config.NumberColumn(
            "Telluric\nRad.\n(µSv/year)",
            format="%.0f",
            width="small"
        ),
        "Cosmic Radiation (µSv/year)": st.column_config.NumberColumn(
            "Cosmic\nRad.\n(µSv/year)",
            format="%.0f",
            width="small"
        ),
        "Radon - Individual House (µSv/year)": st.column_config.NumberColumn(
            "Radon\nIndiv.\n(µSv/year)",
            format="%.0f",
            width="small"
        ),
        "Radon - Collective Housing (µSv/year)": st.column_config.NumberColumn(
            "Radon\nCollect.\n(µSv/year)",
            format="%.0f",
            width="small"
        ),
        "Nuclear Tests & Chernobyl (µSv/year)": st.column_config.NumberColumn(
            "Nuclear\nTests\n(µSv/year)",
            format="%.0f",
            width="small"
        )
    },
    use_container_width=True,
    key="radiation_table"
)
    
    # Get the selected row
    selected_row = None
    # Check if the session state variable exists before accessing it
    if "radiation_table_selected_rows" in st.session_state and st.session_state.radiation_table_selected_rows:
        selected_indices = st.session_state.radiation_table_selected_rows
        if selected_indices:
            selected_row = filtered_df.iloc[selected_indices[0]]

    return filtered_df, selected_row, show_all, selected_departments
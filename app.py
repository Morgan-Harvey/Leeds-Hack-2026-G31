import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from utils import get_prediction, get_stations

# ---------------------------
# Load stations from backend once
# ---------------------------
@st.cache_data
def load_stations():
    return get_stations()

stations = load_stations()

# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.header("Prediction Settings")

# Text input for autocomplete-style search
station_query = st.sidebar.text_input(
    "Search Station",
    placeholder="Type station name...",
    help="Start typing to filter stations"
)

# Filter stations dynamically based on text input
if station_query:
    query = station_query.lower().strip()
    filtered_stations = [
        s for s in stations 
        if query in s.lower()
    ]
    st.sidebar.caption(f"Found {len(filtered_stations)} matching station(s)")
else:
    filtered_stations = stations[:50]
    st.sidebar.caption(f"Showing first 50 of {len(stations)} stations. Use search to find more.")

# Selectbox to pick the final station
station = st.sidebar.selectbox(
    "Select Station",
    filtered_stations,
    disabled=len(filtered_stations) == 0,
    index=0 if filtered_stations else None
)

# Warning if no stations match
if station_query and not filtered_stations:
    st.sidebar.warning("No matching stations found. Try a different search term.")

# Date input (only one day from today)
selected_date = st.sidebar.date_input(
    "Select Date", 
    datetime.today(),
    min_value=datetime.today(),
    max_value=datetime.today() + timedelta(days=1),
    help="Select today or tomorrow for prediction"
)

# Prediction button
predict_button = st.sidebar.button("🔮 Predict Congestion")

# ---------------------------
# Main content area
# ---------------------------
st.title("🚇 Station Congestion Predictor")

if predict_button:
    if not station:
        st.error("Please select a station first")
    else:
        st.subheader(f"Prediction for {station}")
        st.info(f"📅 {selected_date.strftime('%A, %B %d, %Y')}")
        
        with st.spinner(f"Predicting congestion..."):
            # Get prediction from backend (mock for now)
            prediction_result = get_prediction(
                station=station,
                date=selected_date
            )
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Congestion Level",
                    prediction_result.get('level', 'N/A'),
                    delta=prediction_result.get('change', None)
                )
            
            with col2:
                st.metric(
                    "Expected Crowd",
                    prediction_result.get('crowd_size', 'N/A'),
                    delta=prediction_result.get('vs_average', None)
                )
            
            with col3:
                st.metric(
                    "Confidence",
                    f"{prediction_result.get('confidence', 0):.0%}"
                )
            
            # Visualization
            st.subheader("📊 Hourly Congestion Pattern")
            fig, ax = plt.subplots(figsize=(12, 5))
            
            hourly_data = prediction_result['hourly_data']
            ax.plot(hourly_data['hours'], hourly_data['congestion'], 
                   marker='o', linewidth=2, markersize=6, color='#1f77b4')
            ax.fill_between(hourly_data['hours'], hourly_data['congestion'], 
                           alpha=0.3, color='#1f77b4')
            ax.set_xlabel('Hour of Day', fontsize=12)
            ax.set_ylabel('Congestion Level (%)', fontsize=12)
            ax.set_title(f"Predicted Congestion - {selected_date.strftime('%A, %B %d')}", 
                       fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            ax.set_xticks(range(0, 24, 2))
            
            st.pyplot(fig)
            
            # Peak hours information
            st.subheader("⏰ Peak Hours")
            peak_hours = prediction_result.get('peak_hours', [])
            if peak_hours:
                cols = st.columns(len(peak_hours))
                for idx, peak in enumerate(peak_hours):
                    with cols[idx]:
                        st.info(f"**{peak['time_range']}**\n\n{peak['congestion']}% congestion")
            
            # Additional details
            with st.expander("📊 Detailed Information"):
                st.write(f"**Day of Week:** {selected_date.strftime('%A')}")
                st.write(f"**Date:** {selected_date.strftime('%B %d, %Y')}")
                st.write(f"**Average Daily Congestion:** {prediction_result.get('avg_congestion', 0)}%")
                if 'factors' in prediction_result:
                    st.write("**Contributing Factors:**")
                    for factor in prediction_result['factors']:
                        st.write(f"- {factor}")

else:
    # Initial state - show instructions
    st.info("👈 Use the sidebar to configure your prediction settings and click 'Predict Congestion'")
    
    st.markdown("""
    ### How to use:
    1. **Search** for your station using the search box
    2. **Select** the station from the dropdown
    3. **Choose** a date (today or tomorrow)
    4. Click **Predict Congestion** to see the forecast
    
    The prediction includes:
    - 📊 Hourly congestion patterns throughout the day
    - 📈 Key metrics and insights
    - ⏰ Peak hours identification
    """)
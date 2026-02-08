import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import pydeck as pdk
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from utils import get_prediction, get_stations, get_forecast_for_station, get_date_range

# Helper for Home button callback
def _go_home():
    st.session_state['station_query'] = ""
    st.session_state['station_select'] = stations[0] if stations else None
    st.session_state['selected_date'] = min_date
    # Clear prediction state to return to home view
    if 'prediction_station' in st.session_state:
        del st.session_state['prediction_station']
    if 'prediction_date' in st.session_state:
        del st.session_state['prediction_date']
    st.session_state['show_forecast_details'] = False

# ---------------------------
# Load stations and date range
# ---------------------------
@st.cache_data
def load_stations():
    return get_stations()

@st.cache_data
def load_date_range():
    return get_date_range()

stations = load_stations()
min_date, max_date = load_date_range()

# Sidebar controls
# ---------------------------
if st.sidebar.button("🏠 Home", key='sidebar_home', on_click=_go_home):
    pass  # callback handles the reset

st.sidebar.header("🔍 Prediction Settings")

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
    st.sidebar.caption(f"✓ Found {len(filtered_stations)} matching station(s)")
else:
    filtered_stations = stations[:50]
    st.sidebar.caption(f"Showing first 50 of {len(stations)} stations")

# Selectbox to pick the final station
station = st.sidebar.selectbox(
    "Select Station",
    filtered_stations,
    disabled=len(filtered_stations) == 0,
    index=0 if filtered_stations else None,
    key='station_select'
)

# Warning if no stations match
if station_query and not filtered_stations:
    st.sidebar.warning("No matching stations found. Try a different search term.")

# Date input with proper date range from forecast data
selected_date = st.sidebar.date_input(
    "Select Date", 
    min_date,
    min_value=min_date,
    max_value=max_date,
    key='selected_date',
    help="Select a date between today and 7 days from now"
)

# Map schtaff

import pandas as pd
import folium
from datetime import date

# Load your CSVs
all_stations = pd.read_csv("datasets/raw/London stations.csv")
calculated_stations = pd.read_csv("notebooks/data/processed/forecast.csv")

all_stations.rename(columns={"Station": "station"}, inplace=True)
calculated_stations.rename(columns={"risk_label": "category"}, inplace=True)

# Ensure date column is datetime
calculated_stations["date"] = pd.to_datetime(calculated_stations["date"])

# Merge
df = all_stations.merge(calculated_stations, on="station", how="left")

# Filter to today's rows
today = pd.to_datetime(date.today())
df_today = df[df["date"] == today]

cat_colors = {
    "HIGH": "red",
    "MED": "yellow",
    "LOW": "green"
}

m = folium.Map(location=[51.5074, -0.1278], zoom_start=11)

# Only plot today's stations
for _, row in df_today.iterrows():
    category = row["category"]
    color = cat_colors.get(category, "grey")

    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        popup=f"{row['station']} ({category})"
    ).add_to(m)

m.save("map.html")


# Prediction button
predict_button = st.sidebar.button("🔮 Predict Congestion", use_container_width=True)

# ---------------------------
# Main content area
# ---------------------------
# st.set_page_config(layout="wide")
st.title("🚇 Station Congestion Predictor")

# Check if we should show prediction: either predict_button was clicked, or we have stored prediction state
should_show_prediction = predict_button or ('prediction_station' in st.session_state and 'prediction_date' in st.session_state)

# Determine which station/date to use
if predict_button:
    display_station = station
    display_date = selected_date
    # Store the prediction inputs so we can restore view after Back button
    st.session_state['prediction_station'] = station
    st.session_state['prediction_date'] = selected_date
else:
    display_station = st.session_state.get('prediction_station')
    display_date = st.session_state.get('prediction_date')

if should_show_prediction:
    if predict_button and not station:
        st.error("❌ Please select a station first")
    else:
        st.subheader(f"📍 {display_station}")
        st.info(f"📅 {display_date.strftime('%A, %B %d, %Y')}")
        
        with st.spinner("🔄 Predicting congestion..."):
            prediction_result = get_prediction(display_station, display_date)
            
            if 'error' in prediction_result:
                st.error(prediction_result['error'])
            else:
                # Risk Label Display with Color Coding
                risk_label = prediction_result['risk_label']
                risk_emoji = prediction_result['risk_emoji']
                reason = prediction_result['reason']
                
                # Color mapping for risk levels
                if risk_label == 'LOW':
                    risk_color = '🟢'
                    bg_color = '#d4edda'
                    text_color = '#155724'
                elif risk_label == 'MED':
                    risk_color = '🟡'
                    bg_color = '#fff3cd'
                    text_color = '#856404'
                else:  # HIGH
                    risk_color = '🔴'
                    bg_color = '#f8d7da'
                    text_color = '#721c24'
                
                # Main metrics
                col1, = st.columns(1)

                with col1:
                    st.metric(
                        "Predicted Overcrowding",
                        f"{prediction_result['level']:.1f}%",
                        delta=f"{prediction_result['delta']:.1f}%"
                    )

                
                # Risk Alert Box
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; border-left: 5px solid #000;">
                    <h2 style="color: {text_color}; margin-top: 0;">
                        {risk_emoji} Risk Level: <strong>{risk_label}</strong>
                    </h2>
                    <p style="color: {text_color}; font-size: 16px; margin: 10px 0;">
                        <strong>Why?</strong> {reason}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 7-Day Forecast Graph
                st.subheader("📊 7-Day Forecast")
                forecast_data = get_forecast_for_station(display_station)
                
                if forecast_data:

                    forecast_df = pd.DataFrame(forecast_data)
                    forecast_df['date'] = pd.to_datetime(forecast_df['date'])

                    # Create Plotly figure
                    fig = go.Figure()

                    # Add predicted line with gradient area
                    fig.add_trace(go.Scatter(
                        x=forecast_df['date'],
                        y=forecast_df['predicted_overcrowding'],
                        mode='lines+markers',
                        name='Predicted',
                        line=dict(color='#2E86DE', width=3),
                        marker=dict(size=10, symbol='circle', line=dict(color='white', width=2)),
                        fill='tozeroy',
                        fillcolor='rgba(46, 134, 222, 0.1)',
                        hovertemplate='<b>Predicted</b><br>%{y:.1f}%<br>%{x|%b %d}<extra></extra>'
                    ))

                    # Add baseline line
                    fig.add_trace(go.Scatter(
                        x=forecast_df['date'],
                        y=forecast_df['baseline_overcrowding'],
                        mode='lines+markers',
                        name='Baseline',
                        line=dict(color='#FF6B6B', width=2.5, dash='dash'),
                        marker=dict(size=8, symbol='square'),
                        hovertemplate='<b>Baseline</b><br>%{y:.1f}%<br>%{x|%b %d}<extra></extra>'
                    ))

                    # Highlight today's prediction with a larger marker
                    today_data = forecast_df[forecast_df['date'].dt.date == display_date]
                    if not today_data.empty:
                        fig.add_trace(go.Scatter(
                            x=today_data['date'],
                            y=today_data['predicted_overcrowding'],
                            mode='markers',
                            name='Today',
                            marker=dict(
                                size=18,
                                color='#FFA502',
                                line=dict(color='#2C3E50', width=3),
                                symbol='star'
                            ),
                            hovertemplate='<b>TODAY</b><br>%{y:.1f}%<extra></extra>'
                        ))

                    # Update layout with modern styling
                    fig.update_layout(
                        title={
                            'text': f"<b>7-Day Congestion Forecast</b><br><sup>{display_station}</sup>",
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': {'size': 24, 'color': '#2C3E50'}
                        },
                        xaxis=dict(
                            title='<b>Date</b>',
                            showgrid=True,
                            gridcolor='rgba(0,0,0,0.05)',
                            tickformat='%b %d',
                            tickfont=dict(size=12)
                        ),
                        yaxis=dict(
                            title='<b>Overcrowding Level (%)</b>',
                            showgrid=True,
                            gridcolor='rgba(0,0,0,0.05)',
                            range=[0, 130],
                            tickfont=dict(size=12)
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        hovermode='x unified',
                        hoverlabel=dict(
                            bgcolor="black",
                            font_size=13,
                            font_family="Arial"
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            bgcolor="rgba(255,255,255,0.8)",
                            bordercolor="#E0E0E0",
                            borderwidth=1
                        ),
                        height=550,
                        margin=dict(t=100, b=60, l=60, r=40)
                    )

                    # Display in Streamlit
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Forecast details (opened via button modal)
                    display_df = forecast_df[[
                        'date', 'predicted_overcrowding', 'baseline_overcrowding', 
                        'delta', 'risk_label', 'reason'
                    ]].copy()

                    display_df.columns = ['Date', 'Predicted (%)', 'Baseline (%)', 
                                         'Δ Change (%)', 'Risk', 'Reason']
                    display_df['Date'] = display_df['Date'].dt.strftime('%a, %b %d')

                    # Add emoji to risk column
                    risk_emoji_map = {'LOW': '🟢', 'MED': '🟡', 'HIGH': '🔴'}
                    display_df['Risk'] = display_df['Risk'].map(
                        lambda x: f"{risk_emoji_map.get(x, '⚪')} {x}"
                    )

                    st.subheader("📈 Detailed Forecast")
                    # Toggle button to show/hide detailed table
                    if st.button(
                        "🔎 Show Detailed Forecast" if not st.session_state.get('show_forecast_details') else "▼ Hide Detailed Forecast",
                        key=f"show_details_btn_{display_station}"
                    ):
                        st.session_state['show_forecast_details'] = not st.session_state.get('show_forecast_details', False)
                    
                    # Show detailed table if toggled on
                    if st.session_state.get('show_forecast_details'):
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Summary statistics
                    st.subheader("📊 Summary Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Avg Overcrowding",
                            f"{forecast_df['predicted_overcrowding'].mean():.1f}%"
                        )
                    
                    with col2:
                        st.metric(
                            "Peak Day",
                            f"{forecast_df.loc[forecast_df['predicted_overcrowding'].idxmax(), 'date'].strftime('%a')}",
                            f"{forecast_df['predicted_overcrowding'].max():.1f}%"
                        )
                    
                    with col3:
                        st.metric(
                            "Quietest Day",
                            f"{forecast_df.loc[forecast_df['predicted_overcrowding'].idxmin(), 'date'].strftime('%a')}",
                            f"{forecast_df['predicted_overcrowding'].min():.1f}%"
                        )
                    
                    with col4:
                        high_risk_count = len(forecast_df[forecast_df['risk_label'] == 'HIGH'])
                        st.metric(
                            "High Risk Days",
                            high_risk_count
                        )

if not should_show_prediction and not st.session_state.get('show_details'):
    # Initial state - show instructions only when NOT predicting and NOT viewing details
    st.info("👈 Use the sidebar to select a station and date, then click 'Predict Congestion'")
    
    st.markdown("""
    ### 📖 How to use:
    1. **🔍 Search** for your station using the search box
    2. **📍 Select** the station from the dropdown
    3. **📅 Choose** a date (between today and 7 days in the future)
    4. Click **🔮 Predict Congestion** to see the forecast
    
    ### ✨ Features:
    - **Real-time Risk Assessment**: See if a station is LOW, MEDIUM, or HIGH congestion risk
    - **7-Day Forecast**: View congestion patterns across the week
    - **Detailed Breakdown**: Understand why congestion is expected (weather, events, etc.)
    - **Comparison**: See how predictions compare to baseline levels
    """)

    # Convert color names to RGB
    color_map = {
        "red": [255, 0, 0],
        "blue": [0, 0, 255],
        "green": [0, 255, 0],
        "yellow": [255, 255, 0],
        "orange": [255, 165, 0],
        "purple": [128, 0, 128],
        "grey": [128, 128, 128],
        # Add your other colors here
    }

    # Apply colors to dataframe
    df_today['color'] = df_today['category'].apply(
        lambda cat: color_map.get(cat_colors.get(cat, "grey"), [128, 128, 128])
    )

    # Create the layer
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df_today,
        get_position='[Longitude, Latitude]',
        get_color='color',
        get_radius=200,  # Adjust size as needed
        pickable=True,
        auto_highlight=True,
    )

    # Set viewport
    view_state = pdk.ViewState(
        latitude=df_today['Latitude'].mean(),
        longitude=df_today['Longitude'].mean(),
        zoom=11,
        pitch=0,
    )

    # Render with tooltip
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style='https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
        tooltip={"text": "{station}\n{category}"}
    ))


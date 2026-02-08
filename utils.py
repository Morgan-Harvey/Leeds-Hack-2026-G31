import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Load forecast data
FORECAST_PATH = Path(__file__).parent / "notebooks/data/processed/forecast.csv"

@property
def _load_forecast_data():
    """Load forecast data from CSV"""
    return pd.read_csv(FORECAST_PATH)

def get_stations():
    """Get unique stations from forecast data"""
    df = pd.read_csv(FORECAST_PATH)
    return sorted(df['station'].unique().tolist())

def get_prediction(station, date):
    """Get prediction for a station on a specific date"""
    df = pd.read_csv(FORECAST_PATH)
    
    # Convert date to string format matching CSV
    date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
    
    # Filter data
    result = df[(df['station'] == station) & (df['date'] == date_str)]
    
    if result.empty:
        return {
            'error': f'No prediction found for {station} on {date_str}',
            'level': 'N/A',
            'crowd_size': 'N/A',
            'confidence': 0,
            'risk_label': 'N/A',
            'reason': 'No data available'
        }
    
    row = result.iloc[0]
    
    # Determine risk color
    risk_color_map = {
        'LOW': '🟢',
        'MED': '🟡',
        'HIGH': '🔴'
    }
    
    return {
        'level': row['predicted_overcrowding'],
        'crowd_size': f"{row['predicted_overcrowding']:.1f}%",
        'change': None,
        'vs_average': f"{row['delta']:.1f}%",
        'confidence': 0.85,
        'risk_label': row['risk_label'],
        'risk_emoji': risk_color_map.get(row['risk_label'], '⚪'),
        'reason': row['reason'],
        'baseline': row['baseline_overcrowding'],
        'delta': row['delta'],
        'day_of_week': row['day_of_week_code']
    }

def get_forecast_for_station(station):
    """Get 7-day forecast for a station"""
    df = pd.read_csv(FORECAST_PATH)
    result = df[df['station'] == station].sort_values('date')
    return result.to_dict('records')

def get_date_range():
    """Get valid date range for predictions"""
    df = pd.read_csv(FORECAST_PATH)
    min_date = pd.to_datetime(df['date'].min()).date()
    max_date = pd.to_datetime(df['date'].max()).date()
    return min_date, max_date
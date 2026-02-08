import requests

BACKEND_URL = "http://localhost:8000/predict"  # change later if deployed

def get_prediction(station, datetime):
    payload = {
        "station": station,
        "datetime": datetime
    }
    
    response = requests.post(BACKEND_URL, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def get_stations():
    return [
        "Leeds",
        "Bradford",
        "York",
        "Harrogate",
        "Wakefield",
        "Halifax",]
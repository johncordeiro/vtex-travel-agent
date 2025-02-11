import requests
import json
from typing import Dict, Any
import json

def get_value(event, key):
    for param in event.get('parameters', []):
        if param.get('name') == key:
            return param.get('value')
    return None

def get_city_coordinates(city_name):
    """Get the latitude and longitude coordinates for a given city name."""
    geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}"
    response = requests.get(geocoding_url)
    data = response.json()

    if 'results' in data and len(data['results']) > 0:
        city_info = data['results'][0]
        return city_info['latitude'], city_info['longitude']
    else:
        raise ValueError("City not found")

def get_temperature_at_datetime(city_name):
    """
    Get the temperature forecast for a specific city and datetime.
    """
    latitude, longitude = get_city_coordinates(city_name)

    forecast_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&"
        f"hourly=temperature_2m&timezone=auto"
    )
    response = requests.get(forecast_url)
    return response.json()

def format_temperature_data(weather_data):
    """
    Format the weather data into a more readable structure.
    Returns a dictionary with dates as keys and hourly temperatures as values.
    """
    formatted_data = {}

    # Get the hourly data
    times = weather_data.get('hourly', {}).get('time', [])
    temperatures = weather_data.get('hourly', {}).get('temperature_2m', [])

    # Get temperature unit
    temp_unit = weather_data.get('hourly_units', {}).get('temperature_2m', '°C')

    # Combine time and temperature data
    for time, temp in zip(times, temperatures):
        # Split into date and hour
        date, hour = time.split('T')
        hour = hour[:5]  # Keep only HH:MM

        # Initialize date entry if not exists
        if date not in formatted_data:
            formatted_data[date] = {'hours': {}}

        # Add temperature for this hour
        formatted_data[date]['hours'][hour] = f"{temp}{temp_unit}"

    return {
        'location': {
            'latitude': weather_data.get('latitude'),
            'longitude': weather_data.get('longitude'),
            'timezone': weather_data.get('timezone'),
            'elevation': weather_data.get('elevation')
        },
        'forecast': formatted_data
    }

def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AWS Lambda handler function for the weather skill.
    """
    actionGroup = event.get('actionGroup')
    function = event.get('function')

    city = get_value(event, "city")
    weather_data = get_temperature_at_datetime(city)
    formatted_data = format_temperature_data(weather_data)
    temperature_str = json.dumps(formatted_data)

    response_body = {
        'TEXT': {
            'body': temperature_str
        }
    }

    function_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': response_body
        }
    }

    session_attributes = event.get('sessionAttributes')
    prompt_session_attributes = event.get('promptSessionAttributes')

    action_response = {
        'messageVersion': '1.0',
        'response': function_response,
        'sessionAttributes': session_attributes,
        'promptSessionAttributes': prompt_session_attributes
    }

    return action_response
import os
import json
from typing import Dict, Any
from amadeus import Client, ResponseError

def get_value(event, key):
    """Get parameter value from event parameters."""
    for param in event.get('parameters', []):
        if param.get('name') == key:
            return param.get('value')
    return None

def init_amadeus() -> Client:
    """Initialize Amadeus client with credentials."""
    return Client(
        client_id="sa9VPQUSJ0m5RNmyaP2eEdgY1ZZMQ8At",
        client_secret="nw3rRgMxw2MAt0ah"
    )

def search_city(city_name: str) -> Dict[str, Any]:
    """
    Search for city information using Amadeus API.
    Documentation: https://developers.amadeus.com/self-service/category/destination-experiences/api-doc/city-search/api-reference
    """
    try:
        amadeus = init_amadeus()
        response = amadeus.reference_data.locations.cities.get(
            keyword=city_name
        )

        print(f"Response Data: {response.data}")
        
        if not response.data:
            return {
                'success': False,
                'error': 'No cities found matching your search'
            }
        
        # Format the response with relevant information
        cities = []
        for city in response.data:
            cities.append({
                'name': city.get('name', ''),
                'iata_code': city.get('iataCode', '')
            })
        
        return {
            'success': True,
            'cities': cities
        }
        
    except ResponseError as error:
        error_message = str(error.response.body) if hasattr(error, 'response') else str(error)
        return {
            'success': False,
            'error': f'Amadeus API error: {error_message}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error searching city: {str(e)}'
        }

def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AWS Lambda handler for the city search skill.
    
    Parameters:
    - city: Name of the city to search for
    """
    try:
        city = get_value(event, 'city')
        
        if not city:
            return {
                'statusCode': 400,
                'error': 'Missing required parameter: city'
            }
        
        result = search_city(city)
        
        if not result['success']:
            return {
                'statusCode': 404,
                'error': result['error']
            }
        
        response_body = {
            'TEXT': {
                'body': json.dumps(result.get('cities'))
            }
        }

        function_response = {
            'actionGroup': event.get('actionGroup'),
            'function': event.get('function'),
            'functionResponse': {
                'responseBody': response_body
            }
        }

        return {
            'messageVersion': '1.0',
            'response': function_response,
            'sessionAttributes': event.get('sessionAttributes'),
            'promptSessionAttributes': event.get('promptSessionAttributes')
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'error': f'Internal error: {str(e)}'
        } 
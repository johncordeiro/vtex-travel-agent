from datetime import datetime
from typing import Optional, Dict, Any
from amadeus import Client, ResponseError
import json

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

def format_flight_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    """Format flight offer data for better readability."""
    itineraries = offer['itineraries']
    price = offer['price']
    
    formatted_segments = []
    for itinerary in itineraries:
        for segment in itinerary['segments']:
            formatted_segments.append({
                'departure': {
                    'airport': segment['departure']['iataCode'],
                    'time': segment['departure']['at']
                },
                'arrival': {
                    'airport': segment['arrival']['iataCode'],
                    'time': segment['arrival']['at']
                },
                'carrier': segment['carrierCode'],
                'flight_number': segment['number'],
                'duration': segment['duration']
            })
    
    return {
        'price': {
            'total': price['total'],
            'currency': price['currency']
        },
        'segments': formatted_segments
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Search for flights using Amadeus API.
    
    Parameters:
    - origin: IATA code of origin airport
    - destination: IATA code of destination airport
    - departure_date: Departure date (YYYY-MM-DD)
    - return_date: Optional return date for round trips (YYYY-MM-DD)
    - adults: Number of adult passengers
    """
    try:
        # Extract parameters
        origin = get_value(event, 'origin')
        destination = get_value(event, 'destination')
        departure_date = get_value(event, 'departure_date')
        return_date = get_value(event, 'return_date')
        adults = int(get_value(event, 'adults') or 1)
        
        if not all([origin, destination, departure_date]):
            missing = []
            if not origin: missing.append('origin')
            if not destination: missing.append('destination')
            if not departure_date: missing.append('departure_date')
            return {
                'statusCode': 400,
                'error': f'Missing required parameters: {", ".join(missing)}'
            }
        
        # Validate dates
        departure = datetime.strptime(departure_date, '%Y-%m-%d')
        if return_date:
            return_dt = datetime.strptime(return_date, '%Y-%m-%d')
            if return_dt <= departure:
                return {
                    'statusCode': 400,
                    'error': 'Return date must be after departure date'
                }
        
        # Initialize Amadeus client
        amadeus = init_amadeus()
        
        # Search flights
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                returnDate=return_date,
                adults=adults,
                max=20  # Limit results
            )
            
            # Format response
            formatted_offers = [format_flight_offer(offer) for offer in response.data]
            
            response_body = {
                'TEXT': {
                    'body': json.dumps(formatted_offers)
                }
            }

            function_response = {
                'actionGroup': event.get('actionGroup'),
                'function': event.get('function'),
                'functionResponse': {
                    'responseBody': response_body
                }
            }

            response = {
                'messageVersion': '1.0',
                'response': function_response,
                'sessionAttributes': event.get('sessionAttributes'),
                'promptSessionAttributes': event.get('promptSessionAttributes')
            }

            print(f"Lambda response: {response}")
            return response
            
        except ResponseError as error:
            return {
                'statusCode': error.response.status_code,
                'error': error.response.body
            }
            
    except ValueError as e:
        return {
            'statusCode': 400,
            'error': f'Invalid date format: {str(e)}'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'error': f'Internal error: {str(e)}'
        } 
import os
from datetime import datetime
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

def safe_get(data: Dict[str, Any], *keys, default=None) -> Any:
    """Safely get nested dictionary values."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, default)
        if data is None:
            return default
    return data

def format_hotel_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    """Format hotel offer data for better readability."""
    try:
        # Extract main components with safe defaults
        hotel = safe_get(offer, 'hotel', default={})
        offers = safe_get(offer, 'offers', default=[])
        
        # Build the formatted offer with safe getters
        formatted_offer = {
            'hotel': {
                'name': safe_get(hotel, 'name', default='Unknown Hotel'),
                'chainCode': safe_get(hotel, 'chainCode', default=''),
                'rating': safe_get(hotel, 'rating', default=''),
                'description': safe_get(hotel, 'description', default=''),
                'amenities': safe_get(hotel, 'amenities', default=[]),
                'location': {
                    'latitude': safe_get(hotel, 'latitude', default=''),
                    'longitude': safe_get(hotel, 'longitude', default='')
                },
                'contact': {
                    'phone': safe_get(hotel, 'contact', 'phone', default=''),
                    'email': safe_get(hotel, 'contact', 'email', default='')
                }
            },
            'offers': []
        }

        # Add address if available
        address = safe_get(hotel, 'address', default={})
        if address:
            formatted_offer['hotel']['address'] = {
                'street': safe_get(address, 'lines', default=[''])[0],
                'city': safe_get(address, 'cityName', default=''),
                'postal_code': safe_get(address, 'postalCode', default=''),
                'country': safe_get(address, 'countryCode', default='')
            }
        
        # Process each offer
        for offer_details in offers:
            formatted_offer['offers'].append({
                'id': safe_get(offer_details, 'id', default=''),
                'price': {
                    'total': safe_get(offer_details, 'price', 'total', default='0'),
                    'currency': safe_get(offer_details, 'price', 'currency', default='USD')
                },
                'room': {
                    'type': safe_get(offer_details, 'room', 'type', default='Standard'),
                    'description': safe_get(offer_details, 'room', 'description', default=''),
                    'bed_type': safe_get(offer_details, 'room', 'bedType', default='')
                },
                'guests': {
                    'adults': safe_get(offer_details, 'guests', 'adults', default=1)
                },
                'policies': safe_get(offer_details, 'policies', default={}),
                'cancellation': safe_get(offer_details, 'cancellation', default={})
            })
        
        return formatted_offer
    except Exception as e:
        print(f"Error formatting hotel offer: {str(e)}")
        print(f"Original offer data: {offer}")
        # Return a minimal valid structure instead of raising an error
        return {
            'hotel': {
                'name': safe_get(offer, 'hotel', 'name', default='Unknown Hotel'),
                'error': f'Error formatting hotel data: {str(e)}'
            },
            'offers': []
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Search for hotels using Amadeus API.
    
    Parameters:
    - city_code: IATA code of the city
    - check_in: Check-in date (YYYY-MM-DD)
    - check_out: Check-out date (YYYY-MM-DD)
    - adults: Number of adult guests
    - radius: Search radius in KM from city center (optional)
    """
    try:
        # Extract parameters
        city_code = get_value(event, 'city_code')
        check_in = get_value(event, 'check_in')
        check_out = get_value(event, 'check_out')
        adults = int(get_value(event, 'adults') or 1)
        radius = int(get_value(event, 'radius') or 5)
        
        if not all([city_code, check_in, check_out]):
            missing = []
            if not city_code: missing.append('city_code')
            if not check_in: missing.append('check_in')
            if not check_out: missing.append('check_out')
            return {
                'statusCode': 400,
                'error': f'Missing required parameters: {", ".join(missing)}'
            }
        
        # Validate dates
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        if check_out_date <= check_in_date:
            return {
                'statusCode': 400,
                'error': 'Check-out date must be after check-in date'
            }
        
        # Initialize Amadeus client
        amadeus = init_amadeus()
        
        try:
            # First, get hotel list by city
            hotel_list = amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=city_code,
                radius=radius,
                radiusUnit='KM'
            )
            
            if not hotel_list.data:
                return {
                    'statusCode': 404,
                    'error': 'No hotels found in the specified location'
                }
            
            # Get hotel IDs
            hotel_ids = [hotel['hotelId'] for hotel in hotel_list.data[:20]]  # Limit to 20 hotels
            
            # Search hotel offers
            response = amadeus.shopping.hotel_offers_search.get(
                hotelIds=hotel_ids,
                checkInDate=check_in,
                checkOutDate=check_out,
                adults=adults
            )
            
            if not response.data:
                return {
                    'statusCode': 404,
                    'error': 'No hotel offers found for the specified criteria'
                }
            
            # Format response
            formatted_offers = [format_hotel_offer(offer) for offer in response.data]
            
            response_body = {
                'TEXT': {
                    'body': formatted_offers
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
            
        except ResponseError as error:
            error_message = str(error.response.body) if hasattr(error, 'response') else str(error)
            return {
                'statusCode': getattr(error, 'code', 500),
                'error': f'Amadeus API error: {error_message}'
            }
            
    except ValueError as e:
        return {
            'statusCode': 400,
            'error': f'Invalid date format: {str(e)}'
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'error': f'Internal error: {str(e)}'
        } 
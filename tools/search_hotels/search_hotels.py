import json
from datetime import datetime
from typing import Dict, Any
from amadeus import Client, ResponseError
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class SearchHotelsTool(Tool):
    
    def execute(self, context: Context) -> TextResponse:
        try:
            # Extract parameters
            city_code = context.parameters.get('city_code')
            check_in = context.parameters.get('check_in')
            check_out = context.parameters.get('check_out')
            adults = int(context.parameters.get('adults') or 1)
            radius = int(context.parameters.get('radius') or 5)
            
            if not all([city_code, check_in, check_out]):
                missing = []
                if not city_code: missing.append('city_code')
                if not check_in: missing.append('check_in')
                if not check_out: missing.append('check_out')
                return TextResponse(data={
                    'error': f'Missing required parameters: {", ".join(missing)}'
                })
            
            # Validate dates
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            if check_out_date <= check_in_date:
                return TextResponse(data={
                    'error': 'Check-out date must be after check-in date'
                })
            
            client_id = context.credentials.get("CLIENT_ID")
            client_secret = context.credentials.get("CLIENT_SECRET")
            
            # Initialize Amadeus client
            amadeus = self.init_amadeus(client_id, client_secret)
            
            try:
                # First, get hotel list by city
                hotel_list = amadeus.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code,
                    radius=radius,
                    radiusUnit='KM'
                )
                
                if not hotel_list.data:
                    return TextResponse(data={
                        'error': 'No hotels found in the specified location'
                    })
                
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
                    return TextResponse(data={
                        'error': 'No hotel offers found for the specified criteria'
                    })
                
                # Format response
                formatted_offers = [self.format_hotel_offer(offer) for offer in response.data]
                return TextResponse(data={"offers": formatted_offers})
            except ResponseError as error:
                error_message = str(error.response.body) if hasattr(error, 'response') else str(error)
                return TextResponse(data={
                    'error': f'Amadeus API error: {error_message}'
                })
                
        except ValueError as e:
            return TextResponse(data={
                'error': f'Invalid date format: {str(e)}'
            })
        except Exception as e:
            return TextResponse(data={
                'error': f'Internal error: {str(e)}'
            })
    
    def init_amadeus(self, client_id, client_secret) -> Client:
        """Initialize Amadeus client with credentials."""
        return Client(
            client_id=client_id,
            client_secret=client_secret
        )
    
    def safe_get(self, data: Dict[str, Any], *keys, default=None) -> Any:
        """Safely get nested dictionary values."""
        for key in keys:
            if not isinstance(data, dict):
                return default
            data = data.get(key, default)
            if data is None:
                return default
        return data
    
    def format_hotel_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Format hotel offer data for better readability."""
        try:
            # Extract main components with safe defaults
            hotel = self.safe_get(offer, 'hotel', default={})
            offers = self.safe_get(offer, 'offers', default=[])
            
            # Build the formatted offer with safe getters
            formatted_offer = {
                'hotel': {
                    'name': self.safe_get(hotel, 'name', default='Unknown Hotel'),
                    'chainCode': self.safe_get(hotel, 'chainCode', default=''),
                    'rating': self.safe_get(hotel, 'rating', default=''),
                    'description': self.safe_get(hotel, 'description', default=''),
                    'amenities': self.safe_get(hotel, 'amenities', default=[]),
                    'location': {
                        'latitude': self.safe_get(hotel, 'latitude', default=''),
                        'longitude': self.safe_get(hotel, 'longitude', default='')
                    },
                    'contact': {
                        'phone': self.safe_get(hotel, 'contact', 'phone', default=''),
                        'email': self.safe_get(hotel, 'contact', 'email', default='')
                    }
                },
                'offers': []
            }

            # Add address if available
            address = self.safe_get(hotel, 'address', default={})
            if address:
                formatted_offer['hotel']['address'] = {
                    'street': self.safe_get(address, 'lines', default=[''])[0],
                    'city': self.safe_get(address, 'cityName', default=''),
                    'postal_code': self.safe_get(address, 'postalCode', default=''),
                    'country': self.safe_get(address, 'countryCode', default='')
                }
            
            # Process each offer
            for offer_details in offers:
                formatted_offer['offers'].append({
                    'id': self.safe_get(offer_details, 'id', default=''),
                    'price': {
                        'total': self.safe_get(offer_details, 'price', 'total', default='0'),
                        'currency': self.safe_get(offer_details, 'price', 'currency', default='USD')
                    },
                    'room': {
                        'type': self.safe_get(offer_details, 'room', 'type', default='Standard'),
                        'description': self.safe_get(offer_details, 'room', 'description', default=''),
                        'bed_type': self.safe_get(offer_details, 'room', 'bedType', default='')
                    },
                    'guests': {
                        'adults': self.safe_get(offer_details, 'guests', 'adults', default=1)
                    },
                    'policies': self.safe_get(offer_details, 'policies', default={}),
                    'cancellation': self.safe_get(offer_details, 'cancellation', default={})
                })
            
            return formatted_offer
        except Exception as e:
            print(f"Error formatting hotel offer: {str(e)}")
            print(f"Original offer data: {offer}")
            # Return a minimal valid structure instead of raising an error
            return {
                'hotel': {
                    'name': self.safe_get(offer, 'hotel', 'name', default='Unknown Hotel'),
                    'error': f'Error formatting hotel data: {str(e)}'
                },
                'offers': []
            } 
from datetime import datetime
from typing import Optional, Dict, Any
from amadeus import Client, ResponseError
import json
from weni import Skill
from weni.context import Context
from weni.responses import TextResponse

class SearchFlightsSkill(Skill):
    
    def execute(self, context: Context) -> TextResponse:
        try:
            # Extract parameters
            origin = context.parameters.get('origin')
            destination = context.parameters.get('destination')
            departure_date = context.parameters.get('departure_date')
            return_date = context.parameters.get('return_date')
            adults = int(context.parameters.get('adults') or 1)
            
            if not all([origin, destination, departure_date]):
                missing = []
                if not origin: missing.append('origin')
                if not destination: missing.append('destination')
                if not departure_date: missing.append('departure_date')
                return TextResponse(data={
                    'error': f'Missing required parameters: {", ".join(missing)}'
                })
            
            # Validate dates
            departure = datetime.strptime(departure_date, '%Y-%m-%d')
            if return_date:
                return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                if return_dt <= departure:
                    return TextResponse(data={
                        'error': 'Return date must be after departure date'
                    })
            
            client_id = context.credentials.get("CLIENT_ID")
            client_secret = context.credentials.get("CLIENT_SECRET")

            # Initialize Amadeus client
            amadeus = self.init_amadeus(client_id, client_secret)
            
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
                formatted_offers = [self.format_flight_offer(offer) for offer in response.data]
                return TextResponse(data={'offers': formatted_offers})
            except ResponseError as error:
                return TextResponse(data={
                    'error': error.response.body
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

    def format_flight_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
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
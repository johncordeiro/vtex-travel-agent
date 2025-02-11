from datetime import datetime, timedelta
import json
from skills.search_flights.search_flights import lambda_handler as search_flights
from skills.search_hotels.search_hotels import lambda_handler as search_hotels

def create_test_event(parameters):
    """Create a test event with the given parameters."""
    return {
        'actionGroup': 'travel_agent',
        'function': 'test',
        'parameters': [
            {'name': key, 'value': value}
            for key, value in parameters.items()
        ],
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    }

def print_response(title, response):
    """Pretty print the response."""
    print(f"\n{'='*20} {title} {'='*20}")
    
    # Check if response contains error
    if 'error' in response:
        print("\nERROR RESPONSE:")
        print(f"Status Code: {response.get('statusCode', 'Unknown')}")
        print(f"Error Message: {response.get('error', 'Unknown error')}")
    else:
        try:
            # Try to extract the actual hotel/flight data from the response
            if 'response' in response and 'functionResponse' in response['response']:
                response_body = response['response']['functionResponse']['responseBody']
                if 'TEXT' in response_body:
                    data = response_body['TEXT']['body']
                    print("\nSUCCESS RESPONSE:")
                    print(json.dumps(data, indent=2))
                else:
                    print("\nUnexpected response format:")
                    print(json.dumps(response, indent=2))
            else:
                print("\nRaw response:")
                print(json.dumps(response, indent=2))
        except Exception as e:
            print(f"\nError formatting response: {str(e)}")
            print("Raw response:")
            print(json.dumps(response, indent=2))
    
    print(f"\n{'='*50}")

def test_flight_search():
    """Test flight search with sample data."""
    # Get dates for testing
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    test_cases = [
        {
            'title': "Round-trip Flight Search (GRU <-> CDG)",
            'params': {
                'origin': 'MCZ',
                'destination': 'JFK',
                'departure_date': "2025-03-18",
                'return_date': "2025-03-25",
                'adults': '2'
            }
        }
    ]

    for test_case in test_cases:
        try:
            event = create_test_event(test_case['params'])
            response = search_flights(event, None)
            print_response(test_case['title'], response)
        except Exception as e:
            print(f"\nError in {test_case['title']}: {str(e)}")

def test_hotel_search():
    """Test hotel search with sample data."""
    # Get dates for testing
    check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    check_out = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')

    test_cases = [
        {
            'title': "Hotel Search in Paris",
            'params': {
                'city_code': 'PAR',
                'check_in': check_in,
                'check_out': check_out,
                'adults': '2',
                'radius': '5'
            }
        },
        {
            'title': "Hotel Search in New York",
            'params': {
                'city_code': 'NYC',
                'check_in': check_in,
                'check_out': check_out,
                'adults': '1',
                'radius': '10'
            }
        },
        {
            'title': "Hotel Search in London",
            'params': {
                'city_code': 'LON',
                'check_in': check_in,
                'check_out': check_out,
                'adults': '2',
                'radius': '3'
            }
        }
    ]

    for test_case in test_cases:
        try:
            event = create_test_event(test_case['params'])
            response = search_hotels(event, None)
            print_response(test_case['title'], response)
        except Exception as e:
            print(f"\nError in {test_case['title']}: {str(e)}")

def main():
    """Run all tests."""
    print("\nStarting Travel Agent Tests...")
    
    print("\nTesting Flight Search...")
    try:
        test_flight_search()
    except Exception as e:
        print(f"Error in flight search: {str(e)}")
    
    print("\nTesting Hotel Search...")
    try:
        test_hotel_search()
    except Exception as e:
        print(f"Error in hotel search: {str(e)}")
    
    print("\nTests completed!")

if __name__ == "__main__":
    main() 
from skills.get_iata.get_iata import lambda_handler
import json

def create_test_event(city):
    """Create a test event with the city parameter."""
    return {
        'actionGroup': 'utility_agent',
        'function': 'get_iata',
        'parameters': [
            {'name': 'city', 'value': city}
        ],
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    }

def print_response(title, response):
    """Pretty print the response."""
    print(f"\n{'='*20} {title} {'='*20}")
    
    if 'error' in response:
        print("\nERROR RESPONSE:")
        print(f"Status Code: {response.get('statusCode', 'Unknown')}")
        print(f"Error Message: {response.get('error', 'Unknown error')}")
    else:
        try:
            if 'response' in response and 'functionResponse' in response['response']:
                response_body = response['response']['functionResponse']['responseBody']
                if 'TEXT' in response_body:
                    cities = response_body['TEXT']['body']
                    print("\nFound cities:")
                    for city in cities:
                        print(f"\nCity: {city['name']} ({city['iata_code']})")
                        location = []
                        if city['state']:
                            location.append(city['state'])
                        if city['country']:
                            location.append(city['country'])
                        print(f"Location: {', '.join(location)}")
                        print(f"Timezone offset: {city['timezone']}")
                        if city['location']['latitude'] and city['location']['longitude']:
                            print(f"Coordinates: {city['location']['latitude']}, {city['location']['longitude']}")
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

def test_city_search():
    """Test city search with various cities."""
    test_cities = [
        "London",
        "New York",
        "Paris",
        "Tokyo",
        "São Paulo",
        "Dubai",
        # Test partial names
        "San",  # Should find San Francisco, San Diego, etc.
        "Los",  # Should find Los Angeles
        # Test with accents
        "São",
        "München"
    ]

    print("\nStarting City Search Tests...")
    
    for city in test_cities:
        try:
            event = create_test_event(city)
            response = lambda_handler(event, None)
            print_response(f"City Search for '{city}'", response)
        except Exception as e:
            print(f"\nError testing {city}: {str(e)}")

if __name__ == "__main__":
    test_city_search() 
import requests
import json

def get_address(cep):
    base_url = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(base_url)

    return response.json()

def get_value(event, key):
    for param in event.get('parameters', []):
        if param.get('name') == key:
            return param.get('value')
    return None

def lambda_handler(event, context):
    actionGroup = event.get('actionGroup')
    function = event.get('function')

    cep = get_value(event, "cep")
    address_str = json.dumps(get_address(cep))

    response_body = {
        'TEXT': {
            'body': address_str
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


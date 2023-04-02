import argparse
import requests
import json

if __name__ == '__main__':
    
    # Define the command line arguments
    parser = argparse.ArgumentParser(description='Check a URL for potential threats using the Google Safe Browsing API.')
    parser.add_argument('url_to_check', type=str, help='the URL to check')
    
    # Parse the command line arguments
    args = parser.parse_args()
    
    api_key = 'AIzaSyDzJERZizEEmzTCkLoScuygU_gtCnKT2dA'
    url = f'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}'

    # Define the request body as a dictionary
    request_body = {
        'client': {
            'clientId':      'memlink-to',
            'clientVersion': '0.0.1'
        },
        'threatInfo': {
            'threatTypes':      ['MALWARE', 'SOCIAL_ENGINEERING', 'POTENTIALLY_HARMFUL_APPLICATION'],
            'platformTypes':    ['WINDOWS'],
            'threatEntryTypes': ['URL'],
            'threatEntries':    [{'url': args.url_to_check}]
        }
    }

    # Convert the request body to a JSON string
    json_data = json.dumps(request_body)

    # Make the request with the appropriate headers
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json_data)

    # Check if the request was successful and process the response
    if response.status_code == 200:
        response_data = response.json()
        # Process the response data as needed
        if not response_data:
            print("Site is safe")
        else:
            threat_matches = response_data.get('matches', [])
            for match in threat_matches:
                print(f'Site not safe, Threat type: {match["threatType"]}')
    else:
        print(f'Request failed with status code {response.status_code}')

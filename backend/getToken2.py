import os
import json
import urllib3

http = None
client_id = None
client_secret = None

def lambda_handler(event, context):
    global http
    global client_id
    global client_secret

    #print(f"event: {event}", f"context: {context}")

    if 'queryStringParameters' not in event or 'code' not in event['queryStringParameters']:
        return {
            'statusCode': 400,
            'body': 'No code sent'
        }

    code = event['queryStringParameters']['code']
    if len(code) != 36:
        return {
            'statusCode': 400,
            'body': f'Wrong code: {code[:40]}'
        }
    #print(f"Calling Cognito oath/token")

    if http is None:
        if "CLIENT_ID" not in os.environ or "CLIENT_SECRET" not in os.environ:
            return {
                'statusCode': 400,
                'body': 'App unconfigured'
            }
        client_id = os.environ["CLIENT_ID"]
        client_secret = os.environ["CLIENT_SECRET"]
        http = urllib3.PoolManager()

    req_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    req_headers.update(urllib3.util.make_headers(basic_auth = f'{client_id}:{client_secret}'))
    redirect_uri = "https://lore-poc.pwlkrz.people.aws.dev/ai/token"

    resp = http.request('POST', f"https://lore-poc.auth.us-east-2.amazoncognito.com/oauth2/token?grant_type=authorization_code&client_id={client_id}&scope=email&redirect_uri={redirect_uri}&code={code}",
                        headers=req_headers)
    #print(f"response {resp.status}")
    if resp.status != 200:
        return {
            'statusCode': 403,
            'body': f'Authz error: {resp.status} {resp.data[:127]}'
        }
    resp_json = json.loads(resp.data.decode('utf-8'))
    if 'access_token' not in resp_json or 'refresh_token' not in resp_json:
        print(f'{{"error": "Cognito error", "error_details": "{resp.status} {resp_json}"}}')
        return {
            'statusCode': 403,
            'body': f'Not authorized by Cognito {resp_json}'
        }

    access_token = resp_json['access_token']

    headers = {
        'Set-Cookie': f'bearer={access_token}; Max-Age=86400; Path=/; SameSite=Lax; Secure; HttpOnly',
        'Location': 'https://lore-poc.pwlkrz.people.aws.dev/ai/index.html'
    }

    return {
        'statusCode': 302,
        'headers' : headers
    }

import os
import json
import time
import cffi
import urllib.request
from jose import jwk, jwt
from jose.utils import base64url_decode

is_cold_start = True
keys = {}
issuer = os.getenv('Issuer', None)
audience = os.getenv('Audience', None)


def validate_token(token):
    global keys, is_cold_start, issuer, audience
    if is_cold_start:
        keys_url = f'{issuer}/.well-known/jwks.json'
        with urllib.request.urlopen(keys_url) as f:
            response = f.read()
        keys = json.loads(response.decode('utf-8'))['keys']
        is_cold_start = False

    #token_parts = len(str(token.split(".")))
    #if token_parts != 3:
    #    print(f'Wrong token format {token_parts} dots')
    #    return False

    print(token)

    # get the kid from the headers prior to verification
    headers = jwt.get_unverified_headers(token)
    kid = headers['kid']
    # search for the kid in the downloaded public keys
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        print('Public key not found in jwks.json')
        return False
    # construct the public key
    public_key = jwk.construct(keys[key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(token).rsplit('.', 1)
    # decode the signature
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        print('Signature verification failed')
        return False
    print('Signature successfully verified')
    # since verification succeeded, you can now safely use the unverified claims
    claims = jwt.get_unverified_claims(token)

    # Additionally you can verify the token expiration
    if time.time() > claims['exp']:
        print('Token is expired')
        return False
    # and the Audience
    if claims['client_id'] != audience:
        print('Token was not issued for this audience')
        return False
    return True
    #decoded_jwt = jwt.decode(token, key=keys[key_index], audience=app_client_id)
    #return decoded_jwt

def lambda_handler(event, context):
    print(f"event: {event}")
    cookie_name = os.getenv('Cookie')
    for cookie_set in event["identitySource"]:
        for cookie in cookie_set.split(";"):
            tokens = cookie.split("=")
            print(f"token {tokens}")
            if cookie_name != tokens[0].strip() or len(tokens)<2:
                continue
            token = "=".join(tokens[1:]).strip()
            print(f"pure token {token}")
            try:
                if validate_token(token):
                    return {
                        "isAuthorized": True
                    }
            except Exception:
                pass    # just check another one
    return {
        "isAuthorized": False
    }
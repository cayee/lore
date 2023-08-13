import os
import time
import boto3
import hashlib

KEY = os.getenv('TableKey')
TABLE = os.getenv('Table')
TTL_NAME = os.getenv('TTL')
TTL_TIME = int(os.getenv('TTLtime'))
VALUE_NAME = os.getenv('DataField')

COOKIE_NAME = os.getenv('Cookie')

class DDBsession:
    def get(self):
        if self.sess_id is None:
            return
        self.data = self._ddb.get_item(TableName=TABLE, Key={KEY: {"S": self.sess_id}}).get("Item", {})

    def put(self):
        if self.sess_id is None:
            return
        ttl_value = int(time.time())+TTL_TIME
        update_expression = 'ADD #counter :increment SET #value = :value, #createdAt = if_not_exists(#createdAt, :now), #ttl = :ttl'
        expression_attribute_names={
            '#value': VALUE_NAME,
            '#counter': 'AccessCounter',
            '#createdAt': 'CreatedAt',
            '#ttl': TTL_NAME
        }
        expression_attribute_values={
            ':increment': {"N": str(1)},
            ':value': {"S": str(self.data)},
            ':now': {"N": str(int(time.time()))},
            ':ttl': {"N": str(ttl_value)}
        }
        self._ddb.update_item(TableName=TABLE,
                              Key={KEY: {"S": self.sess_id}},
                              ReturnValues='ALL_OLD',
                              UpdateExpression=update_expression,
                              ExpressionAttributeNames=expression_attribute_names,
                              ExpressionAttributeValues=expression_attribute_values)

    def init(self):
        self.get()

    def __init__(self):
        self.sess_id = None
        self._ddb = boto3.client(service_name="dynamodb")

# find session id
# get JWT token and use the signature as a session id
def get_session_key(event):
    if 'cookies' not in event:
        return None
    for cookie_set in event['cookies']:
        for cookie in cookie_set.split(";"):
            tokens = cookie.split("=")
            print(f"token {tokens}")
            if COOKIE_NAME != tokens[0].strip() or len(tokens)<2:
                continue
            token = "=".join(tokens[1:]).strip()
            print(f"pure token {token}")
            parts = token.split(".")
            if len(parts) != 3 or len(parts[2])<1:
                return None
            m = hashlib.sha256()
            m.update(parts[2].encode("ascii"))
            return m.hexdigest()

class DDBsessionJWT(DDBsession):
    def init(self, event):
        self.sess_id = get_session_key(event)
        super().init()
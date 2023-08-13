import os
import boto3
import time
import hashlib

KEY = os.getenv('TableKey')
TABLE = os.getenv('Table')
TTL_FIELD = os.getenv('TTL')
TTL_TIME = int(os.getenv('TTLtime'))
ANSWERS_FIELD = os.getenv('Answers')
QUESTIONS_FIELD = os.getenv('Questions')

COOKIE_NAME = os.getenv('Cookie')

class DDBsession:
    def get(self):
        if self.sess_id is None:
            return
        self.item = self._ddb.get_item(TableName=TABLE, Key={KEY: {"S": self.sess_id}}).get("Item", {})

    def put(self):
        if self.sess_id is None:
            return
        ttl_value = int(time.time())+TTL_TIME
        self.expression_attribute_values[':increment'] = {"N": "1"}
        self.expression_attribute_values[':now'] = {"N": str(time.time())}
        self.expression_attribute_values[':ttl'] = {"N": str(ttl_value)}
        self._ddb.update_item(TableName=TABLE,
                              Key={KEY: {"S": self.sess_id}},
                              ReturnValues='NONE',
                              UpdateExpression=self.update_expression,
                              ExpressionAttributeNames=self.expression_attribute_names,
                              ExpressionAttributeValues=self.expression_attribute_values)

    def init(self):
        self.get()

    def __init__(self):
        self.sess_id = None
        self._ddb = boto3.client(service_name="dynamodb")
        # set update expression
        self.update_expression = 'ADD #counter :increment SET #createdAt = if_not_exists(#createdAt, :now), #ttl = :ttl'
        self.expression_attribute_names={
            '#counter': 'AccessCounter',
            '#createdAt': 'CreatedAt',
            '#ttl': TTL_FIELD
        }
        self.expression_attribute_values={
            ':increment': {"N": str(1)}
        }

# find session id
# get JWT token and use the signature as a session id
def get_session_key(event):
    if 'cookies' not in event:
        return None
    for cookie_set in event['cookies']:
        for cookie in cookie_set.split(";"):
            tokens = cookie.split("=")
            #print(f"token {tokens}")
            if COOKIE_NAME != tokens[0].strip() or len(tokens)<2:
                continue
            token = "=".join(tokens[1:]).strip()
            #print(f"pure token {token}")
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

class ChatSession(DDBsessionJWT):
    def __init__(self):
        super().__init__()
        self.update_expression += ", #questions = list_append(if_not_exists(#questions, :empty_list), :query)"
        self.update_expression += ", #answers = list_append(if_not_exists(#answers, :empty_list), :answer)"
        self.expression_attribute_names["#questions"] = QUESTIONS_FIELD
        self.expression_attribute_names["#answers"] = ANSWERS_FIELD
        self.expression_attribute_values[':empty_list'] = {"L": []}

    def put(self, query, answer):
        self.expression_attribute_values[':query'] = {"L": [{"S": query}]}
        self.expression_attribute_values[':answer'] = {"L": [{"S": answer}]}
        super().put()

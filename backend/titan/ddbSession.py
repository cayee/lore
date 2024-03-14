import os
import json
import time
import boto3
import hashlib

from langchain.schema.messages import messages_from_dict, messages_to_dict
from langchain.memory.chat_message_histories import ChatMessageHistory

KEY = os.getenv('TableKey')
TABLE = os.getenv('Table')
TTL_FIELD = os.getenv('TTL')
TTL_TIME = int(os.getenv('TTLtime'))
ANSWERS_FIELD = os.getenv('Answers') if os.getenv('Answers') != None else "Answers"
QUESTIONS_FIELD = os.getenv('Questions') if os.getenv('Questions') != None else "Questions"
LOCATION_FIELD = os.getenv('Location') if os.getenv('Location') != None else "StoryLocation"
SUMMARY_FIELD = os.getenv('Summary') if os.getenv('Summary') != None else "Summary"
CHAT_FIELD = os.getenv('Chat')

COOKIE_NAME = os.getenv('Cookie')


class DDBsession:
    def get(self):
        if self.sess_id is None:
            return
        self.item = self._ddb.get_item(TableName=TABLE, Key={KEY: {"S": self.sess_id}},
                                       ProjectionExpression=self.projection_expression).get("Item", {})

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

    def reset(self):
        self.update_expression = 'ADD #counter :increment SET #createdAt = if_not_exists(#createdAt, :now), #ttl = :ttl'

    def __init__(self):
        self.sess_id = None
        self.item = None
        self._ddb = boto3.client(service_name="dynamodb")
        # set projection expression
        self.projection_expression = KEY
        # set update expression
        self.update_expression = 'ADD #counter :increment SET #createdAt = if_not_exists(#createdAt, :now), #ttl = :ttl'
        self.expression_attribute_names = {
            '#counter': 'AccessCounter',
            '#createdAt': 'CreatedAt',
            '#ttl': TTL_FIELD
        }
        self.expression_attribute_values = {
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
            # print(f"token {tokens}")
            if COOKIE_NAME != tokens[0].strip() or len(tokens) < 2:
                continue
            token = "=".join(tokens[1:]).strip()
            # print(f"pure token {token}")
            parts = token.split(".")
            if len(parts) != 3 or len(parts[2]) < 1:
                return None
            m = hashlib.sha256()
            m.update(parts[2].encode("ascii"))
            return m.hexdigest()


class DDBsessionJWT(DDBsession):
    def init(self, event, clientSessId):
        self.sess_id = get_session_key(event)
        self.sess_id = clientSessId if self.sess_id is None else self.sess_id+clientSessId
        super().init()


class ChatSession(DDBsessionJWT):
    def __init__(self):
        super().__init__()
        self.expression_attribute_names["#questions"] = QUESTIONS_FIELD
        self.expression_attribute_names["#answers"] = ANSWERS_FIELD
        self.projection_expression += f", {QUESTIONS_FIELD}, {ANSWERS_FIELD}"

    def reset(self, doReset):
        super().reset()
        if doReset:
            self.update_expression += ", #questions = :query"
            self.update_expression += ", #answers = :answer"
            if QUESTIONS_FIELD in self.item:
                self.item.pop(QUESTIONS_FIELD)
            if ANSWERS_FIELD in self.item:
                self.item.pop(ANSWERS_FIELD)
            if ':empty_list' in self.expression_attribute_values:
                self.expression_attribute_values.pop(':empty_list')
        else:
            self.update_expression += ", #questions = list_append(if_not_exists(#questions, :empty_list), :query)"
            self.update_expression += ", #answers = list_append(if_not_exists(#answers, :empty_list), :answer)"
            self.expression_attribute_values[':empty_list'] = {"L": []}

    def put(self, query, answers):
        self.expression_attribute_values[':query'] = {"L": [{"S": query}]}
        self.expression_attribute_values[':answer'] = {"L": [{"S": answers["answer"]}]}
        super().put()

    def load(self):
        chat_questions = self.item[QUESTIONS_FIELD]["L"] if QUESTIONS_FIELD in self.item else []
        chat_questions = [e["S"] for e in chat_questions]
        chat_answers = self.item[ANSWERS_FIELD]["L"] if ANSWERS_FIELD in self.item else []
        chat_answers = [e["S"] for e in chat_answers]
        return {"questions": chat_questions, "answers": chat_answers}


class ChatSessionLocation(ChatSession):
    def __init__(self):
        super().__init__()
        self.projection_expression += f", {LOCATION_FIELD}, {SUMMARY_FIELD}"
        self.expression_attribute_names["#location"] = LOCATION_FIELD
        self.expression_attribute_names["#summary"] = SUMMARY_FIELD
        self.update_expression += ", #location = :location, #summary = :summary"

    def reset(self, doReset):
        super().reset(doReset)
        self.update_expression += ", #location = :location, #summary = :summary"

    def put(self, query, answers, location, summary):
        self.expression_attribute_values[':location'] = {"S": location}
        self.expression_attribute_values[':summary'] = {"S": summary}
        super().put(query, answers)

    def load(self):
        qa = super().load()
        if qa is None:
            qa = {}
        qa["location"] = self.item[LOCATION_FIELD]["S"] if LOCATION_FIELD in self.item else None
        qa["summary"] = self.item[SUMMARY_FIELD]["S"] if SUMMARY_FIELD in self.item else None
        return qa

class ChatMessagesSession(ChatSession):
    def __init__(self):
        super().__init__()
        self.projection_expression += f", {CHAT_FIELD}"
        self.expression_attribute_names["#chat"] = CHAT_FIELD
        self.update_expression += ", #chat = :messages"

    def load(self):
        chat_state = self.item[CHAT_FIELD]["S"] if CHAT_FIELD in self.item else "{}"
        return ChatMessageHistory(messages=messages_from_dict(json.loads(chat_state)))

    def get(self):
        super().get()
        self.load()

    def put(self, query, answers, memory):

        self.expression_attribute_values[':messages'] = {"S": json.dumps(messages_to_dict(memory.buffer))}
        super().put(query, answers)

    def reset(self, doReset):
        super().reset(doReset)
        self.update_expression += ", #chat = :messages"

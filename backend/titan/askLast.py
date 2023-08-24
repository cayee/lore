import json
import time

from ddbSession import ChatSessionLocation

from time import sleep

is_cold_start = True
session = None


def lambda_handler(event, _):
    startTime = time.time()
    print(f"Start time: {time.time() - startTime}")
    if 'body' not in event:
        return {
            'statusCode': 400,
            'body': "Send a question, please!"
        }
    body = json.loads(event['body'])
    clientSessId = body['sessId'] if 'sessId' in body else ''
    questionId = int(body['questionId']) if 'questionId' in body else -1

    global is_cold_start, session

    if is_cold_start:
        session = ChatSessionLocation()
        is_cold_start = False

    print(f"Before session init: {time.time() - startTime}")
    session.init(event, clientSessId)

    while True:
        print(f"Before session load: {time.time() - startTime}")
        msgHistory = session.load()
        print(f"After session load: {time.time() - startTime}")
        countAnswers = len(msgHistory["answers"])
        if questionId < countAnswers:
            break
        time.sleep(1)

    resp_json = {"answers":[{
        "chatCount": countAnswers,
        "answer": msgHistory["answers"][questionId] if countAnswers > 0 else "",
        "location": msgHistory["location"] if msgHistory["location"] is not None else "Piltover plaza"
    }]}

    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }


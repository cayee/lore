import json
import time

from ddbSession import ChatSession
from ddbSession import ChatSessionLocation
from askBedrock import connectToBedrock, getDocs, call_bedrock, modelId, textGenerationConfig

is_cold_start = True
bedrock = None
vectorstores = []
session = None


def lambda_handler(event, _):
    startTime = time.time()
    print(f"Start time: {time.time() - startTime}")
    log_questions = False
    clientSessId = ''
    body = {}
    if "query" not in event:
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': "Send a question, please!"
            }
        body = json.loads(event['body'])
        if 'query' not in body:
            return {
                'statusCode': 400,
                'body': "Ask a question, please!"
            }
        query = body['query']
        if 'logQuestions' in body:
            log_questions = body['logQuestions']
        clientSessId = body['sessId'] if 'sessId' in body else ''
    else:
        query = event["query"]

    global is_cold_start, bedrock, vectorstores, session

    if is_cold_start:
        bedrock, vectorstores = connectToBedrock(["/opt/index_faiss"])
        session = ChatSessionLocation()
        is_cold_start = False

    print(f"Before session init: {time.time() - startTime}")
    session.init(event, clientSessId)
    print(f"After session init: {time.time() - startTime}")
    msgHistory = session.load()
    print(f"After session load: {time.time() - startTime}")

    if 'contextReturnNumber' not in body or body['contextReturnNumber'] == "":
        body['contextReturnNumber'] = 4
    else:
        try:
            body['contextReturnNumber'] = int(body['contextReturnNumber'])
        except:
            body['contextReturnNumber'] = 4

    if 'promptPrefix' not in body or body['promptPrefix'] == "":
        if 'loreType' in body:
            if body["loreType"] == "Default":
                body['promptPrefix'] = """You are an assistant helping Human understand the Runeterra world. Complete the following dialogue using the context provided. If the answer is not related to the context or the Runeterra world, say that you cannot answer the question. Unless specified, use around 3 sentences to answer the question. {["context":"""
            elif body["loreType"] == "First":
                body['promptPrefix'] = """You are a mysterious Bot that answers Human's questions about the Runeterra world. You usually speak in a weird, sometimes confusing manner but you still stick to the facts. Complete the following dialogue using the context provided. If the answer is not related to the context or the Runeterra world, say that you cannot answer the question. Unless specified, use around 3 sentences to answer the question. {["context":"""
            else:
                body['promptPrefix'] = """You are a strict Bot that answers Human's questions about the Runeterra world. You do not use many words and are not very talkative. Complete the following dialogue using the context provided. If the answer is not related to the context or the Runeterra world, say that you cannot answer the question. {["context":"""
        
    previousUserMessages = msgHistory["questions"] + [query]
    previousBotResponses = msgHistory["answers"] + [""]
    if msgHistory["location"] != None:
        topicList = msgHistory["location"].split(", ")
        convSubject = " or ".join(topicList)
    else:
        topicList = ""
        convSubject = ""

    if 'promptSuffix' not in body or body['promptSuffix'] == "":
        body['promptSuffix'] = f""", "dialogue":\""""
        for q, a in zip(previousUserMessages[-3:], previousBotResponses[-3:]):
            body['promptSuffix'] += " Human: " + q + " Bot: " + a

    generated_control_ans = ""
    if convSubject != "":
        generated_control_ans = call_bedrock(bedrock, """This is the conversation between Human and Bot in JSON format: {["conversation": \"""" + body["promptSuffix"][14:] + """\"]}. Does the Human's last question refer to """ + convSubject + "?")
        if generated_control_ans[-1] == '.':
            generated_control_ans = generated_control_ans[:-1]
        if generated_control_ans not in topicList or "no" in generated_control_ans.lower():
            body['contextQuestions'] = query
            convSubject = ""
    if convSubject == "":
        msgHistory["location"] = call_bedrock(bedrock, """This is the conversation between Human and Bot in JSON format: {["conversation": \"""" + body["promptSuffix"][14:] + """\"]}. Which characters, regions or events does the question '""" + query + """' refer to? List all the names.""")

    if 'contextQuestions' not in body or body['contextQuestions'] == "":
        contextQuestions = previousUserMessages if len(previousUserMessages) <= 3 else previousUserMessages [-3:]
    else:
        contextQuestions = body['contextQuestions'].split('_')

    answers = []
    for vectorstore in vectorstores:
        # Find docs
        context = ""
        doc_sources_string = []

        for q in contextQuestions:
            print(f"Before getDocs: {time.time() - startTime}")
            docs = getDocs(q, vectorstore, k=body['contextReturnNumber'])
            print(f"After getDocs: {time.time() - startTime}")
            for doc in docs:
                doc_sources_string.append(doc.metadata)
                context += doc.page_content

        if 'context' in body and body['context'] != "":
            context = body["context"]

        prompt = f"""{body['promptPrefix']} {context} {body['promptSuffix']}"""

        # first - use just a prompt
        bedrockStartTime = time.time() - startTime
        time.sleep(3)
        print(f"Before bedrock call: {bedrockStartTime}")
        generated_text = call_bedrock(bedrock, prompt)
        bedrockEndTime = time.time() - startTime
        print(f"After bedrock call: {bedrockEndTime}")
        print({"bedrockStartTime": bedrockStartTime, "bedrockEndTime": bedrockEndTime, "bedrockCallTime": bedrockEndTime - bedrockStartTime, "promptLength": len(prompt), "prompt": prompt})
        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt, "topicList": topicList, "control_ans": generated_control_ans, "location": msgHistory["location"]})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    print(f"Before session put: {time.time() - startTime}")
    print(f"expr: {session.update_expression}")
    session.reset(False)
    print(f"expr: {session.update_expression}")
    if "Sorry - this model" not in generated_text:
        session.put(query, answers, msgHistory["location"], "")
    print(f"After session put: {time.time() - startTime}")
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }


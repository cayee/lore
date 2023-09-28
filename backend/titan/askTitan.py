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
        bedrock, vectorstores = connectToBedrock([#{"index": "/opt/index_faiss", "model": "amazon.titan-e1t-medium"},
                                                  #{"index": "/opt/index_faiss_5_embv2", "model": "amazon.titan-embed-g1-text-02"},
                                                  {"index": "/opt/index_faiss_10_embv2", "model": "amazon.titan-embed-g1-text-02"}])
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
        body['promptPrefix'] = """You are a mysterious Bot that answers Human's questions about the Runeterra world. You usually speak in a weird, sometimes confusing manner but you still stick to the facts. Complete the following dialogue using the context provided. Stick to the facts provided in context. If the answer is not related to the context or the Runeterra world, say that you cannot answer the question. Unless specified, use around 3 sentences to answer the question. {["context":"""
    
    difficulty = 0
    if 'loreType' in body:
        if body["loreType"] == "First":
            difficulty = 1
        elif body["loreType"] == "Second":
            difficulty = 2
        
    previousUserMessages = msgHistory["questions"] + [query]
    previousBotResponses = msgHistory["answers"] + [""]

    qNumber = int(msgHistory["summary"]) if msgHistory["summary"] != None else 0
    if msgHistory["location"] != None:
        topicList = msgHistory["location"].split(", ")
        convSubject = " or ".join(topicList)
    else:
        msgHistory["location"] = []
        topicList = ""
        convSubject = ""

    if 'promptSuffix' not in body or body['promptSuffix'] == "":
        body['promptSuffix'] = f""", "dialogue":\""""
        for q, a in zip(previousUserMessages[-3:], previousBotResponses[-3:]):
            body['promptSuffix'] += " Human: " + q + " Bot: " + a

    generated_control_ans = ""
    if difficulty > 0:             # more advanced prompting - context cutoff
        if difficulty == 1:
            if convSubject != "":
                generated_control_ans = call_bedrock(bedrock, """This is the conversation between Human and Bot in JSON format: {["conversation": \"""" + body["promptSuffix"][14:] + """\"]}. Does the Human's last question refer to """ + convSubject + """? Answer in this JSON format: {["answer": BOOLEAN_A]}. Substitute BOOLEAN_A with a True or False.\nBOOLEAN_A = """)
                time.sleep(3)
                qNumber += 1
                if "false" in generated_control_ans.lower():
                    qNumber -= 1
                    convSubject = ""
        if convSubject == "" or difficulty == 2:
            new_location = call_bedrock(bedrock, """This is the conversation between Human and Bot in JSON format: {["conversation": \"""" + body["promptSuffix"][14:] + """\"]}. Which characters, regions or events does the question '""" + query + """' refer to? List all the names. Provide answer as follows: {['names': NAMES_A]}. Substitute NAMES_A with a list of names found. This is a JSON format.\nNAMES_A = """)
            try:
                new_location = json.loads(new_location)
            except:
                new_location = []
            qNumber += 1
            new_set = set(new_location)
            old_set = set(msgHistory["location"])
            if not (new_set & old_set): # topic actually changed
                qNumber = 1
                msgHistory["location"] = new_location
            else:
                msgHistory["location"] = new_set | old_set
    else:
        qNumber = qNumber+1 if qNumber < 3 else 3

    if 'contextQuestions' not in body or body['contextQuestions'] == "":
        contextQuestions = previousUserMessages[-qNumber:] if qNumber <= 3 else previousUserMessages [-3:]
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
                context += doc.page_content + " "

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

        generated_fact_check = ""
        first_ans = generated_text
        if difficulty > 1:         # even more advanced prompting - fact checking
            context2 = ""
            doc_sources_string2 = []
            docs2 = getDocs(generated_text, vectorstore)
            for doc in docs2:
                doc_sources_string2.append(doc.metadata)
                context2 += doc.page_content + " "
            prompt2 = """Complete the following dialogue using context provided. The dialogue is provided in a JSON format: {["context": \"""" +  context2 + """\", "dialogue": Human: '""" + generated_text + """' Is this statement correct? Answer with a 'true' or 'false'. Bot:"""
            time.sleep(5)
            bedrockStartTime2 = time.time() - startTime
            print(f"Before bedrock call 2: {bedrockStartTime2}")
            generated_fact_check = call_bedrock(bedrock, prompt2)
            bedrockEndTime2 = time.time() - startTime
            print(f"After bedrock call 2: {bedrockEndTime2}")
            if "false" in generated_fact_check.lower():
                context += "The following statement is false: " + generated_text + " "
                prompt = f"""{body['promptPrefix']} {context} {body['promptSuffix']}"""
                bedrockStartTime3 = time.time() - startTime
                time.sleep(5)
                print(f"Before bedrock call: {bedrockStartTime3}")
                generated_text = call_bedrock(bedrock, prompt)
                bedrockEndTime3 = time.time() - startTime
                print(f"After bedrock call: {bedrockEndTime3}")

        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt, "topicList": topicList, "control_ans": generated_control_ans, "location": str(msgHistory["location"]), "qNumber": str(qNumber), "first_answer": first_ans, "factCheck": generated_fact_check})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    print(f"Before session put: {time.time() - startTime}")
    print(f"expr: {session.update_expression}")
    session.reset(False)
    print(f"expr: {session.update_expression}")
    if "Sorry - this model" not in generated_text:
        session.put(query, answers[0], str(msgHistory["location"]), str(qNumber))
    print(f"After session put: {time.time() - startTime}")
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }


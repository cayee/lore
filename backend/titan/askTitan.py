import json
import time

from ddbSession import ChatMessagesSession
from askBedrock import connectToBedrock, getDocs, call_bedrock, modelId, textGenerationConfig

from langchain.llms.bedrock import Bedrock
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.vectorstores.base import VectorStoreRetriever

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
        bedrock, vectorstores = connectToBedrock(["/opt/index_faiss", "/opt/index_faiss_3"])
        session = ChatMessagesSession()
        is_cold_start = False

    print(f"Before session init: {time.time() - startTime}")
    session.init(event, clientSessId)
    print(f"After session init: {time.time() - startTime}")
    msgHistory = session.load()
    print(f"After session load: {time.time() - startTime}")
    llm = Bedrock(client=bedrock, model_id=modelId, model_kwargs=textGenerationConfig)
    print(f"After Bedrock init: {time.time() - startTime}")

    if 'contextReturnNumber' not in body or body['contextReturnNumber'] == "":
        body['contextReturnNumber'] = 4
    else:
        try:
            body['contextReturnNumber'] = int(body['contextReturnNumber'])
        except:
            body['contextReturnNumber'] = 4

    if 'promptSuffix' not in body or body['promptSuffix'] == "":
        body['promptSuffix'] = f"""Question: {query}
            Answer:"""

    if 'contextQuestions' not in body or body['contextQuestions'] == "":
        contextQuestions = [query]
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

        prompt = f"""{body['promptPrefix'] if 'promptPrefix' in body else ''}
    
        {context}
        
        {body['promptSuffix']}
        """

        # first - use just a prompt
        bedrockStartTime = time.time() - startTime
        print(f"Before bedrock call: {bedrockStartTime}")
        generated_text = call_bedrock(bedrock, prompt)
        bedrockEndTime = time.time() - startTime
        print(f"After bedrock call: {bedrockEndTime}")
        print({"bedrockStartTime": bedrockStartTime, "bedrockEndTime": bedrockEndTime, "bedrockCallTime": bedrockEndTime - bedrockStartTime, "promptLength": len(prompt), "prompt": prompt})
        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt})

    # use stored messages
    memory = ConversationBufferWindowMemory(chat_memory=msgHistory, memory_key="chat_history", return_messages=True, human_prefix="Human:", ai_prefix="Bot:")
    retriever = VectorStoreRetriever(vectorstore=vectorstores[0])
    print(f"Before ConversationalRetrievalChain from llm: {time.time() - startTime}")
    conversation_with_retrieval = ConversationalRetrievalChain.from_llm(llm, retriever, memory=memory)
    print(f"After ConversationalRetrievalChain from llm: {time.time() - startTime}")
    chat_response = conversation_with_retrieval({"question": query})
    print(f"After conversation_with_retrieval: {time.time() - startTime}")
    answers.append({"answer": chat_response['answer']})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    print(f"Before session put: {time.time() - startTime}")
    session.put(query, answers, memory)
    print(f"After session put: {time.time() - startTime}")
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }


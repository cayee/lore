import json
import os

import boto3

from ddbSession import ChatMessagesSession

from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS

from langchain.llms.bedrock import Bedrock
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.vectorstores.base import VectorStoreRetriever

is_cold_start = True
bedrock = None
vectorstores = []
session = None
modelId = "amazon.titan-tg1-large"
textGenerationConfig = {
    "maxTokenCount": 4096,
    "stopSequences": [],
    "temperature": 0.5,
    "topP": 0.2,
}


def call_bedrock(bedrock_client, prompt):
    prompt_config = {
        "inputText": prompt,
        "textGenerationConfig": textGenerationConfig
    }

    body = json.dumps(prompt_config)

    accept = "application/json"
    content_type = "application/json"

    response = bedrock_client.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=content_type
    )
    response_body = json.loads(response.get("body").read())

    results = response_body.get("results")[0].get("outputText")
    return results


def connectToBedrock():
    roleArn = os.environ["titanRoleArn"]
    sts = boto3.client('sts')

    resp = sts.assume_role(RoleArn=roleArn, RoleSessionName="TitanAccessFromLambda", DurationSeconds=3600)

    return boto3.client(aws_access_key_id=resp['Credentials']['AccessKeyId'],
                        aws_secret_access_key=resp['Credentials']['SecretAccessKey'],
                        aws_session_token=resp['Credentials']['SessionToken'],
                        service_name="bedrock",
                        region_name="us-west-2",
                        endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
                        #endpoint_url="https://bedrock.us-east-1.amazonaws.com",
                        )


def getDocs(query, vectorstore, k=4):
    docs = vectorstore.similarity_search(query, k=k)
    return docs


def lambda_handler(event, context):
    log_questions = False
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
    else:
        query = event["query"]

    global is_cold_start, bedrock, vectorstores, session

    if is_cold_start:
        bedrock = connectToBedrock()
        indexes = ["/opt/index_faiss", "/opt/index_faiss_3"]
        embeddings = BedrockEmbeddings(client=bedrock)
        vectorstores = [FAISS.load_local(index, embeddings) for index in indexes]
        session = ChatMessagesSession()
        is_cold_start = False

    session.init(event)
    msgHistory = session.load()
    llm = Bedrock(client=bedrock, model_id=modelId, model_kwargs=textGenerationConfig)

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
            docs = getDocs(q, vectorstore, k=body['contextReturnNumber'])
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
        generated_text = call_bedrock(bedrock, prompt)
        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt})

    # use stored messages
    memory = ConversationBufferWindowMemory(chat_memory=msgHistory, memory_key="chat_history", return_messages=True, human_prefix="Human:", ai_prefix="Bot:")
    retriever = VectorStoreRetriever(vectorstore=vectorstores[0])
    conversation_with_retrieval = ConversationalRetrievalChain.from_llm(llm, retriever, memory=memory)
    chat_response = conversation_with_retrieval({"question": query})
    answers.append({"answer": chat_response['answer']})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    session.put(query, answers, memory)
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }

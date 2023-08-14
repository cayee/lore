import json
import os

import boto3

from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS

from ddbSession import ChatSession

is_cold_start = True
bedrock = None
vectorstores = []
session = None

def call_bedrock(bedrock, prompt):
    prompt_config = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 8192,
            "stopSequences": [],
            "temperature": 0.5,
            "topP": 0.2,
        },
    }

    body = json.dumps(prompt_config)

    modelId = "amazon.titan-tg1-large"
    accept = "application/json"
    contentType = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())

    results = response_body.get("results")[0].get("outputText")
    return results

def connectToBedrock():
    roleArn = os.environ["titanRoleArn"]
    sts = boto3.client('sts')

    resp = sts.assume_role(RoleArn=roleArn, RoleSessionName="TitanAccessFromLambda", DurationSeconds=12*3600)

    return boto3.client(aws_access_key_id=resp['Credentials']['AccessKeyId'],
                        aws_secret_access_key=resp['Credentials']['SecretAccessKey'],
                        aws_session_token=resp['Credentials']['SessionToken'],
                        service_name="bedrock",
                        region_name="us-west-2",
                        endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
                        #endpoint_url="https://bedrock.us-east-1.amazonaws.com",
                        )

def getDocs(query, vectorstore, k=4):
    docs =  vectorstore.similarity_search(query, k=k)
    return docs

def lambda_handler(event, context):
    log_questions = False
    if not "query" in event:
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
        session = ChatSession()
        is_cold_start = False

    session.init(event)
    #print(f"Session: {session.sess_id}, {session.data}")
    #queries = query.split("_")

    if body['contextReturnNumber'] == "":
        body['contextReturnNumber'] = 4
    else:
        try:
            body['contextReturnNumber'] = int(body['contextReturnNumber'])
        except:
            body['contextReturnNumber'] = 4

    if body['promptSuffix'] == "":
        body['promptSuffix'] = f"""Question: {query}
            Answer:"""

    if body['contextQuestions'] == "":
        contextQuestions = [query]
    else:
        contextQuestions = body['contextQuestions'].split('_')

    answers = []
    for idx in range(len(vectorstores)):
        # Find docs
        context = ""
        doc_sources_string = []

        for q in contextQuestions:
            docs = getDocs(q, vectorstores[idx], k=body['contextReturnNumber'])
            for doc in docs:
                doc_sources_string.append(doc.metadata)
                context += doc.page_content

        if body['context'] != "":
            context = body["context"]

        prompt = f"""{body['promptPrefix']}
    
        {context}
        
        {body['promptSuffix']}
        """

        generated_text = call_bedrock(bedrock, prompt)
        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    #TODO - put something useful
    session.put(query, answers[0]["answer"])
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }
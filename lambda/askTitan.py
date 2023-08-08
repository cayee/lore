import json
import os

import boto3

from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS

def call_bedrock(bedrock, prompt):
    prompt_config = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 4096,
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

    resp = sts.assume_role(RoleArn=roleArn, RoleSessionName="TitanAccessFromLambda")

    bedrock = boto3.client(aws_access_key_id=resp['Credentials']['AccessKeyId'],
                           aws_secret_access_key=resp['Credentials']['SecretAccessKey'],
                           aws_session_token=resp['Credentials']['SessionToken'],
                           service_name="bedrock",
                           region_name="us-west-2",
                           endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
                           #endpoint_url="https://bedrock.us-east-1.amazonaws.com",
                           )
    return bedrock

def getDocs(query, bedrock):
    embeddings = BedrockEmbeddings()
    embeddings.client = bedrock
    vectorstore = FAISS.load_local("/opt/index_faiss", embeddings)
    return vectorstore.similarity_search(query)

def lambda_handler(event, context):

    if not "query" in event:
        if 'queryStringParameters' not in event or 'query' not in event['queryStringParameters']:
            return {
                'statusCode': 400,
                'body': "Ask a question, please!"
            }
        query = event['queryStringParameters']["query"]
    else:
        query = event["query"]


    print("query: ", query)

    queries = query.split("_")
    if len(queries) == 1:
        queries = ["Use the following pieces of context to answer the question at the end.",
                   f"""

            Question: {query}
            Answer:"""]

    bedrock = connectToBedrock()

    # Find docs
    context = ""
    doc_sources_string = ""

    for query in queries[:-2]:
        docs = getDocs(query, bedrock)
        for doc in docs:
            # doc_sources_string += doc.metadata["source"] + "\n"
            context += doc.page_content

    #prompt = f"""Use the following pieces of context to answer the question at the end.
    prompt = f"""{queries[-2]}

    {context}
    
    {queries[-1]}
    """

    generated_text = call_bedrock(bedrock, prompt)

    resp_json = {"answer": str(generated_text), "docs": doc_sources_string}
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }

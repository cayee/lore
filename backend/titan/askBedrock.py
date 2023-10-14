import os
import json
import boto3

from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS

modelId = "amazon.titan-text-express-v1"
textGenerationConfig = {
    "maxTokenCount": 8192,
    "stopSequences": [],
    "temperature": 0.0,
    "topP": 0.2,
}

def call_bedrock(bedrock_client, prompt, model = modelId):
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


def connectToBedrock(indexes):
    bedrock = boto3.client(service_name="bedrock-runtime",
                           region_name="us-west-2",
                           endpoint_url="https://prod.us-west-2.dataplane.bedrock.aws.dev"
                           )
    vectorstores = [FAISS.load_local(index["index"], BedrockEmbeddings(client=bedrock, model_id=index["model"]))
                    for index in indexes]
    return bedrock, vectorstores


def getDocs(query, vectorstore, k=4):
    docs = vectorstore.similarity_search(query, k=k)
    return docs

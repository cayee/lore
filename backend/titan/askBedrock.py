import os
import json
import boto3

from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS

modelId = "amazon.titan-tg1-xlarge"
textGenerationConfig = {
    "maxTokenCount": 3072,
    "stopSequences": [],
    "temperature": 0.0,
    "topP": 0.2,
}

#"amazon.titan-tg1-xlarge", "maxTokenCount": 8192

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
    roleArn = os.environ["titanRoleArn"]
    sts = boto3.client('sts')

    resp = sts.assume_role(RoleArn=roleArn, RoleSessionName="TitanAccessFromLambda", DurationSeconds=3600)

    bedrock = boto3.client(aws_access_key_id=resp['Credentials']['AccessKeyId'],
                           aws_secret_access_key=resp['Credentials']['SecretAccessKey'],
                           aws_session_token=resp['Credentials']['SessionToken'],
                           service_name="bedrock",
                           region_name="us-west-2",
                           endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
                           # endpoint_url="https://bedrock.us-east-1.amazonaws.com",
                           )
    vectorstores = [FAISS.load_local(index["index"], BedrockEmbeddings(client=bedrock, model_id=index["model"]))
                    for index in indexes]
    return bedrock, vectorstores


def getDocs(query, vectorstore, k=4):
    docs = vectorstore.similarity_search(query, k=k)
    return docs

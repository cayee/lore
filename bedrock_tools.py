import json

import boto3
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from transformers import Tool

bedrock = boto3.client(
    service_name="bedrock",
    region_name="us-west-2",
    endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
    #endpoint_url="https://bedrock.us-east-1.amazonaws.com",
)


def call_bedrock(prompt):
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

def get_embedding(body, modelId, accept, contentType):
    response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    embedding = response_body.get('embedding')
    return embedding

#body = json.dumps({"inputText": "explain black holes to 8th graders"})
modelId = 'amazon.titan-e1t-medium'
accept = 'application/json'
contentType = 'application/json'

class AWSWellArchTool(Tool):
    name = "well_architected_tool"
    description = "Use this tool for any AWS related question to help customers understand best practices on building on AWS. It will use the relevant context from the AWS Well-Architected Framework to answer the customer's query. The input is the customer's question. The tool returns an answer for the customer using the relevant context."
    inputs = ["text"]
    outputs = ["text"]

    def __call__(self, query):
        # Find docs
        embeddings = BedrockEmbeddings()
        embeddings.client = bedrock
        #vectorstore = FAISS.load_local("local_index", embeddings)
        vectorstore = FAISS.load_local("index_faiss", embeddings)
        docs = vectorstore.similarity_search(query)
        context = ""

        doc_sources_string = ""
        for doc in docs:
            # doc_sources_string += doc.metadata["source"] + "\n"
            context += doc.page_content

        prompt = f"""Use the following pieces of context to answer the question at the end.

        {context}

        Question: {query}
        Answer:"""

        generated_text = call_bedrock(prompt)
        print(generated_text)

        resp_json = {"ans": str(generated_text), "docs": doc_sources_string}
        return resp_json


class CodeGenerationTool(Tool):
    pass


#### Testing Well Architected Tool
# query = "How can I design secure VPCs?"
# well_arch_tool = AWSWellArchTool()
# output = well_arch_tool(query)
# print(output)


#### Testing Code Generation Tool
# query = "Write a function in Python to upload a file to Amazon S3"
# code_gen_tool = CodeGenerationTool()
# output = code_gen_tool(query)
# print(output)

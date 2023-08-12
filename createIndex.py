import json

import boto3
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.schema import Document
from transformers import Tool
import numpy as np

bedrock = boto3.client(
    service_name="bedrock",
    region_name="us-west-2",
    endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
    #endpoint_url="https://bedrock.us-east-1.amazonaws.com",
)

FILENAME = "textParts.json"

with open(FILENAME, 'r') as f:
    championInfo = json.load(f)

texts = championInfo["list"]
metadatas = championInfo["meta"]

docs = [Document(page_content=text, metadata={'link': link}) for text, link in zip(texts, metadatas)]

be = BedrockEmbeddings(client = bedrock)
#be.embed_documents(texts)

docsearch = FAISS.from_documents(docs, be)
docsearch.save_local('index_faiss')

import json

import boto3
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
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

be = BedrockEmbeddings()
be.client = bedrock
#be.embed_documents(texts)

docsearch = FAISS.from_texts(texts, be, metadatas=metadatas)
docsearch.save_local('index_faiss')

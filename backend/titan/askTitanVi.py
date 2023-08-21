import json
import os

import boto3

from ddbSession import ChatSessionReset

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
        doReset = body['resetChat'] if 'resetChat' in body else False
    else:
        query = event["query"]

    global is_cold_start, bedrock, vectorstores, session

    if is_cold_start:
        bedrock = connectToBedrock()
        indexes = ["/opt/index_faiss"]
        embeddings = BedrockEmbeddings(client=bedrock)
        vectorstores = [FAISS.load_local(index, embeddings) for index in indexes]
        session = ChatSessionReset()
        is_cold_start = False

    session.init(event, doReset)
    msgHistory = session.load()

    answers = []
    for vectorstore in vectorstores:
        # Find docs
        context = ""
        doc_sources_string = []
        
        docs = getDocs(query, vectorstore)
        for doc in docs:
            doc_sources_string.append(doc.metadata)
            context += doc.page_content

        if 'context' in body and body['context'] != "":
            context = body["context"]

        prompt = """You are playing a character named Vi. Here are some texts about Vi:
        {["texts": "This text is about Vi.  The truth, however, finally came to light when Old Hungry’s Scars—a vicious gang whose murder sprees had spread topside—were brought down by a respected sheriff of Piltover and her new ally… Vi.The former gang leader was now in the employ of the Wardens, and she had replaced the chem-powered pulverizer gauntlets with a pair of brand new hextech Atlas prototypes.This text is about Vi. ”“I can’t.”Vi tapped a finger on her chin, as if weighing whether to punch him again. She smiled, the expression worrying Devaki more than the thought of her fists.“Be a shame if word got round the Lanes that you’d been informing on all your criminal friends for the last couple of years.”“What?” said Devaki, spluttering in pain and indignation.This text is about Vi.  “That’s a lie!”“Of course it is,” said Vi, “but I know all the right people to talk to down there. A lot of folk’ll listen if I let it slip that you’re in the wardens’ pocket.”“I’ll be dead in a day if you do that,” protested Devaki.“Now you’re catching on,” said Vi. “Tell me what I want to know.Once a criminal from the mean streets of Zaun, Vi is a hotheaded, impulsive, and fearsome woman with only a very loose respect for authority figures. Growing up all but alone, Vi developed finely honed survival instincts as well as a wickedly abrasive sense of humor. Now working with the Wardens to keep the peace in Piltover, she wields mighty hextech gauntlets that can punch through walls—and suspects—with equal ease."]}
        Here is some context to the situation:
        """+ context + """
        
        Complete the following short story as Vi:       
        {["context": """

        #depending on the location
        prompt += "Rookie is a new enforcer in piltovian police force. Vi is taking him to the Ecliptic Vaults where an attempted robbery has been reported. Vi should not say where they are going or what happened there unless asked. Moreover, Vi has a feeling she knows who is responsible for it but will not share this information for now.\""


        prompt += ", \"story\": \""

        # use previous messages
        previousUserMessages = msgHistory["questions"] + [query]
        previousViResponses = msgHistory["answers"] + [""]

        for q, a in zip(previousUserMessages, previousViResponses):
            prompt += "Rookie: " + q + " Vi: " + a + " "
        
        # first - use just a prompt
        generated_text = call_bedrock(bedrock, prompt)

        # beautify the response:
        # cut everything out after the first 'Rookie' appearance
        ix = generated_text.find('Rookie:')
        if ix != -1:
            generated_text = generated_text[:ix]

        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt})

   
    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    session.put(query, answers)
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }
import json
import time

from ddbSession import ChatSessionReset
from askBedrock import connectToBedrock, getDocs, call_bedrock

is_cold_start = True
bedrock = None
vectorstores = []
session = None


def lambda_handler(event, _):
    startTime = time.time()
    print(f"Start time: {time.time() - startTime}")
    log_questions = False
    doReset = False
    body = {}
    clientSessId = ''
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
        log_questions = body['logQuestions'] if 'logQuestions' in body else False
        doReset = body['resetChat'] if 'resetChat' in body else False
        clientSessId = body['sessId'] if 'sessId' in body else ''
    else:
        query = event["query"]

    global is_cold_start, bedrock, vectorstores, session

    if is_cold_start:
        bedrock, vectorstores = connectToBedrock(["/opt/index_faiss"])
        session = ChatSessionReset()
        is_cold_start = False

    print(f"Before session init: {time.time() - startTime}")
    session.init(event, clientSessId, doReset)
    print(f"After session init: {time.time() - startTime}")
    msgHistory = session.load()
    print(f"After session load: {time.time() - startTime}")
    answers = []
    for vectorstore in vectorstores:
        # Find docs
        context = ""
        doc_sources_string = []
        
        print(f"Before getDocs: {time.time() - startTime}")
        #docs = getDocs(query, vectorstore)
        docs = getDocs("Ecliptic Vaults", vectorstore)
        for doc in docs:
            doc_sources_string.append(doc.metadata)
            context += doc.page_content

        print(f"After getDocs: {time.time() - startTime}")
        if 'context' in body and body['context'] != "":
            context = body["context"]

        prompt = """You are playing a character named Vi. Here are some texts about Vi:
        {["texts": "This text is about Vi.  The truth, however, finally came to light when Old Hungry’s Scars—a vicious gang whose murder sprees had spread topside—were brought down by a respected sheriff of Piltover and her new ally… Vi.The former gang leader was now in the employ of the Wardens, and she had replaced the chem-powered pulverizer gauntlets with a pair of brand new hextech Atlas prototypes.This text is about Vi. ”“I can’t.”Vi tapped a finger on her chin, as if weighing whether to punch him again. She smiled, the expression worrying Devaki more than the thought of her fists.“Be a shame if word got round the Lanes that you’d been informing on all your criminal friends for the last couple of years.”“What?” said Devaki, spluttering in pain and indignation.This text is about Vi.  “That’s a lie!”“Of course it is,” said Vi, “but I know all the right people to talk to down there. A lot of folk’ll listen if I let it slip that you’re in the wardens’ pocket.”“I’ll be dead in a day if you do that,” protested Devaki.“Now you’re catching on,” said Vi. “Tell me what I want to know.Once a criminal from the mean streets of Zaun, Vi is a hotheaded, impulsive, and fearsome woman with only a very loose respect for authority figures. Growing up all but alone, Vi developed finely honed survival instincts as well as a wickedly abrasive sense of humor. Now working with the Wardens to keep the peace in Piltover, she wields mighty hextech gauntlets that can punch through walls—and suspects—with equal ease."]}
        Here is some context to the situation:
        """ + context + """
        
        Complete the following short story as Vi:       
        {["context": """

        # depending on the location
        prompt += "Rookie is a new enforcer in piltovian police force. Rookie meets Vi at the plaza in Piltover. Vi was ordered to go to the Ecliptic Vaults and take Rookie with her since someone broke into the vault a few hours ago. Noone was hurt at the scene but the perpetrators could still be in the area. Vi should not say where they are going or what happened there unless asked. Moreover, Vi knows the Zaun gang 'Rawring Sparks' is responsible for the break in but will not share this information for now no matter what.\""

        prompt += ", \"story\": \""

        # use previous messages
        previousUserMessages = msgHistory["questions"] + [query]
        previousViResponses = msgHistory["answers"] + [""]

        for q, a in zip(previousUserMessages, previousViResponses):
            prompt += "Rookie: " + q + " Vi: " + a + " "
        
        # first - use just a prompt
        # beautify the response:
        bedrockStartTime = time.time() - startTime
        print(f"Before bedrock call: {bedrockStartTime}")
        generated_text = call_bedrock(bedrock, prompt)
        bedrockEndTime = time.time() - startTime
        print(f"After bedrock call: {bedrockEndTime}")
        print({"bedrockStartTime": bedrockStartTime, "bedrockEndTime": bedrockEndTime, "bedrockCallTime": bedrockEndTime - bedrockStartTime, "promptLength": len(prompt), "prompt": prompt})
        # cut everything out after the first 'Rookie' appearance
        ix = generated_text.find('Rookie:')
        if ix != -1:
            generated_text = generated_text[:ix]

        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    print(f"Before session put: {time.time() - startTime}")
    session.put(query, answers)
    print(f"After session put: {time.time() - startTime}")
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }


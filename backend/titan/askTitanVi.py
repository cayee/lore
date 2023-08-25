import json
import time

from ddbSession import ChatSessionLocation
from askBedrock import connectToBedrock, getDocs, call_bedrock

is_cold_start = True
bedrock = None
vectorstores = []
session = None


def lambda_handler(event, _):
    startTime = time.time()
    print(f"Start time: {time.time() - startTime}")
    LOCATION_1 = "Piltover plaza"
    LOCATION_2 = "Ecliptic Vaults"
    LOCATION_3 = "the Lanes"
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
        session = ChatSessionLocation()
        is_cold_start = False

    print(f"Before session init: {time.time() - startTime}")
    session.init(event, clientSessId)
    print(f"After session init: {time.time() - startTime}")
    msgHistory = session.load()
    location = msgHistory["location"] if msgHistory["location"] != None else LOCATION_1
    summary = msgHistory["summary"] if msgHistory["summary"] != None else ""
    print(f"After session load: {time.time() - startTime}")
    answers = []
    for vectorstore in vectorstores:
        # Find docs
        context = ""
        doc_sources_string = []
        
        print(f"Before getDocs: {time.time() - startTime}")
        #docs = getDocs(query, vectorstore)
        docs = getDocs(location, vectorstore)
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
        """

        promptContext = """{["context": """

        CONTEXT_SCENE_1 = "Rookie is a new enforcer trainee in piltovian police force. Vi is training him to be a real enforcer in near future. Rookie meets Vi at the plaza in Piltover. Vi was ordered to go to the Ecliptic Vaults and investigate the scene since someone broke into the vault a few hours ago. Noone was hurt at the scene but the perpetrators could still be in the area. At first, Vi doesn't want to take Rookie with her but Rookie can persuade her if they prove they are strong enough. Only when Vi agrees to take Rookie with her will she suggest going to the Ecliptic Vaults. Vi should not say where she is going or what happened there unless specifically asked for it by Rookie. Moreover, Vi knows the Zaun gang 'Rawring Sparks' is responsible for the break in but will not share this information for now no matter what.\""
        SUMMARY_SCENE_2 = """
            Rookie is a new enforcer in the Piltovian police force, and Vi has been ordered to take Rookie to the Ecliptic Vaults, which have been broken into. Vi knows the Zaun gang Rawring Sparks is responsible for the break-in, but she will not share this information. Rookie is eager to learn more about the case, but Vi is not allowed to say anything more. Vi explains that the vaults are massive and hold some of the most valuable things in Piltover and Zaun and are guarded by some of the strongest people around. Rookie and Vi then head to the Ecliptic Vaults.

            """
        CONTEXT_SCENE_2 = "Right now Rookie and Vi are at the Ecliptic Vaults. There is noone around but the main vault is in a bad shape. Vi and Rookie cannot go inside no matter what since the building is very unstable. There is a lot of junk lying around and among them there is a scrap of metal with a blue graffiti on it. Vi knows it is not Jinx's graffiti but rather Loxy's - one of the 'Rawring Sparks' gang member but will speak of it only if asked about the scrap. Vi cannot tell anything about the Rawring Sparks gang no matter what but eventually can be persuaded to say that Loxy is a part of some Zaun gang. When Rookie finds out about Loxy, Vi should suggest going to the Lanes as it is the very heart of Zaun."
        CONTEXT_SCENE_3 = "Rookie is a new enforcer in piltovian police force. Rookie meets Vi at the plaza in Piltover. Vi was ordered to go to the Ecliptic Vaults and take Rookie with her since someone broke into the vault a few hours ago. Noone was hurt at the scene but the perpetrators could still be in the area. Vi should not say where they are going or what happened there unless asked. Moreover, Vi knows the Zaun gang 'Rawring Sparks' is responsible for the break in but will not share this information for now no matter what.\""

        # depending on the location
        if location == LOCATION_1:
            promptContext += CONTEXT_SCENE_1
        elif location == LOCATION_2:
            promptContext += SUMMARY_SCENE_2
            promptContext += CONTEXT_SCENE_2 
        else:
            promptContext += CONTEXT_SCENE_3

        promptStory = ", \"story\": \""

        # use previous messages
        previousUserMessages = msgHistory["questions"] + [query]
        previousViResponses = msgHistory["answers"] + [""]

        for q, a in zip(previousUserMessages, previousViResponses):
            promptStory += "Rookie: " + q + " Vi: " + a + " "
        
        #check the region
        if location == LOCATION_1:
            region_response = call_bedrock(bedrock, f"""This is the story of Rookie and Vi with some context in JSON format: {promptContext + promptStory+'"]}'}. Are Vi and Rookie at the Ecliptic Vaults already? Answer 'Yes.' or 'No.'""")
            if region_response == "Yes.":
                location = LOCATION_2
                promptContext = """{["context": """
                promptContext += SUMMARY_SCENE_2
                promptContext += CONTEXT_SCENE_2

        elif location == LOCATION_2:
            region_response = call_bedrock(bedrock, f"""This is the story of Rookie and Vi with some context in JSON format: {promptContext + promptStory+'"]}'}. Are Vi and Rookie at the Lanes already? Answer 'Yes.' or 'No.'""")
            if region_response == "Yes.":
                location = LOCATION_3
                promptContext = """{["context": """
                promptContext += CONTEXT_SCENE_3
        else:
            region_response = call_bedrock(bedrock, f"""This is the story of Rookie and Vi with some context in JSON format: {promptContext + promptStory+'"]}'}. Are Vi and Rookie in Piltover already? Answer 'Yes.' or 'No.'""")
            if region_response == "Yes.":
                location = LOCATION_1
                promptContext = """{["context": """
                promptContext += CONTEXT_SCENE_1

        prompt += promptContext + promptStory
        # beautify the response:
        bedrockStartTime = time.time() - startTime
        print(f"Before bedrock call: {bedrockStartTime}")
        #prompt = "Rookie: " + query + " Vi: " + call_bedrock(bedrock, prompt)
        generated_text = call_bedrock(bedrock, prompt)
        bedrockEndTime = time.time() - startTime
        print(f"After bedrock call: {bedrockEndTime}")
        print({"bedrockStartTime": bedrockStartTime, "bedrockEndTime": bedrockEndTime, "bedrockCallTime": bedrockEndTime - bedrockStartTime, "promptLength": len(prompt), "prompt": prompt})
        # cut everything out after the first 'Rookie' appearance
        fullAnswer = generated_text
        ix = generated_text.find('Rookie:')
        if ix != -1:
            generated_text = generated_text[:ix]
        if generated_text[-3:] == '"]}' or '"' in generated_text[-3:]:
            generated_text = generated_text[:-3]
            # change scene
            location = "the Ecliptic Vaults"
            doReset = True

        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt, "location": location, "full_answer": fullAnswer})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    print(f"Before session put: {time.time() - startTime}")
    session.reset(doReset)
    session.put(query, answers, location, summary)
    print(f"After session put: {time.time() - startTime}")
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }


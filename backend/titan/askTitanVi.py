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
        bedrock, vectorstores = connectToBedrock([{"index": "/opt/index_faiss", "model": "amazon.titan-e1t-medium"}])
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
        {"texts": "Vi is a League of Legends champion and their title is the Piltover Enforcer. The champion's quote is “We can either do this the hard way or… Oh wait, no. There's just the hard way.”. The champion's roles are: fighter and assassin. Vi is associated with Piltover. Once a criminal from the mean streets of Zaun, Vi is a hotheaded, impulsive, and fearsome woman with only a very loose respect for authority figures. Growing up all but alone, Vi developed finely honed survival instincts as well as a wickedly abrasive sense of humor. Now working with the Wardens to keep the peace in Piltover, she wields mighty hextech gauntlets that can punch through walls—and suspects—with equal ease. This text is about Vi.  She snatched up the gauntlets, the wrist mechanisms clamping down painfully on her arms, but she endured the agony long enough to smash open a path to free the miners.The following day, Vi paid a visit to the Factorywood Fiends. Still wearing the powered gauntlets, she took on the entire gang, administering a beating so legendary that it is still spoken of in the Lanes to this day.Vi eventually disappeared from Zaun during a time of great upheaval, when tensions with Piltover were running high. Rumors circulated between the gangs that she had been killed in a huge explosion in the heart of the undercity, or that she had turned her back on her friends and struck out for distant lands. The truth, however, finally came to light when Old Hungry’s Scars—a vicious gang whose murder sprees had spread topside—were brought down by a respected sheriff of Piltover and her new ally… Vi.The former gang leader was now in the employ of the Wardens, and she had replaced the chem-powered pulverizer gauntlets with a pair of brand new hextech Atlas prototypes. This text is about Vi. Vi remembers little of her childhood in Zaun, and what she does remember, she wishes she didn’t. Running with the sump-snipe gangs, she quickly learned to use her wits, as well as her fists, to survive. Everyone who encountered Vi knew she could talk—or punch—her way out of trouble. More often than not, she chose the latter.None of the old-timers from her youth could tell her anything of her parents. Most assumed they had died in one of the industrial accidents that were, sadly, all too common in the undercity. Though she had ended up in the crumbling Hope House orphanage, a notoriously mad sump-scrapper claimed to have found her adrift in a bassinet large enough for two in the ruins of a collapsed chem-lab. In the end, Vi figured some things were best left unknown.With her wild pink hair, she became a distinctive sight on the streets of Zaun—hightailing from angry shopkeepers in the boundary markets, swaggering through the colorful bazaars of the Black Lanes, or hitching rides up into Piltover aboard the hexdraulic conveyors. Wherever there was a scrape to be gotten into or a scam to be run, Vi was in the thick of it, though she never stole from those that couldn’t cover the loss… and never hurt those that didn’t deserve it. "}
        Here is some context about the place where the scene takes place:
        """ + context + """
        
        Complete the following short story as Vi:
        """

        promptContext = """{"context": """

        CONTEXT_SCENE_1 = "Rookie is a new enforcer trainee in piltovian police force. Rookie meets Vi at the plaza in Piltover. Vi was ordered to go to the Ecliptic Vaults and investigate the scene since someone broke into the vault a few hours ago. She is going there alone."
        CONTEXT_SCENE_1_FULL = "Rookie is a new enforcer trainee in piltovian police force. Rookie meets Vi at the plaza in Piltover. Vi was ordered to go to the Ecliptic Vaults and investigate the scene since someone broke into the vault a few hours ago. Noone was hurt at the scene but the perpetrators could still be in the area. Nobody knows if anything has been stolen, that's for the Vi to find out. Vi doesn't want to take Rookie to the Vaults with her. Only if Rookie proves they are strong enough Vi might change her mind. Vi doesn't know who is behind the break in and will doubt every theory regarding who might have done it."
        CONTEXT_SCENE_2_FULL = "Right now Rookie and Vi are at the Ecliptic Vaults. There is noone around but the main vault is in a bad shape and looks as if it was damaged in an attempted break-in. Vi and Rookie cannot go inside no matter what since the building is very unstable. The thieves didn't manage to break through and didn't steal anything. There is a lot of junk lying around and among them there is a scrap of metal with a blue graffiti on it. Vi recognizes the graffiti to be Loxy's - one of the 'Rawring Sparks' gang member. Loxy is the mastermind behind the Rawring Sparks operations. The Rawring Sparks have been causing mischeif in Piltover more and more often recently. Vi doesn't want to share all the information at once. When Rookie finds out about Loxy, Vi should suggest going to the Lanes together with Rookie as it is the very heart of Zaun."
        CONTEXT_SCENE_2 = "Right now Rookie and Vi are at the Ecliptic Vaults. Rookie and Vi can't go inside the vaults as they were damaged in an attempted break-in and might collapse any minute."
        CONTEXT_SCENE_3 = "Rookie and Vi arrive to the Lanes in Zaun. Vi suggest going to the local bar 'The Last Crop' to ask locals for some information regarding 'Rawring Sparks'."

        # depending on the location
        promptContext += summary + " "
        if location == LOCATION_1:
            promptContext += CONTEXT_SCENE_1
        elif location == LOCATION_2:
            promptContext += CONTEXT_SCENE_2 
        else:
            promptContext += CONTEXT_SCENE_3

        promptStory = ", \"story\": \""

        # use previous messages
        previousUserMessages = msgHistory["questions"] + [query]
        previousViResponses = msgHistory["answers"] + [""]
        dialogue = ""
        for q, a in zip(previousUserMessages, previousViResponses):
            dialogue += "Rookie: " + q + " Vi: " + a + " "
        promptStory += dialogue

        controlReturn = "K"
        #check the region
        if location == LOCATION_1:
            controlPrompt = f"""This is the story of Rookie and Vi with some context in JSON format: {promptContext + promptStory+'"}'}. Are Vi and Rookie at the Ecliptic Vaults already? Answer 'Yes.' or 'No.'"""
            region_response = call_bedrock(bedrock, controlPrompt)
            controlReturn = "1_" + controlPrompt + "_" + region_response
            if "yes" in region_response.lower():
                location = LOCATION_2
                summary = call_bedrock(bedrock, f"""This is the story of Rookie and Vi with some context in JSON format: {'{' + promptStory[2:]+'"}'}. Summarize the story.""")
                promptContext = """{"context": """
                promptContext += summary + " "
                promptContext += CONTEXT_SCENE_2
                doReset = True

        elif location == LOCATION_2:
            controlPrompt = f"""This is the story of Rookie and Vi with some context in JSON format: {promptContext + promptStory+'"}'}. Are Vi and Rookie at the Lanes already? Answer 'Yes.' or 'No.'"""
            region_response = call_bedrock(bedrock, controlPrompt)
            controlReturn = "2_" + controlPrompt + "_" + region_response
            if "yes" in region_response.lower():
                location = LOCATION_3
                summary = call_bedrock(bedrock, f"""This is the story of Rookie and Vi with some context in JSON format: {'{' + promptStory[2:]+'"}'}. Summarize the story.""")
                promptContext = """{"context": """
                promptContext += summary + " "
                promptContext += CONTEXT_SCENE_3
                doReset = True
                
        else:
            controlPrompt = f"""This is the story of Rookie and Vi with some context in JSON format: {promptContext + promptStory+'"}'}. Are Vi and Rookie in Shurima already? Answer 'Yes.' or 'No.'"""
            region_response = call_bedrock(bedrock, controlPrompt)
            controlReturn = "3_" + controlPrompt + "_" + region_response
            if "yes" in region_response.lower():
                location = LOCATION_1
                summary = call_bedrock(bedrock, f"""This is the story of Rookie and Vi with some context in JSON format: {'{' + promptStory[2:]+'"}'}. Summarize the story.""")
                promptContext = """{"context": """
                promptContext += summary + " "
                promptContext += CONTEXT_SCENE_1
                doReset = True

        # check subquests
        subquests1 = {0: 'Has Rookie asked about the vaults?', 1: 'Has Rookie asked why is Vi going to the vaults?', 2: 'Has Rookie asked about the perpetrators?', 3: 'Has Rookie asked about the break-in?', 4: 'Has Rookie asked about the investigation?', 5: 'Has Rookie asked Vi to come with her?'}
        subanswers1 = {0: 'Noone is sure about what happened at the scene.', 1: '', 2: 'Noone knows who the perpetrators may be and Vi will doubt every claim about who might have done it.', 3: 'Noone was injured in a break-in but the perpetrators might still be around.', 4: 'Vi is the first and only enforcer dispatched in this investigation.', 5: 'Vi won\'t take Rookie with her unless Rookie proves they are strong enough by punching a tree hard enough or running circles around the plaza.'}
        subquests2 = {0: 'Has Rookie asked about the vaults?', 1: 'Has Rookie asked about the break-in?', 2: 'Has Rookie asked if anything has been stolen?', 3: 'Has anyone suggested looking for clues?', 4: 'Has Rookie asked about the blue graffiti?', 5: 'Has Vi told Rookie about Loxy?', 6: 'Has Rookie asked about the perpetrators?', 7: 'Has Rookie asked who might have broken in?', 8: 'Has Vi told Rookie about Zaun gangsters?'}
        subanswers2 = {0: '', 1: 'The thieves tried to break in but only managed to damage the building, they didn\'t steal anything.', 2: 'Nothing has been stolen from the Vaults.', 3: 'Vi and Rookie should look around for clues. There is a lot of junk lying around. Among them there is a piece of metal with blue graffiti on it.', 4: 'Although it is similiar to Jinx\'s style, Vi recognizes the graffiti to be Loxy\'s', 5: 'Loxy is a part of the Zaun gang known as Rawring Sparks and is the mastermind behind their operations.', 6: 'Vi suspects that the thieves might actually be the Zaun gangsters.', 7: 'Vi suspects that the thieves might actually be the Zaun gangsters.', 8: 'Rawring Sparks\' leader is Loxy. The Sparks have been causing a lot of mischief in Piltover lately.', 'Bonus1': 'Vi might suggest going to the Lanes to look for more information.'}
        subquests3 = {0: 'Has Rookie asked about what to do there?', 1: '', 2: '', 3: '', 4: '', 5: ''}
        subanswers3 = {0: '', 1: '', 2: '', 3: '', 4: '', 5: ''}

        promptQuests = """The following is a story involving Rookie and Vi with some context in a JSON format: {"context": \""""
        if location == LOCATION_1:
            promptQuests += CONTEXT_SCENE_1
            promptQuests += """, "story": \"""" + dialogue[:-5] + """\"}. There is a list of questions provided. Answer each question with a 'yes' or 'no', as an output provide a list. The list of questions:\nQuestions:\n"""
            for k, v in subquests1.items():
                promptQuests += str(k+1) + ". " + v + '\n'
            promptQuests += "Answers:\n"
        elif location == LOCATION_2:
            promptQuests += CONTEXT_SCENE_2
            promptQuests += """, "story": \"""" + dialogue[:-5] + """\"}. There is a list of questions provided. Answer each question with a 'yes' or 'no', as an output provide a list. The list of questions:\nQuestions:\n"""
            for k, v in subquests2.items():
                promptQuests += str(k+1) + ". " + v + '\n'
            promptQuests += "Answers:\n"
        else:
            promptQuests += CONTEXT_SCENE_3
            promptQuests += """, "story": \"""" + dialogue[:-5] + """\"}. There is a list of questions provided. Answer each question with a 'yes' or 'no', as an output provide a list. The list of questions:\nQuestions:\n"""
            for k, v in subquests3.items():
                promptQuests += str(k+1) + ". " + v + '\n'
            promptQuests += "Answers:\n"
        print("Quests prompt:", promptQuests)
        generated_quest_ans = call_bedrock(bedrock, promptQuests)
        print("Quest answers: " + generated_quest_ans)
        questAns = generated_quest_ans.split('\n')
        promptQuestBonus = ""
        completedQuests = set()
        for i in range(len(questAns)):
            if 'yes' in questAns[i].lower():
                completedQuests.add(i)
                if location == LOCATION_1:
                    promptQuestBonus += subanswers1[i] + " "
                elif location == LOCATION_2:
                    promptQuestBonus += subanswers2[i] + " "
                    if set([4, 5, 6, 7]) & completedQuests:
                        promptQuestBonus += subanswers2['Bonus1'] + " "
                else:
                    promptQuestBonus += subanswers3[i] + " "
        
        prompt += promptContext + promptQuestBonus + promptStory
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
        if ('"' in generated_text[-3:] or '}' in generated_text[-3:] or fullAnswer == generated_text) and "Sorry - this model" not in generated_text:
            generated_text = generated_text[:-3]
            # change scene
            if location == LOCATION_1:
                location = LOCATION_2
            elif location == LOCATION_2:
                location = LOCATION_3
            else:
                location = LOCATION_1
            summary = call_bedrock(bedrock, f"""This is the story of Rookie and Vi with some context in JSON format: {'{[' + promptStory[2:]+'"]}'}. Summarize the story.""")
            doReset = True

        answers.append({"answer": str(generated_text), "docs": doc_sources_string, "context": context, "prompt": prompt, "location": location, "control": controlReturn, "full_answer": fullAnswer, "summary": summary, 'quests': generated_quest_ans})

    resp_json = {"answers": answers}
    if log_questions:
        print({"question": query, "answers": answers})

    print(f"Before session put: {time.time() - startTime}")
    session.reset(doReset)
    if "Sorry - this model" not in generated_text:
        session.put(query, answers, location, summary)
    print(f"After session put: {time.time() - startTime}")
    return {
        'statusCode': 200,
        'body': json.dumps(resp_json)
    }


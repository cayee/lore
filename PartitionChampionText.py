import json

FILENAME = "championsInfo_v1_nice.json"

with open(FILENAME, 'r') as f:
    championInfo = json.load(f)

SENTENCES = 5
textParts = []
metadatas = []

def divideText(text, name=""):
    if name == "":
        START_TEXT = ""
    else:
        START_TEXT = f"This text is about {name}. "
    if text == "":
        return []
    parts = []
    part = START_TEXT
    i = 0
    while True:
        ix = text.find('.')
        if ix == -1:
            break
        part += text[:ix+1]
        text = text[ix+1:]
        i += 1
        if i == SENTENCES:
            parts.append(part)
            part = START_TEXT
            i = 0
    if part != START_TEXT:
        parts.append(part)
    return parts

def createParagraph(data):
    text = f"{data['name']} is a League of Legends champion and their title is {data['title']}."
    
    if data["races"] != []:
        if len(data["races"]) == 1:
            text += f" The champion's race is {data['races'][0]}."
        else:
            text += f" The champion's races are: {', '.join(data['races'][:-1])} and {data['races'][-1]}."
            
    if data['quote-author'] == '' or data['quote-author'] == data['name']:
        text += f" The champion's quote is {data['quote']}."
    else:
        text += f" {data['quote-author']} said about this champion that, quote: {data['quote']}."
        
    if data["roles"] != []:
        if len(data["roles"]) == 1:
            text += f" The champion's role is {data['roles'][0]}."
        else:
            text += f" The champion's roles are: {', '.join(data['roles'][:-1])} and {data['roles'][-1]}."
    
    if data['associated-faction-slug'] == 'unaffiliated' or data['associated-faction-slug'] == '':
        text += f" {data['name']} is not associated with any faction or region."
    else:
        ix = data['associated-faction-slug'].find('-')
        if ix == -1:
            faction = data['associated-faction-slug'][0].upper() + data['associated-faction-slug'][1:]
        else:
            faction = data['associated-faction-slug'][0].upper() + data['associated-faction-slug'][1:ix] + " " + data['associated-faction-slug'][ix+1].upper() + data['associated-faction-slug'][ix+2:]
        text += f" {data['name']} is associated with {faction}."

    return [text]

for champion in championInfo.keys():
    if champion == "extras":
        continue
    championText = championInfo[champion]
    
	#bio short
    textParts += [championText["bio-short"]]
    metadatas += [championText["main-url"]]
    # bio full
    newPart = divideText(championText["bio-full"], championText["name"])
    textParts += newPart
    for part in newPart:
        metadatas += [championText["bio-url"]]
    # color story
    newPart = divideText(championText["color-story"], championText["name"])
    textParts += newPart
    for part in newPart:
        metadatas += [championText["color-story-url"]]
    # name, title, races, quote (+author), roles, associated faction [slug]
    newPart = createParagraph(championText)
    textParts += newPart
    metadatas += [championText["main-url"]]

for text in championInfo["extras"]:
    newPart = divideText(text["content"])
    textParts += newPart
    for part in newPart:
        metadatas += [text["url"]]

print(len(textParts), len(metadatas))
finality = {"list": textParts, "meta": metadatas}

with open(f"textParts-{SENTENCES}.json", 'w') as f:
    data = json.dumps(finality)
    f.write(data)

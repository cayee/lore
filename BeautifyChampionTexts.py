import html
import json

def cleanText(text):
    text = html.unescape(text)
    # remove HTML sections
    while True:
        ix = text.find('<')
        if ix == -1:
            break
        ix2 = text.find('>')
        text = text[:ix] + text[ix2+1:]
    return text

FILENAME = "championsInfo_v1"
EXTENSION = ".json"
with open(FILENAME+EXTENSION, 'r') as f:
    championInfo = json.load(f)

for champion in championInfo.keys():
    if champion == "extras":
        continue
    for mod in championInfo[champion].keys():
        data = championInfo[champion][mod]
        if isinstance(data, list):
            newText = []
            for text in data:
                text = cleanText(text)
                newText.append(text)
            championInfo[champion][mod] = newText
            continue
        data = cleanText(data)
        championInfo[champion][mod] = data
extras = []
for text in championInfo["extras"]:
    extras.append({'content': cleanText(text['content']), 'url': text['url']})
championInfo["extras"] = extras 

with open(FILENAME + "_nice" + EXTENSION, 'w') as f:
    data = json.dumps(championInfo)
    f.write(data)
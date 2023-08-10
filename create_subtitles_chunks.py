import pandas as pd
import json

data = pd.read_csv("ArcaneSubtitles.csv", delimiter=",")

data = data.fillna("")

currentSpeaker = ""
currentListener = ""
textChunks = []
for i, row in data.iterrows():
    if currentSpeaker == row["Who said it:"] and currentListener == row["Who was it said to:"]:
        textChunks[-1] = textChunks[-1] + " " + row["Text:"]
        continue
    currentSpeaker = row["Who said it:"]
    currentListener = row["Who was it said to:"]
    if currentSpeaker == "":
        continue
    if currentListener == "":
        textChunks.append(f"{currentSpeaker} said: {row['Text:']}")
    else:
        textChunks.append(f"{currentSpeaker} said to {currentListener}: {row['Text:']}")
        
finality = {"texts": textChunks}
with open("subtitles_chunks.json", "w") as f:
    jsonData = json.dumps(finality)
    f.write(jsonData)
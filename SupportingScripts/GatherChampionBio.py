import requests
import json
import time


UPDATE_CHAMPION_LIST = True


if UPDATE_CHAMPION_LIST:
    # get all champions json
    response = requests.get('https://universe-meeps.leagueoflegends.com/v1/en_pl/search/index.json')

    # Parse the response and save it
    data = response.json()
    data = json.dumps(data)
    with open("championsList.json", "w") as f:
        f.write(data)

# open json
with open('championsList.json', 'r') as f:
    championJson = json.load(f)
    
championList = []
for championInfo in championJson["champions"]:
    championURL = championInfo["url"].split('/')[-1]
    championList.append(championURL)

UPDATE_CHAMPIONS_JSONS = True
UPDATE_CHAMPIONS_COLORS = True
UPDATE_EXTRAS = True

urlPrefix = "https://universe-meeps.leagueoflegends.com/v1/en_us/champions/"
urlColorPrefix = "https://universe-meeps.leagueoflegends.com/v1/en_us/story/"

finalSet = {"extras": []}
for championName in championList:
    if UPDATE_CHAMPIONS_JSONS or UPDATE_CHAMPIONS_COLORS:
        time.sleep(1)
    print(f"Starting {championName}", end="...  ")
    championInfo = {'name': "", 'title': "", 'slug': "", 'main-url': "", 'associated-faction-slug': "", 'roles': [], 'bio-short': "", 'bio-full': "", 'bio-url': "",'quote': "", 'quote-author': "", 'related-champions': [], 'modules': [], 'races': [], 'color-story': "", "color-story-url": ""}
    
    # general json
    trueURL = urlPrefix + championName + "/index.json"
    if UPDATE_CHAMPIONS_JSONS:
        response = requests.get(trueURL)
        if response.status_code == 200:
            data = response.json()
            data = json.dumps(data)
            with open(f"UniverseChampionsJsons/{championName}.json", "w") as f:
                f.write(data)
        else:
            print(f"Error while downloading general json for {championName}, error code: {response.status_code}")
            continue

    with open(f"UniverseChampionsJsons/{championName}.json", "r") as f:
        data = json.load(f)
    championInfo["name"] = data["name"]
    championInfo["title"] = data["title"]
    championInfo["slug"] = data["champion"]["slug"]
    championInfo["main-url"] = f"https://universe.leagueoflegends.com/en_US/champion/{championInfo['slug']}"
    championInfo["associated-faction-slug"] = data["champion"]["associated-faction-slug"]
    for role in data["champion"]["roles"]:
        championInfo["roles"].append(role["slug"])
    championInfo["bio-short"] = data["champion"]["biography"]["short"]
    championInfo["bio-full"] = data["champion"]["biography"]["full"]
    championInfo["bio-url"] = f"https://universe.leagueoflegends.com/en_US/story/champion/{championInfo['slug']}"
    championInfo["quote"] = data["champion"]["biography"]["quote"]
    championInfo["quote-author"] = data["champion"]["biography"]["quote-author"]
    for relChamp in data["related-champions"]:
        championInfo["related-champions"].append(relChamp["slug"])
    for module in data["modules"]:
        if "url" in module.keys():
            championInfo["modules"].append(module["slug"] + "|" + module["type"] + "|" + module["url"])
            if module["type"] == "story-preview" and "color-story" not in module["url"]:
                ix = module["url"].rfind('/')
                extraName = module['url'][ix+1:]
                if UPDATE_EXTRAS:
                    extraURL = "https://universe-meeps.leagueoflegends.com/v1/en_us/story/" + extraName + "/index.json"
                    response = requests.get(extraURL)
                    if response.status_code == 200:
                        data2 = response.json()
                        data2 = json.dumps(data2)
                        with open(f"UniverseChampionsJsons/{extraName}.json", "w") as f:
                            f.write(data2)
                    else:
                        print(f"Error while downloading general json for {championName}, error code: {response.status_code}")
                with open(f"UniverseChampionsJsons/{extraName}.json", "r") as ff:
                    dataExtra = json.load(ff)
                strExtra = ""
                for p in dataExtra["story"]["story-sections"][0]["story-subsections"]:
                    if p["content"] != None:
                        strExtra += p["content"]
                finalSet["extras"].append({'content': strExtra, 'url': f"https://universe.leagueoflegends.com{module['url']}"})
        else:
            championInfo["modules"].append(module["slug"] + "|" + module["type"] + "|")
    if "races" in data["champion"].keys():
        for race in data["champion"]["races"]:
            championInfo["races"].append(race["slug"])

    # color story
    trueColorURL = urlColorPrefix + championName + "-color-story/index.json"
    if UPDATE_CHAMPIONS_COLORS:
        response = requests.get(trueColorURL)
        if response.status_code == 200:
            data = response.json()
            data = json.dumps(data)
            with open(f"UniverseChampionsJsons/{championName}_color.json", "w") as f:
                f.write(data)
        else:
            print(f"Error while downloading color-story json for {championName}, error code: {response.status_code}")

    try:
        with open(f"UniverseChampionsJsons/{championName}_color.json", "r") as f:
            data = json.load(f)
    
        for section in data["story"]["story-sections"][0]["story-subsections"]:
            championInfo["color-story"] += section["content"]
        championInfo["color-story-url"] = f"https://universe.leagueoflegends.com/en_US/story/{championInfo['slug']}-color-story/"
    except FileNotFoundError:
        print(" [no color story found] ", end=" ")

    finalSet[f"{championName}"] = championInfo
    print(f"Finished {championName}")

dataToSave = json.dumps(finalSet)
with open("championsInfo_v1.json", "w") as f:
    f.write(dataToSave)